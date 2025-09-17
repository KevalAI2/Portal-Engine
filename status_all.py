#!/usr/bin/env python3
import socket
import subprocess
import os
import sys

def get_project_root():
    """Get the project root directory."""
    return os.getcwd()

def run_command(cmd, timeout=10):
    """Run a command and return the result."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)

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

def get_all_pids(pattern):
    """Get all PIDs matching the pattern."""
    try:
        cmd = f"ps aux | grep '{pattern}' | grep -v grep | awk '{{print $2}}'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip().split('\n')
        return []
    except Exception:
        return []

def check_celery_workers():
    """Check Celery workers status using direct inspection."""
    root_dir = get_project_root()
    app_dir = os.path.join(root_dir, "app")
    
    try:
        # Set PYTHONPATH for the subprocess
        env = os.environ.copy()
        env['PYTHONPATH'] = f"{root_dir}:{app_dir}"
        
        result = subprocess.run([
            sys.executable, '-c', 
            'try:'
            '    from app.workers.celery_app import celery_app;'
            '    insp = celery_app.control.inspect(timeout=3);'
            '    if insp:'
            '        active = insp.active() or {};'
            '        registered = insp.registered() or {};'
            '        scheduled = insp.scheduled() or {};'
            '        print(f"ACTIVE:{len(active)}");'
            '        print(f"REGISTERED:{len(registered)}");'
            '        print(f"SCHEDULED:{len(scheduled)}");'
            '        for hostname in active.keys():'
            '            print(f"HOSTNAME:{hostname}");'
            '    else:'
            '        print("NO_INSPECTOR");'
            'except Exception as e:'
            '    print(f"ERROR:{e}");'
        ], capture_output=True, text=True, timeout=10, env=env)
        
        if result.returncode == 0:
            return result.stdout.strip()
        return "ERROR:Subprocess failed"
    except Exception as e:
        return f"ERROR:{e}"

def main():
    # Define ports
    NOTIFICATION_PORT = 9000
    FASTAPI_PORT = 3031
    RABBITMQ_PORT = 5672
    REDIS_PORT = 6379
    
    RABBITMQ_CTL_PATH = "/usr/local/opt/rabbitmq/sbin/rabbitmqctl"
    
    print("=== Service Status Check ===")
    print("")

    # Check Redis
    print(f"Redis (port {REDIS_PORT}):")
    if is_port_in_use(REDIS_PORT):
        pid = get_pid_for_port(REDIS_PORT)
        print(f"✅ RUNNING - PID: {pid}")
        
        # Test Redis connection
        success, stdout, stderr = run_command("redis-cli ping", timeout=3)
        if success and "PONG" in stdout:
            print("   ✅ Redis responding properly")
        else:
            print("   ⚠️  Redis port open but not responding")
    else:
        print("❌ STOPPED")
    print("")

    # Check RabbitMQ
    print(f"RabbitMQ (port {RABBITMQ_PORT}):")
    if is_port_in_use(RABBITMQ_PORT):
        pid = get_pid_for_port(RABBITMQ_PORT)
        print(f"✅ RUNNING - PID: {pid}")
        
        # Check if RabbitMQ is responding
        if os.path.exists(RABBITMQ_CTL_PATH):
            success, stdout, stderr = run_command(f"{RABBITMQ_CTL_PATH} status", timeout=5)
            if success:
                print("   ✅ RabbitMQ responding properly")
            else:
                print("   ⚠️  RabbitMQ port open but slow to respond")
        else:
            print("   ⚠️  RabbitMQ control tool not found")
    else:
        print("❌ STOPPED")
    print("")

    # Check Celery Worker
    print("Celery Worker:")
    celery_worker_pids = get_all_pids("celery.*worker")
    if celery_worker_pids:
        print(f"✅ RUNNING - PIDs: {', '.join(celery_worker_pids)}")
        
        # Check Celery status
        celery_status = check_celery_workers()
        if "ACTIVE:" in celery_status:
            lines = celery_status.split('\n')
            active_count = lines[0].split(":")[1]
            registered_count = lines[1].split(":")[1]
            scheduled_count = lines[2].split(":")[1]
            
            print(f"   ✅ {active_count} active workers")
            print(f"   ✅ {registered_count} registered tasks")
            print(f"   ✅ {scheduled_count} scheduled tasks")
            
            # Show hostnames if available
            hostnames = [line.split(":")[1] for line in lines[3:] if line.startswith("HOSTNAME:")]
            if hostnames:
                print(f"   ✅ Hostnames: {', '.join(hostnames)}")
                
        elif "NO_INSPECTOR" in celery_status:
            print("   ⚠️  Workers running but inspector not available")
        elif "ERROR:" in celery_status:
            print(f"   ⚠️  Status check error: {celery_status.split('ERROR:')[1]}")
        else:
            print("   ⚠️  Unknown status response")
    else:
        print("❌ STOPPED")
    print("")

    # Check Celery Beat
    print("Celery Beat:")
    celery_beat_pids = get_all_pids("celery.*beat")
    if celery_beat_pids:
        print(f"✅ RUNNING - PIDs: {', '.join(celery_beat_pids)}")
    else:
        print("❌ STOPPED")
    print("")

    # Check Notification Service
    print(f"Notification Service (port {NOTIFICATION_PORT}):")
    if is_port_in_use(NOTIFICATION_PORT):
        pid = get_pid_for_port(NOTIFICATION_PORT)
        print(f"✅ RUNNING - PID: {pid}")
    else:
        # Fallback to process check
        notification_pids = get_all_pids("notification_service.py")
        if notification_pids:
            print(f"✅ RUNNING - PIDs: {', '.join(notification_pids)} (port not detected)")
        else:
            print("❌ STOPPED")
    print("")

    # Check FastAPI Service
    print(f"FastAPI Service (port {FASTAPI_PORT}):")
    if is_port_in_use(FASTAPI_PORT):
        pid = get_pid_for_port(FASTAPI_PORT)
        print(f"✅ RUNNING - PID: {pid}")
    else:
        # Fallback to process check
        fastapi_pids = get_all_pids("main.py")
        if fastapi_pids:
            print(f"✅ RUNNING - PIDs: {', '.join(fastapi_pids)} (port not detected)")
        else:
            print("❌ STOPPED")
    print("")

    print("=== Status Check Complete ===")

if __name__ == "__main__":
    main()