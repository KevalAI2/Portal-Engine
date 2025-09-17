import os
import subprocess
import time
import sys

def run_command(cmd, cwd=None, background=False, env=None):
    """Helper to run shell commands."""
    if background:
        return subprocess.Popen(cmd, cwd=cwd, shell=True, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        result = subprocess.run(cmd, cwd=cwd, shell=True, check=False, env=env, capture_output=True, text=True)
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

def main():
    # Get project root
    root_dir = os.getcwd()
    print(f"🚀 Starting all services in {root_dir}...")

    # Ensure __init__.py files exist
    ensure_package_dirs(root_dir)

    # Setup environment
    env = os.environ.copy()
    app_dir = os.path.join(root_dir, "app")
    env["PYTHONPATH"] = app_dir  # Set PYTHONPATH to app/ to allow importing 'workers' directly
    env["CELERY_BROKER_URL"] = "amqp://guest:guest@localhost:5672//"
    env["CELERY_RESULT_BACKEND"] = "redis://localhost:6379/0"

    # --- Start Redis ---
    print("📡 Starting Redis on port 6379...")
    run_command("redis-server --port 6379 --daemonize yes --protected-mode no", env=env)

    # Wait briefly for Redis to start
    time.sleep(2)

    # --- Start RabbitMQ ---
    print("📡 Starting RabbitMQ on port 5672...")
    RABBITMQ_SBIN = "/opt/homebrew/opt/rabbitmq/sbin"  # Adjust if your RabbitMQ path differs
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
    worker_cmd = (
        "celery -A workers.celery_app worker "
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
    run_command(worker_cmd, cwd=root_dir, background=True, env=env)
    time.sleep(2)

    # --- Start Celery Beat ---
    print("⏰ Starting Celery Beat...")
    beat_cmd = (
        "celery -A workers.celery_app beat "
        "--loglevel=warning "
        "--scheduler=celery.beat:PersistentScheduler"
    )
    run_command(beat_cmd, cwd=root_dir, background=True, env=env)
    time.sleep(2)

    # --- Start Notification Service ---
    print("📨 Starting Notification Service...")
    run_command("python notification_service.py", cwd=root_dir, background=True, env=env)
    time.sleep(2)

    # --- Start FastAPI Service ---
    print("🌐 Starting FastAPI Service...")
    # Temporarily append root_dir to PYTHONPATH for FastAPI if needed
    # fastapi_env = env.copy()
    # fastapi_env["PYTHONPATH"] = f"{root_dir}:{app_dir}"
    # run_command("python app/main.py", cwd=root_dir, background=True, env=fastapi_env)

    print("✅ All services started successfully!")
    print("👉 Use './stop_all.sh' to stop them.")
    print("👉 Check status with: './status_all.sh'")

if __name__ == "__main__":
    main()