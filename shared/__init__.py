"""
Shared models and interfaces for the ProCert content management system.

This package contains all the core data models and service interfaces
used across the application components.
"""

from .models import (
    ContentMetadata,
    QuestionAnswer,
    UserProgress,
    VectorDocument,
    ContentType,
    CertificationType,
    DifficultyLevel,
    ProgressType,
    validate_model,
    validate_models,
    detect_certification_from_filename,
    get_certification_display_name,
    get_certification_level,
    get_certifications_for_dropdown,
    validate_certification_code
)

from .interfaces import (
    ProcessingResult,
    ValidationResult,
    SearchResult,
    ContentClassification,
    ContentChunk,
    PerformanceMetrics,
    InteractionData,
    IContentIngestionService,
    IContentProcessor,
    IStorageManager,
    ISearchService,
    IProgressTracker,
    IServiceFactory,
    IConfiguration
)

from .storage_manager import StorageManager

__version__ = "1.0.0"

__all__ = [
    # Models
    "ContentMetadata",
    "QuestionAnswer", 
    "UserProgress",
    "VectorDocument",
    "ContentType",
    "CertificationType",
    "DifficultyLevel",
    "ProgressType",
    "validate_model",
    "validate_models",
    
    # Certification utilities
    "detect_certification_from_filename",
    "get_certification_display_name",
    "get_certification_level",
    "get_certifications_for_dropdown",
    "validate_certification_code",
    
    # Result classes
    "ProcessingResult",
    "ValidationResult",
    "SearchResult",
    "ContentClassification",
    "ContentChunk",
    "PerformanceMetrics",
    "InteractionData",
    
    # Service interfaces
    "IContentIngestionService",
    "IContentProcessor",
    "IStorageManager",
    "ISearchService",
    "IProgressTracker",
    "IServiceFactory",
    "IConfiguration",
    
    # Service implementations
    "StorageManager"
]