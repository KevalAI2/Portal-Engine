#!/usr/bin/env python3
"""
Script to stop all services and processes running on ports
"""
import os
import sys
import subprocess
import signal
import time
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# Add app directory to Python path for relative imports
app_dir = current_dir / "app"
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

# Temporarily change working directory to app for relative imports to work
original_cwd = os.getcwd()
os.chdir(app_dir)

try:
    from core.config import settings
    from core.logging import get_logger
finally:
    # Restore original working directory
    os.chdir(original_cwd)

logger = get_logger("stop_services")


def get_processes_on_port(port: int) -> list:
    """Get all processes running on a specific port"""
    try:
        result = subprocess.run(
            ["lsof", "-ti", f":{port}"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip().split('\n')
        return []
    except Exception as e:
        logger.warning(f"Could not check port {port}: {e}")
        return []


def kill_processes_on_port(port: int, process_name: str = ""):
    """Kill all processes running on a specific port"""
    pids = get_processes_on_port(port)
    if pids:
        logger.info(f"Found {len(pids)} process(es) on port {port} ({process_name})")
        for pid in pids:
            try:
                pid = pid.strip()
                if pid:
                    logger.info(f"Killing process {pid} on port {port}")
                    os.kill(int(pid), signal.SIGTERM)
                    time.sleep(1)
                    # Check if process is still running, force kill if needed
                    try:
                        os.kill(int(pid), 0)  # Check if process exists
                        logger.warning(f"Process {pid} still running, force killing...")
                        os.kill(int(pid), signal.SIGKILL)
                    except OSError:
                        logger.info(f"Process {pid} stopped successfully")
            except Exception as e:
                logger.error(f"Error killing process {pid}: {e}")
    else:
        logger.info(f"No processes found on port {port} ({process_name})")


def stop_celery_processes():
    """Stop all Celery processes"""
    logger.info("Stopping Celery processes...")
    
    try:
        # Stop Celery beat
        subprocess.run(["pkill", "-f", "celery.*beat"], capture_output=True)
        
        # Stop Celery workers
        subprocess.run(["pkill", "-f", "celery.*worker"], capture_output=True)
        
        # Stop any remaining Celery processes
        subprocess.run(["pkill", "-f", "celery"], capture_output=True)
        
        logger.info("Celery processes stopped")
    except Exception as e:
        logger.error(f"Error stopping Celery processes: {e}")


def stop_python_processes():
    """Stop Python processes related to our application"""
    logger.info("Stopping Python application processes...")
    
    try:
        # Stop FastAPI/uvicorn processes
        subprocess.run(["pkill", "-f", "uvicorn.*app.main"], capture_output=True)
        
        # Stop any Python processes running our scripts
        subprocess.run(["pkill", "-f", "python.*start_all_services"], capture_output=True)
        subprocess.run(["pkill", "-f", "python.*main.py"], capture_output=True)
        
        logger.info("Python application processes stopped")
    except Exception as e:
        logger.error(f"Error stopping Python processes: {e}")


def stop_redis():
    """Stop Redis server"""
    logger.info("Stopping Redis server...")
    
    try:
        # Try systemctl first
        result = subprocess.run(
            ["sudo", "systemctl", "stop", "redis-server"],
            capture_output=True,
            timeout=10
        )
        
        if result.returncode == 0:
            logger.info("Redis server stopped via systemctl")
        else:
            # Try direct kill
            subprocess.run(["pkill", "-f", "redis-server"], capture_output=True)
            logger.info("Redis server stopped via direct kill")
            
    except Exception as e:
        logger.error(f"Error stopping Redis: {e}")


def stop_rabbitmq():
    """Stop RabbitMQ server"""
    logger.info("Stopping RabbitMQ server...")
    
    try:
        # Try systemctl first
        result = subprocess.run(
            ["sudo", "systemctl", "stop", "rabbitmq-server"],
            capture_output=True,
            timeout=15
        )
        
        if result.returncode == 0:
            logger.info("RabbitMQ server stopped via systemctl")
        else:
            # Try direct kill
            subprocess.run(["pkill", "-f", "rabbitmq"], capture_output=True)
            logger.info("RabbitMQ server stopped via direct kill")
            
    except Exception as e:
        logger.error(f"Error stopping RabbitMQ: {e}")


def stop_project_ports():
    """Stop processes only on ports used by this project"""
    logger.info("Stopping processes on project-specific ports...")
    
    # Only ports used by this specific project
    project_ports = [
        (settings.api_port, "FastAPI API"),
        (5672, "RabbitMQ Broker"),
        (15672, "RabbitMQ Management"),
        (6379, "Redis Cache"),
    ]
    
    for port, service_name in project_ports:
        kill_processes_on_port(port, service_name)


def cleanup_temp_files():
    """Clean up temporary files created by Celery"""
    logger.info("Cleaning up temporary files...")
    
    try:
        # Remove Celery beat schedule file
        schedule_file = Path("celerybeat-schedule")
        if schedule_file.exists():
            schedule_file.unlink()
            logger.info("Removed celerybeat-schedule file")
        
        # Remove any .pid files
        for pid_file in Path(".").glob("*.pid"):
            pid_file.unlink()
            logger.info(f"Removed {pid_file}")
            
    except Exception as e:
        logger.error(f"Error cleaning up files: {e}")


def main():
    """Main function to stop project services only"""
    logger.info("Stopping project services and processes...")
    
    try:
        # Stop application processes first
        stop_python_processes()
        time.sleep(2)
        
        # Stop Celery processes
        stop_celery_processes()
        time.sleep(2)
        
        # Stop processes on project-specific ports only
        stop_project_ports()
        time.sleep(2)
        
        # Stop infrastructure services
        stop_redis()
        stop_rabbitmq()
        time.sleep(2)
        
        # Final cleanup
        cleanup_temp_files()
        
        logger.info("Project services stopped successfully!")
        logger.info("You can now start services again with: python start_all_services.py")
        
    except KeyboardInterrupt:
        logger.info("Stopping process interrupted by user")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
