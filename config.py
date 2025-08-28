"""
Configuration management for OncoStaging application.
Centralized configuration with environment variable support.
"""

import os
from typing import Dict, List
import logging

# Application Settings
APP_NAME = "OncoStaging"
APP_VERSION = "1.0.0"

# File Upload Settings
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
ALLOWED_FILE_TYPES = ["pdf", "docx"]
ALLOWED_MIME_TYPES = [
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
]

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = "oncostaging.log"

# Cache Settings
CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() == "true"
CACHE_TTL_HOURS = int(os.getenv("CACHE_TTL_HOURS", "24"))
CACHE_DIR = ".cache"

# Medical Data Validation Ranges
TUMOR_SIZE_RANGE = {
    "min": 0.1,  # cm
    "max": 50.0  # cm
}

LYMPH_NODES_RANGE = {
    "min": 0,
    "max": 100
}

# Feature Extraction Settings
CONFIDENCE_THRESHOLD = 0.6
MIN_TEXT_LENGTH = 100

# Cancer Type Keywords
CANCER_TYPE_KEYWORDS = {
    "gallbladder": ["gallbladder", "gb carcinoma", "cholangiocarcinoma"],
    "esophageal": ["esophagus", "esophageal", "oesophageal"],
    "breast": ["breast", "mammary", "ductal carcinoma", "lobular carcinoma"],
    "lung": ["lung", "pulmonary", "nsclc", "sclc", "bronchogenic"],
    "colorectal": ["colon", "rectum", "colorectal", "rectal", "colonic"],
    "head and neck": ["oral cavity", "oropharynx", "larynx", "pharynx", "head and neck"]
}

# TNM Staging Keywords
TNM_KEYWORDS = {
    "tumor_depth": [
        "mucosa", "submucosa", "muscularis", "subserosa", 
        "serosa", "adventitia", "muscularis propria"
    ],
    "metastasis": [
        "metastasis", "metastases", "metastatic", "distant spread",
        "secondary", "disseminated"
    ],
    "liver_invasion": [
        "liver invasion", "hepatic invasion", "involving segments",
        "liver involvement", "hepatic involvement"
    ]
}

# Feedback Settings
FEEDBACK_CSV_FILE = "feedback_log.csv"
FEEDBACK_FIELDS = ["timestamp", "helpful", "anxiety", "stage", "cancer_type"]

# UI Settings
PAGE_TITLE = "🏥 OncoStaging - Cancer Staging Assistant"
PAGE_ICON = "🏥"
SIDEBAR_STATE = "expanded"

# Error Messages
ERROR_MESSAGES = {
    "file_too_large": "File is too large (maximum {max_size}MB). Please upload a smaller file.",
    "invalid_file_type": "Invalid file type. Only PDF and DOCX files are supported.",
    "processing_error": "Document processing error occurred. Please try again.",
    "extraction_error": "Failed to extract medical information.",
    "staging_error": "Failed to determine cancer staging.",
    "cancer_type_not_found": "Cancer type could not be identified from the report.",
    "insufficient_data": "Insufficient data for staging determination."
}

# Success Messages
SUCCESS_MESSAGES = {
    "file_uploaded": "✅ File uploaded successfully.",
    "processing_complete": "✅ Report analyzed successfully.",
    "feedback_submitted": "🙏 Thank you for your feedback!"
}

# Treatment Guidelines URLs
TREATMENT_GUIDELINES_URLS = {
    "gallbladder": "https://www.nccn.org/professionals/physician_gls/pdf/hepatobiliary.pdf",
    "esophageal": "https://www.nccn.org/professionals/physician_gls/pdf/esophageal.pdf",
    "breast": "https://www.nccn.org/professionals/physician_gls/pdf/breast.pdf",
    "lung": "https://www.nccn.org/professionals/physician_gls/pdf/nscl.pdf",
    "colorectal": "https://www.nccn.org/professionals/physician_gls/pdf/colon.pdf",
    "head and neck": "https://www.nccn.org/professionals/physician_gls/pdf/head-and-neck.pdf"
}


def setup_logging() -> None:
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format=LOG_FORMAT,
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler()
        ]
    )


def get_config() -> Dict:
    """Get all configuration as dictionary."""
    return {
        "app": {
            "name": APP_NAME,
            "version": APP_VERSION
        },
        "file_upload": {
            "max_size_mb": MAX_FILE_SIZE_MB,
            "allowed_types": ALLOWED_FILE_TYPES
        },
        "cache": {
            "enabled": CACHE_ENABLED,
            "ttl_hours": CACHE_TTL_HOURS
        },
        "logging": {
            "level": LOG_LEVEL,
            "file": LOG_FILE
        }
    }
