"""Configuration settings for NYC Taxi Batch Prediction System"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Project paths
    PROJECT_ROOT: Path = Path(__file__).parent.parent
    DATA_INPUT_DIR: Path = PROJECT_ROOT / "data" / "input"
    DATA_OUTPUT_DIR: Path = PROJECT_ROOT / "data" / "output"
    DATA_PROCESSED_DIR: Path = PROJECT_ROOT / "data" / "processed"
    LOGS_DIR: Path = PROJECT_ROOT / "logs"
    MODEL_PATH: Path = PROJECT_ROOT / "lin_reg.bin"
    
    # Batch processing settings
    BATCH_SIZE: int = 1000
    MAX_WORKERS: int = 4
    CHUNK_SIZE: int = 100
    
    # Data generation settings
    NUM_TRIPS_PER_BATCH: int = 5000
    MIN_TRIP_DISTANCE: float = 0.1
    MAX_TRIP_DISTANCE: float = 50.0
    MIN_LOCATION_ID: int = 1
    MAX_LOCATION_ID: int = 263
    
    # Prefect settings
    PREFECT_API_URL: Optional[str] = None
    PREFECT_WORK_POOL: str = "default-agent-pool"
    
    # Scheduling settings
    BATCH_SCHEDULE_CRON: str = "0 */2 * * *"  # Every 2 hours
    CLEANUP_SCHEDULE_CRON: str = "0 2 * * *"  # Daily at 2 AM
    
    # Monitoring settings
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    
    # Retention settings
    OUTPUT_RETENTION_DAYS: int = 30
    LOG_RETENTION_DAYS: int = 7
    
    # Performance settings
    MEMORY_LIMIT_GB: float = 4.0
    CPU_LIMIT_PERCENT: float = 80.0
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()

# Ensure directories exist
for directory in [
    settings.DATA_INPUT_DIR,
    settings.DATA_OUTPUT_DIR,
    settings.DATA_PROCESSED_DIR,
    settings.LOGS_DIR,
]:
    directory.mkdir(parents=True, exist_ok=True)
