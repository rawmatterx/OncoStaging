"""
Configuration management for OncoStaging application.
Centralizes all configuration settings and constants.
"""

import os
from typing import Dict, List
from dataclasses import dataclass


@dataclass
class AppConfig:
    """Application configuration settings."""
    
    # File processing settings
    MAX_FILE_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: List[str] = None
    UPLOAD_TIMEOUT_SECONDS: int = 30
    
    # Text processing settings
    MAX_TEXT_LENGTH: int = 1000000  # 1MB of text
    CACHE_ENABLED: bool = True
    CACHE_TTL_SECONDS: int = 3600
    
    # Medical data validation
    MAX_TUMOR_SIZE_CM: float = 50.0
    MAX_LYMPH_NODES: int = 100
    
    # UI settings
    PAGE_TITLE: str = "Cancer Staging Chatbot"
    PAGE_ICON: str = "🤖"
    
    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "oncostaging.log"
    
    # Feedback settings
    FEEDBACK_CSV_FILE: str = "feedback_log.csv"
    
    def __post_init__(self):
        if self.ALLOWED_EXTENSIONS is None:
            self.ALLOWED_EXTENSIONS = ["pdf", "docx"]


class ConfigManager:
    """Manages application configuration with environment variable support."""
    
    def __init__(self):
        self._config = AppConfig()
        self._load_from_env()
    
    def _load_from_env(self):
        """Load configuration from environment variables."""
        # File processing
        if os.getenv("MAX_FILE_SIZE_MB"):
            self._config.MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB"))
        
        if os.getenv("UPLOAD_TIMEOUT_SECONDS"):
            self._config.UPLOAD_TIMEOUT_SECONDS = int(os.getenv("UPLOAD_TIMEOUT_SECONDS"))
        
        # Cache settings
        if os.getenv("CACHE_ENABLED"):
            self._config.CACHE_ENABLED = os.getenv("CACHE_ENABLED").lower() == "true"
        
        # Logging
        if os.getenv("LOG_LEVEL"):
            self._config.LOG_LEVEL = os.getenv("LOG_LEVEL")
    
    @property
    def config(self) -> AppConfig:
        """Get the current configuration."""
        return self._config
    
    def get_staging_guidelines_urls(self) -> Dict[str, str]:
        """Get NCCN guidelines URLs for different cancer types."""
        return {
            "gallbladder": "https://www.nccn.org/professionals/physician_gls/pdf/hepatobiliary.pdf",
            "esophageal": "https://www.nccn.org/professionals/physician_gls/pdf/esophageal.pdf",
            "breast": "https://www.nccn.org/professionals/physician_gls/pdf/breast.pdf",
            "lung": "https://www.nccn.org/professionals/physician_gls/pdf/nscl.pdf",
            "colorectal": "https://www.nccn.org/professionals/physician_gls/pdf/colon.pdf",
            "head_and_neck": "https://www.nccn.org/professionals/physician_gls/pdf/head-and-neck.pdf"
        }


# Global configuration instance
config_manager = ConfigManager()