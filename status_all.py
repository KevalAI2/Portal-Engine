import socket
import subprocess
import psutil
import os
import signal

# Your specific ports
NOTIFICATION_PORT = 9000
FASTAPI_PORT = 3031
RABBITMQ_PORT = 5672
REDIS_PORT = 6379

RABBITMQ_CTL_PATH = "/usr/local/Cellar/rabbitmq/4.1.3/sbin/rabbitmqctl"  # Adjust if needed

def is_port_in_use(port):
    """Check if a port is in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def get_pid_for_port(port):
    """Get the PID listening on the given port using lsof."""
    try:
        output = subprocess.check_output(['lsof', '-ti', f':{port}']).decode().strip()
        if output:
            return output.split('\n')[0]
        return None
    except subprocess.CalledProcessError:
        return None

def check_process(pattern):
    """Check if a process matching the pattern is running and get its PID."""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
            if pattern in cmdline:
                return proc.info['pid']
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return None

def run_with_timeout(cmd, timeout_sec):
    """Run a command with timeout."""
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            proc.wait(timeout=timeout_sec)
            return proc.returncode == 0
        except subprocess.TimeoutExpired:
            os.kill(proc.pid, signal.SIGTERM)
            proc.wait()
            return False
    except Exception:
        return False

print("=== Service Status Check ===")
print("")

# Check Redis
print(f"Redis (port {REDIS_PORT}):")
if is_port_in_use(REDIS_PORT):
    pid = get_pid_for_port(REDIS_PORT)
    print(f"✅ RUNNING - PID: {pid}")
else:
    print("❌ STOPPED")
print("")

# Check RabbitMQ
print(f"RabbitMQ (port {RABBITMQ_PORT}):")
if is_port_in_use(RABBITMQ_PORT):
    pid = get_pid_for_port(RABBITMQ_PORT)
    print(f"✅ RUNNING - PID: {pid}")
    # Check if RabbitMQ is actually responding with timeout
    responding = run_with_timeout([RABBITMQ_CTL_PATH, 'status'], 2)
    if responding:
        print("   ✅ RabbitMQ responding properly")
    else:
        print("   ⚠️  RabbitMQ port open but slow to respond")
else:
    print("❌ STOPPED")
print("")

# Check Celery Worker
print("Celery Worker:")
celery_worker_pid = check_process("celery.*worker.*user_processing_alt")
if celery_worker_pid:
    print(f"✅ RUNNING - PID: {celery_worker_pid}")
else:
    print("❌ STOPPED")
print("")

# Check Celery Beat
print("Celery Beat:")
celery_beat_pid = check_process("celery.*beat")
if celery_beat_pid:
    print(f"✅ RUNNING - PID: {celery_beat_pid}")
else:
    print("❌ STOPPED")
print("")

# Check Notification Service
print(f"Notification Service (port {NOTIFICATION_PORT}):")
if is_port_in_use(NOTIFICATION_PORT):
    pid = get_pid_for_port(NOTIFICATION_PORT)
    print(f"✅ RUNNING - PID: {pid}")
else:
    print("❌ STOPPED")
print("")

# Check FastAPI Service
print(f"FastAPI Service (port {FASTAPI_PORT}):")
if is_port_in_use(FASTAPI_PORT):
    pid = get_pid_for_port(FASTAPI_PORT)
    print(f"✅ RUNNING - PID: {pid}")
else:
    print("❌ STOPPED")
print("")

print("=== Status Check Complete ===")