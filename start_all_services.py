#!/usr/bin/env python3
"""
Script to start all services: Celery worker, beat, RabbitMQ, and Redis
"""
import os
import sys
import subprocess
import time
import signal
import threading
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# Add app directory to Python path for relative imports
app_dir = current_dir / "app"
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

# Import using absolute paths
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("startup_script")

# Global variables to track processes
processes = {}
stop_event = threading.Event()


def check_service_running(service_name: str, check_command: list) -> bool:
    """Check if a service is already running"""
    try:
        result = subprocess.run(check_command, capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except Exception:
        return False


def start_redis():
    """Start Redis server if not running"""
    logger.info("Checking Redis server...")
    
    if check_service_running("Redis", ["redis-cli", "ping"]):
        logger.info("Redis server is already running")
        return True
    
    logger.info("Starting Redis server...")
    try:
        # Try to start Redis using systemctl
        process = subprocess.Popen(
            ["sudo", "systemctl", "start", "redis-server"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        process.wait(timeout=10)
        
        if process.returncode == 0:
            logger.info("Redis server started successfully")
            return True
        else:
            logger.warning("Failed to start Redis with systemctl, trying direct command...")
            
            # Try direct Redis command
            process = subprocess.Popen(
                ["redis-server", "--daemonize", "yes"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            process.wait(timeout=10)
            
            if process.returncode == 0:
                logger.info("Redis server started successfully")
                return True
            else:
                logger.error("Failed to start Redis server")
                return False
                
    except Exception as e:
        logger.error(f"Error starting Redis: {e}")
        return False


def start_rabbitmq():
    """Start RabbitMQ server if not running"""
    logger.info("Checking RabbitMQ server...")
    
    if check_service_running("RabbitMQ", ["sudo", "rabbitmqctl", "status"]):
        logger.info("RabbitMQ server is already running")
        return True
    
    logger.info("Starting RabbitMQ server...")
    try:
        # Try to start RabbitMQ using systemctl
        process = subprocess.Popen(
            ["sudo", "systemctl", "start", "rabbitmq-server"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        process.wait(timeout=15)
        
        if process.returncode == 0:
            # Enable management plugin
            subprocess.run(["sudo", "rabbitmq-plugins", "enable", "rabbitmq_management"], 
                         capture_output=True)
            logger.info("RabbitMQ server started successfully")
            return True
        else:
            logger.error("Failed to start RabbitMQ server")
            return False
            
    except Exception as e:
        logger.error(f"Error starting RabbitMQ: {e}")
        return False


def start_celery_worker():
    """Start Celery worker with enhanced logging"""
    logger.info("Starting Celery worker...")
    
    # Get the virtual environment Python executable
    venv_python = os.path.join(os.path.dirname(__file__), "venv", "bin", "python")
    
    concurrency = settings.celery_worker_concurrency
    cmd = [
        venv_python, "-m", "celery", "-A", "workers.celery_app", "worker",
        "--loglevel=info",
        f"--concurrency={concurrency}",
        "--queues=user_processing",
        "--hostname=worker@%h",
        "--prefetch-multiplier=1",  # One task per worker for independence
        "--without-gossip",  # Reduce network overhead
        "--without-mingle",  # Reduce startup overhead
        "--without-heartbeat",  # Reduce heartbeat overhead
        "--pool=prefork",  # Use prefork pool for maximum isolation
        "--max-tasks-per-child=1000",  # Restart workers after 1000 tasks
        "--time-limit=300",  # 5 minutes max per task
        "--soft-time-limit=240",  # 4 minutes soft limit
        "--autoscale=1,10",  # Auto-scale between 1 and 10 workers
        "--max-memory-per-child=200000",  # Restart if memory exceeds 200MB
        "--without-mingle",  # Reduce startup noise
        "--without-heartbeat",  # Reduce heartbeat noise
    ]
    
    try:
        # Start worker with enhanced visibility
        print("\n" + "🔧" * 20 + " CELERY WORKER STARTING " + "🔧" * 20)
        process = subprocess.Popen(
            cmd,
            cwd=os.path.join(os.path.dirname(__file__), "app"),
            stdout=None,  # Use parent's stdout to see logs
            stderr=None,  # Use parent's stderr to see logs
            universal_newlines=True,
            env={**os.environ, "CELERY_WORKER_RUNNING": "1"}  # Add environment flag
        )
        
        processes["celery_worker"] = process
        logger.info(f"Celery worker started with PID: {process.pid}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to start Celery worker: {e}")
        return False


def start_fastapi():
    """Start FastAPI application with minimal logging"""
    logger.info("Starting FastAPI application...")
    
    # Get the virtual environment Python executable
    venv_python = os.path.join(os.path.dirname(__file__), "venv", "bin", "python")
    
    cmd = [
        venv_python, "-m", "uvicorn", "main:app",
        "--host", settings.api_host,
        "--port", str(settings.api_port),
        "--reload" if settings.debug else "",
        "--log-level", "warning"  # Reduce FastAPI log noise
    ]
    
    # Remove empty strings from command
    cmd = [arg for arg in cmd if arg]
    
    try:
        print("🌐 Starting FastAPI...")
        process = subprocess.Popen(
            cmd,
            cwd=os.path.join(os.path.dirname(__file__), "app"),
            stdout=subprocess.PIPE,  # Capture stdout to see errors
            stderr=subprocess.PIPE,  # Capture stderr to see errors
            universal_newlines=True
        )
        
        # Wait a moment to see if it starts successfully
        time.sleep(2)
        
        # Check if process is still running
        if process.poll() is not None:
            # Process died, get the error output
            stdout, stderr = process.communicate()
            logger.error(f"FastAPI failed to start!")
            logger.error(f"STDOUT: {stdout}")
            logger.error(f"STDERR: {stderr}")
            return False
        
        processes["fastapi"] = process
        logger.info(f"FastAPI started with PID: {process.pid}")
        logger.info(f"FastAPI will be available at: http://{settings.api_host}:{settings.api_port}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to start FastAPI: {e}")
        return False


def start_celery_beat():
    """Start Celery beat scheduler with minimal logging"""
    logger.info("Starting Celery beat...")
    
    # Get the virtual environment Python executable
    venv_python = os.path.join(os.path.dirname(__file__), "venv", "bin", "python")
    
    cmd = [
        venv_python, "-m", "celery", "-A", "workers.celery_app", "beat",
        "--loglevel=warning",  # Reduce beat log noise
        "--scheduler=celery.beat.PersistentScheduler"
    ]
    
    try:
        print("⏰ Starting Celery Beat (logs minimized for worker visibility)...")
        process = subprocess.Popen(
            cmd,
            cwd=os.path.join(os.path.dirname(__file__), "app"),
            stdout=subprocess.DEVNULL,  # Suppress beat logs
            stderr=subprocess.DEVNULL,  # Suppress beat logs
            universal_newlines=True
        )
        
        processes["celery_beat"] = process
        logger.info(f"Celery beat started with PID: {process.pid}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to start Celery beat: {e}")
        return False


def monitor_processes():
    """Monitor all processes and restart if needed"""
    while not stop_event.is_set():
        for name, process in processes.items():
            if process.poll() is not None:
                logger.warning(f"{name} process died, restarting...")
                if name == "fastapi":
                    start_fastapi()
                elif name == "celery_worker":
                    start_celery_worker()
                elif name == "celery_beat":
                    start_celery_beat()
        
        time.sleep(5)


def print_status():
    """Print current status of all services with worker focus"""
    print("\n" + "="*60)
    print("🚀 SERVICE STATUS")
    print("="*60)
    
    for name, process in processes.items():
        if name == "celery_worker":
            if process.poll() is None:
                print(f"🔧 {name.upper()}: Running (PID: {process.pid}) - WORKER LOGS BELOW")
            else:
                print(f"❌ {name.upper()}: Stopped")
        else:
            if process.poll() is None:
                print(f"✅ {name.upper()}: Running (PID: {process.pid})")
            else:
                print(f"❌ {name.upper()}: Stopped")
    
    print(f"🌐 FastAPI: http://{settings.api_host}:{settings.api_port}")
    print(f"📚 API Docs: http://{settings.api_host}:{settings.api_port}/docs")
    print(f"🔧 Celery Workers: {settings.celery_worker_concurrency}")
    print(f"⏰ Task Interval: {settings.task_interval_seconds} seconds")
    print("="*60)
    print("🔧 WORKER LOGS WILL APPEAR BELOW - WATCH FOR TASK PROCESSING")
    print("="*60 + "\n")


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info("Received shutdown signal, stopping all services...")
    stop_event.set()
    
    # Stop all processes
    for name, process in processes.items():
        if process.poll() is None:  # Process is still running
            logger.info(f"Stopping {name}...")
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
    
    logger.info("All services stopped")
    sys.exit(0)


def main():
    """Main function to start all services"""
    logger.info("Starting all services...")
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start infrastructure services
    if not start_redis():
        logger.error("Failed to start Redis, exiting...")
        sys.exit(1)
    
    if not start_rabbitmq():
        logger.error("Failed to start RabbitMQ, exiting...")
        sys.exit(1)
    
    # Wait a bit for services to be ready
    logger.info("Waiting for services to be ready...")
    time.sleep(3)
    
    # Start FastAPI
    if not start_fastapi():
        logger.error("Failed to start FastAPI, exiting...")
        sys.exit(1)
    
    # Start Celery services
    if not start_celery_worker():
        logger.error("Failed to start Celery worker, exiting...")
        sys.exit(1)
    
    if not start_celery_beat():
        logger.error("Failed to start Celery beat, exiting...")
        sys.exit(1)
    
    logger.info("Complete system started successfully!")
    print_status()
    
    # Start monitoring thread
    monitor_thread = threading.Thread(target=monitor_processes, daemon=True)
    monitor_thread.start()
    
    # Keep main thread alive
    try:
        while not stop_event.is_set():
            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)


if __name__ == "__main__":
    main()
