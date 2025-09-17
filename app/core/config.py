"""
Configuration settings for Portal Engine
"""
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
import sys


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    app_name: str = "Portal Engine"
    debug: bool = True
    database_url: str = "sqlite:///./test.db"

    # ✅ Pydantic v2 way (no inner Config class)
    model_config = ConfigDict(env_file=".env", extra="ignore")

    # Application
    app_name: str = Field(default="Portal Engine", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    environment: str = Field(default="production", env=["APP_ENV", "ENVIRONMENT"])
    debug: bool = Field(default=False, env="DEBUG")
    
    # API Settings
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=3031, env="API_PORT")
    api_prefix: str = Field(default="/api/v1", env="API_PREFIX")
    
    # Redis Settings
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_db: int = Field(default=0, env="REDIS_DB")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    redis_namespace: str = Field(default="recommendations", env="REDIS_NAMESPACE")
    
    # RabbitMQ Settings
    rabbitmq_host: str = Field(default="localhost", env="RABBITMQ_HOST")
    rabbitmq_port: int = Field(default=5672, env="RABBITMQ_PORT")
    rabbitmq_user: str = Field(default="guest", env="RABBITMQ_USER")
    rabbitmq_password: str = Field(default="guest", env="RABBITMQ_PASSWORD")
    rabbitmq_vhost: str = Field(default="/", env="RABBITMQ_VHOST")
    
    # Celery Settings
    celery_broker_url: str = Field(
        default="amqp://guest:guest@localhost:5672//", 
        env="CELERY_BROKER_URL"
    )
    celery_result_backend: str = Field(
        default="redis://localhost:6379/0", 
        env="CELERY_RESULT_BACKEND"
    )
    
    # External Services
    user_profile_service_url: str = Field(
        default="http://localhost:8000", 
        env="USER_PROFILE_SERVICE_URL"
    )
    lie_service_url: str = Field(
        default="http://localhost:8000", 
        env="LIE_SERVICE_URL"
    )
    cis_service_url: str = Field(
        default="http://localhost:8000", 
        env="CIS_SERVICE_URL"
    )
    prefetch_service_url: str = Field(
        default="http://localhost:8000", 
        env="PREFETCH_SERVICE_URL"
    )
    recommendation_api_url: str = Field(
        default="http://localhost:8080",
        env="RECOMMENDATION_API_URL"
    )
    recommendation_api_provider: str = Field(
        default="groq",
        env="RECOMMENDATION_API_PROVIDER"
    )
    
    # Scheduling
    recommendation_refresh_interval_minutes: int = Field(
        default=30, 
        env="RECOMMENDATION_REFRESH_INTERVAL_MINUTES"
    )

    # Task interval
    task_interval_seconds: int = Field(default=10, env="TASK_INTERVAL_SECONDS")
    
    # Celery Worker Configuration
    celery_worker_concurrency: int = Field(default=10, env="CELERY_WORKER_CONCURRENCY")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    


# Global settings instance
settings = Settings()
if "pytest" in sys.modules:
    settings.environment = "test"