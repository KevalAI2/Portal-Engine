import os
import subprocess
import time

def run_command(cmd, shell=True):
    """Helper to run shell commands."""
    try:
        result = subprocess.run(cmd, shell=shell, check=False, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"⚠️ Command '{cmd}' failed with exit code {result.returncode}")
            print(result.stdout)
            print(result.stderr)
        return result
    except subprocess.SubprocessError as e:
        print(f"❌ Error executing command '{cmd}': {e}")
        return None

def stop_service(name, pattern=None, port=None):
    """Helper to stop a service by pattern or port."""
    if pattern:
        print(f"Stopping {name}...")
        run_command(f"pkill -f \"{pattern}\"")
    if port:
        print(f"Stopping {name} (port {port})...")
        result = run_command(f"lsof -ti:{port}")
        if result and result.stdout.strip():
            run_command(f"lsof -ti:{port} | xargs kill -9")
        else:
            print(f"❌ No process found on port {port}")

def stop_redis(port):
    """Stop Redis service on specified port."""
    print(f"Stopping Redis on port {port}...")
    result = run_command(f"lsof -ti:{port}")
    if result and result.stdout.strip():
        pid = result.stdout.strip().split('\n')[0]
        run_command(f"kill -9 {pid}")
        print(f"✅ Redis (PID: {pid}) stopped")
    else:
        print("❌ Redis not running")

def main():
    # Define ports from environment variables or defaults
    NOTIFICATION_PORT = os.getenv("NOTIFICATION_PORT", "9000")
    FASTAPI_PORT = os.getenv("FASTAPI_PORT", "3031")
    RABBITMQ_PORT = os.getenv("RABBITMQ_PORT", "5672")
    REDIS_PORT = os.getenv("REDIS_PORT", "6379")

    # Stop Celery Beat
    stop_service("Celery Beat", pattern="celery -A workers.celery_app beat")

    # Stop Celery Worker
    stop_service("Celery Worker", pattern="python.*celery")

    # Stop Notification Service
    stop_service("Notification Service", port=NOTIFICATION_PORT)

    # Stop FastAPI Service
    stop_service("FastAPI Service", port=FASTAPI_PORT)

    # Stop RabbitMQ
    stop_service("RabbitMQ", port=RABBITMQ_PORT)

    # Stop Redis
    stop_redis(REDIS_PORT)

    print("✅ All services stopped!")

if __name__ == "__main__":
    main()