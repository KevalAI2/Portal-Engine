import os
import subprocess
import time
import sys

def run_command(cmd, cwd=None, background=False, env=None):
    """Helper to run shell commands."""
    if background:
        # Use start_new_session=True to detach the process properly
        return subprocess.Popen(cmd, cwd=cwd, shell=True, env=env, 
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              start_new_session=True)
    else:
        result = subprocess.run(cmd, cwd=cwd, shell=True, check=False, 
                              env=env, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"⚠️ Command '{cmd}' failed with exit code {result.returncode}")
            print(result.stdout)
            print(result.stderr)
        return result

def ensure_package_dirs(root_dir):
    """Ensure app and workers dirs are Python packages (add __init__.py if missing)."""
    app_dir = os.path.join(root_dir, "app")
    workers_dir = os.path.join(app_dir, "workers")
    for d in [app_dir, workers_dir]:
        if not os.path.exists(d):
            os.makedirs(d)
            print(f"📁 Created directory {d}")
        init_file = os.path.join(d, "__init__.py")
        if not os.path.exists(init_file):
            with open(init_file, "w") as f:
                f.write("# Auto-created to make this a Python package\n")
            print(f"📦 Created {init_file}")

def check_celery_app_exists(root_dir):
    """Check if the Celery app can be imported properly."""
    app_dir = os.path.join(root_dir, "app")
    workers_dir = os.path.join(app_dir, "workers")
    
    # Check if celery_app.py exists
    celery_app_path = os.path.join(workers_dir, "celery_app.py")
    if not os.path.exists(celery_app_path):
        print(f"❌ Celery app not found at {celery_app_path}")
        return False
    
    # Try to import it to check for syntax errors
    try:
        import sys
        sys.path.insert(0, root_dir)
        sys.path.insert(0, app_dir)
        from app.workers.celery_app import celery_app
        print("✅ Celery app imports successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to import Celery app: {e}")
        return False

def main():
    # Get project root
    root_dir = os.getcwd()
    print(f"🚀 Starting all services in {root_dir}...")

    # Ensure __init__.py files exist
    ensure_package_dirs(root_dir)

    # Check if Celery app exists and can be imported
    if not check_celery_app_exists(root_dir):
        print("❌ Cannot start Celery without a valid app")
        sys.exit(1)

    # Setup environment
    env = os.environ.copy()
    app_dir = os.path.join(root_dir, "app")
    env["PYTHONPATH"] = f"{root_dir}:{app_dir}"  # Include both root and app dir
    env["CELERY_BROKER_URL"] = "amqp://guest:guest@localhost:5672//"
    env["CELERY_RESULT_BACKEND"] = "redis://localhost:6379/0"

    # --- Start Redis ---
    print("📡 Starting Redis on port 6379...")
    run_command("redis-server --port 6379 --daemonize yes --protected-mode no", env=env)
    time.sleep(2)

    # --- Start RabbitMQ ---
    print("📡 Starting RabbitMQ on port 5672...")
    RABBITMQ_SBIN = "/opt/homebrew/opt/rabbitmq/sbin"  # Adjust if your RabbitMQ path differs
    #RABBITMQ_SBIN = "/usr/local/opt/rabbitmq/sbin"
    rabbitmq_server = os.path.join(RABBITMQ_SBIN, "rabbitmq-server")
    rabbitmq_ctl = os.path.join(RABBITMQ_SBIN, "rabbitmqctl")

    if not os.path.exists(rabbitmq_server):
        print(f"❌ RabbitMQ not found at {rabbitmq_server}")
        print("➡️ Run `brew reinstall rabbitmq` or check Homebrew path.")
        sys.exit(1)

    # Stop any existing RabbitMQ instance gracefully
    run_command(f"{rabbitmq_ctl} stop 2>/dev/null || true", env=env)
    run_command(f"RABBITMQ_NODE_PORT=5672 {rabbitmq_server} -detached", env=env)
    time.sleep(5)  # Give RabbitMQ time to start

    # --- Start Celery Worker ---
    print("⚙️ Starting Celery Worker...")
    # Use the correct import path - app.workers.celery_app
    worker_cmd = (
        f"cd {root_dir} && "
        "celery -A app.workers.celery_app worker "  # Changed from workers.celery_app to app.workers.celery_app
        "--loglevel=info "
        "--concurrency=4 "
        "--queues=user_processing_alt "
        "--hostname=worker_alt@%h "
        "--prefetch-multiplier=1 "
        "--without-gossip "
        "--without-mingle "
        "--without-heartbeat "
        "--pool=prefork "
        "--max-tasks-per-child=1000 "
        "--time-limit=300 "
        "--soft-time-limit=240 "
        "--autoscale=1,10 "
        "--max-memory-per-child=200000"
    )
    celery_worker = run_command(worker_cmd, cwd=root_dir, background=True, env=env)
    print(f"📝 Celery Worker PID: {celery_worker.pid}")
    
    # Capture and log stderr for debugging
    time.sleep(2)
    if celery_worker.poll() is not None:
        stdout, stderr = celery_worker.communicate()
        print(f"❌ Celery Worker failed to start. Error: {stderr}")
    else:
        print("✅ Celery Worker started successfully")

    # --- Start Celery Beat ---
    print("⏰ Starting Celery Beat...")
    beat_cmd = (
        f"cd {root_dir} && "
        "celery -A app.workers.celery_app beat "  # Changed from workers.celery_app to app.workers.celery_app
        "--loglevel=info "
        "--scheduler=celery.beat:PersistentScheduler"
    )
    celery_beat = run_command(beat_cmd, cwd=root_dir, background=True, env=env)
    print(f"📝 Celery Beat PID: {celery_beat.pid}")
    
    # Capture and log stderr for debugging
    time.sleep(2)
    if celery_beat.poll() is not None:
        stdout, stderr = celery_beat.communicate()
        print(f"❌ Celery Beat failed to start. Error: {stderr}")
    else:
        print("✅ Celery Beat started successfully")

    # --- Start Notification Service ---
    print("📨 Starting Notification Service...")
    notification_cmd = f"cd {root_dir} && python notification_service.py"
    notification_proc = run_command(notification_cmd, background=True, env=env)
    print(f"📝 Notification Service PID: {notification_proc.pid}")
    time.sleep(2)

    # --- Start FastAPI Service ---
    print("🌐 Starting FastAPI Service...")
    fastapi_cmd = f"cd {root_dir} && python app/main.py"
    fastapi_proc = run_command(fastapi_cmd, background=True, env=env)
    print(f"📝 FastAPI Service PID: {fastapi_proc.pid}")

    print("✅ All services started successfully!")
    print("👉 Check if services are running with:")
    print("   ps aux | grep celery")
    print("   ps aux | grep python")
    print("👉 Use './stop_all.sh' to stop them.")

    # Wait a bit and check if Celery processes are still running
    time.sleep(5)
    print("\n🔍 Checking if Celery processes are running...")
    run_command("ps aux | grep celery", cwd=root_dir)

if __name__ == "__main__":
    main()