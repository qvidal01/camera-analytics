"""
Application settings management using Pydantic Settings.

This module provides centralized configuration management with environment variable
support, validation, and type safety.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    All settings can be overridden via environment variables.
    See .env.example for available options.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # API Server Settings
    api_host: str = Field(default="0.0.0.0", description="API server bind address")
    api_port: int = Field(default=8000, ge=1, le=65535, description="API server port")
    api_workers: int = Field(default=4, ge=1, description="Number of worker processes")
    secret_key: str = Field(default="change-me-in-production", description="JWT secret key")
    access_token_expire_minutes: int = Field(default=30, ge=1, description="JWT token lifetime")

    # Database Settings
    database_url: str = Field(
        default="postgresql://postgres:password@localhost:5432/camera_analytics",
        description="PostgreSQL connection URL",
    )
    database_pool_size: int = Field(default=20, ge=1, description="Database connection pool size")
    database_max_overflow: int = Field(default=10, ge=0, description="Max overflow connections")

    # Redis Settings
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis connection URL")

    # AI Model Settings
    model_path: str = Field(default="./models", description="Directory for AI models")
    default_detection_model: str = Field(default="yolov8n", description="Default YOLO model")
    detection_confidence_threshold: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Minimum detection confidence"
    )
    detection_device: Literal["cpu", "cuda", "mps"] = Field(
        default="cpu", description="Device for inference"
    )
    batch_size: int = Field(default=4, ge=1, description="Inference batch size")

    # Camera Settings
    max_cameras: int = Field(default=16, ge=1, description="Maximum concurrent cameras")
    default_fps: int = Field(default=15, ge=1, le=60, description="Default camera FPS")
    default_resolution: str = Field(default="1920x1080", description="Default resolution")
    reconnect_delay_seconds: int = Field(default=5, ge=1, description="Reconnection delay")
    max_reconnect_attempts: int = Field(default=10, ge=1, description="Max reconnection attempts")

    # Recording Settings
    recording_path: str = Field(default="./recordings", description="Recording storage path")
    recording_retention_days: int = Field(default=30, ge=1, description="Recording retention")
    recording_format: str = Field(default="mp4", description="Video recording format")
    event_buffer_seconds: int = Field(default=10, ge=0, description="Pre-event buffer duration")

    # Alert Settings (Email)
    smtp_host: str = Field(default="smtp.gmail.com", description="SMTP server host")
    smtp_port: int = Field(default=587, ge=1, le=65535, description="SMTP server port")
    smtp_user: str = Field(default="", description="SMTP username")
    smtp_password: str = Field(default="", description="SMTP password")
    smtp_from: str = Field(
        default="alerts@camera-analytics.local", description="From email address"
    )
    alert_email_to: str = Field(default="", description="Default alert recipient")

    # Optional: Twilio Settings
    twilio_account_sid: str = Field(default="", description="Twilio account SID")
    twilio_auth_token: str = Field(default="", description="Twilio auth token")
    twilio_from_number: str = Field(default="", description="Twilio from phone number")
    twilio_to_number: str = Field(default="", description="Twilio to phone number")

    # Optional: Webhook
    webhook_url: str = Field(default="", description="Webhook notification URL")

    # Logging Settings
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Logging level"
    )
    log_format: Literal["json", "text"] = Field(default="json", description="Log format")

    # Security Settings
    encryption_key: str = Field(
        default="", description="Fernet encryption key for credentials"
    )
    allowed_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="CORS allowed origins",
    )

    # Performance Settings
    enable_gpu: bool = Field(default=True, description="Enable GPU acceleration")
    enable_tensorrt: bool = Field(default=False, description="Enable TensorRT optimization")
    enable_frame_batching: bool = Field(default=True, description="Enable frame batching")

    # Development Settings
    debug: bool = Field(default=False, description="Enable debug mode")
    reload: bool = Field(default=False, description="Enable auto-reload")

    @field_validator("default_resolution")
    @classmethod
    def validate_resolution(cls, v: str) -> str:
        """Validate resolution format (WIDTHxHEIGHT)."""
        try:
            width, height = v.split("x")
            w, h = int(width), int(height)
            if w <= 0 or h <= 0:
                raise ValueError("Width and height must be positive")
            return v
        except (ValueError, AttributeError):
            raise ValueError(f"Invalid resolution format: {v}. Expected WIDTHxHEIGHT")

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_origins(cls, v):
        """Parse comma-separated origins from environment variable."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v


@lru_cache
def get_settings() -> Settings:
    """
    Get cached application settings.

    Returns:
        Settings: Application settings instance.

    Note:
        Settings are cached for performance. To reload settings,
        clear the cache: get_settings.cache_clear()
    """
    return Settings()
