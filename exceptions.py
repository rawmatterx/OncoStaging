"""
Custom exception classes for OncoStaging application.
Provides specific error handling for different failure scenarios.
"""

class OncoStagingError(Exception):
    """Base exception class for OncoStaging application."""
    pass


class DocumentProcessingError(OncoStagingError):
    """Raised when document processing fails."""
    pass


class FileValidationError(OncoStagingError):
    """Raised when file validation fails."""
    pass


class FeatureExtractionError(OncoStagingError):
    """Raised when feature extraction fails."""
    pass


class StagingError(OncoStagingError):
    """Raised when cancer staging calculation fails."""
    pass


class ConfigurationError(OncoStagingError):
    """Raised when configuration is invalid."""
    pass


class MedicalDataValidationError(OncoStagingError):
    """Raised when medical data validation fails."""
    pass