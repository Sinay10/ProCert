"""
Data models for the ProCert content management system.

This module contains all the core data models used across the application,
including content metadata, questions/answers, user progress, and vector documents.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from enum import Enum
import re
import json


class ContentType(Enum):
    """Enumeration of supported content types."""
    QUESTION = "question"
    STUDY_GUIDE = "study_guide"
    PRACTICE_EXAM = "practice_exam"
    DOCUMENTATION = "documentation"


class CertificationType(Enum):
    """Enumeration of supported AWS certification types."""
    # Foundational
    CCP = "CCP"  # AWS Certified Cloud Practitioner
    AIP = "AIP"  # AWS Certified AI Practitioner
    
    # Associate Level
    MLA = "MLA"  # AWS Certified Machine Learning Engineer - Associate
    DEA = "DEA"  # AWS Certified Data Engineer - Associate
    DVA = "DVA"  # AWS Certified Developer - Associate
    SAA = "SAA"  # AWS Certified Solutions Architect - Associate
    SOA = "SOA"  # AWS Certified SysOps Administrator - Associate
    
    # Professional Level
    DOP = "DOP"  # AWS Certified DevOps Engineer - Professional
    SAP = "SAP"  # AWS Certified Solutions Architect - Professional
    
    # Specialty
    ANS = "ANS"  # AWS Certified Advanced Networking - Specialty
    MLS = "MLS"  # AWS Certified Machine Learning - Specialty
    SCS = "SCS"  # AWS Certified Security - Specialty
    
    # General/Unknown
    GENERAL = "GENERAL"


class DifficultyLevel(Enum):
    """Enumeration of difficulty levels."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class ProgressType(Enum):
    """Enumeration of progress tracking types."""
    VIEWED = "viewed"
    ANSWERED = "answered"
    COMPLETED = "completed"


@dataclass
class ContentMetadata:
    """
    Metadata for content items in the system.
    
    This model represents the core metadata for any piece of content,
    including questions, study guides, and other materials.
    """
    content_id: str
    title: str
    content_type: ContentType
    certification_type: CertificationType
    category: str
    subcategory: Optional[str] = None
    difficulty_level: DifficultyLevel = DifficultyLevel.INTERMEDIATE
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    version: str = "1.0"
    source_file: str = ""
    source_bucket: str = ""
    chunk_count: int = 0
    question_count: Optional[int] = None

    def validate(self) -> List[str]:
        """
        Validate the content metadata.
        
        Returns:
            List of validation error messages. Empty list if valid.
        """
        errors = []
        
        if not self.content_id or not self.content_id.strip():
            errors.append("content_id is required and cannot be empty")
        
        if not self.title or not self.title.strip():
            errors.append("title is required and cannot be empty")
        
        if not self.category or not self.category.strip():
            errors.append("category is required and cannot be empty")
        
        if self.chunk_count < 0:
            errors.append("chunk_count cannot be negative")
        
        if self.question_count is not None and self.question_count < 0:
            errors.append("question_count cannot be negative")
        
        # Validate version format (semantic versioning)
        version_pattern = r'^\d+\.\d+(\.\d+)?$'
        if not re.match(version_pattern, self.version):
            errors.append("version must follow semantic versioning format (e.g., '1.0' or '1.0.0')")
        
        return errors

    def is_valid(self) -> bool:
        """Check if the content metadata is valid."""
        return len(self.validate()) == 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'content_id': self.content_id,
            'title': self.title,
            'content_type': self.content_type.value,
            'certification_type': self.certification_type.value,
            'category': self.category,
            'subcategory': self.subcategory,
            'difficulty_level': self.difficulty_level.value,
            'tags': self.tags,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'version': self.version,
            'source_file': self.source_file,
            'source_bucket': self.source_bucket,
            'chunk_count': self.chunk_count,
            'question_count': self.question_count
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContentMetadata':
        """Create instance from dictionary."""
        return cls(
            content_id=data['content_id'],
            title=data['title'],
            content_type=ContentType(data['content_type']),
            certification_type=CertificationType(data['certification_type']),
            category=data['category'],
            subcategory=data.get('subcategory'),
            difficulty_level=DifficultyLevel(data.get('difficulty_level', 'intermediate')),
            tags=data.get('tags', []),
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            version=data.get('version', '1.0'),
            source_file=data.get('source_file', ''),
            source_bucket=data.get('source_bucket', ''),
            chunk_count=data.get('chunk_count', 0),
            question_count=data.get('question_count')
        )


@dataclass
class QuestionAnswer:
    """
    Model for question and answer pairs.
    
    Represents individual questions with their answers, explanations,
    and associated metadata.
    """
    question_id: str
    content_id: str
    question_text: str
    answer_options: List[str]
    correct_answer: str
    explanation: Optional[str] = None
    category: str = ""
    difficulty: DifficultyLevel = DifficultyLevel.INTERMEDIATE
    tags: List[str] = field(default_factory=list)

    def validate(self) -> List[str]:
        """
        Validate the question-answer data.
        
        Returns:
            List of validation error messages. Empty list if valid.
        """
        errors = []
        
        if not self.question_id or not self.question_id.strip():
            errors.append("question_id is required and cannot be empty")
        
        if not self.content_id or not self.content_id.strip():
            errors.append("content_id is required and cannot be empty")
        
        if not self.question_text or not self.question_text.strip():
            errors.append("question_text is required and cannot be empty")
        
        if not self.answer_options or len(self.answer_options) < 2:
            errors.append("at least 2 answer options are required")
        
        if not self.correct_answer or not self.correct_answer.strip():
            errors.append("correct_answer is required and cannot be empty")
        
        if self.correct_answer not in self.answer_options:
            errors.append("correct_answer must be one of the answer_options")
        
        return errors

    def is_valid(self) -> bool:
        """Check if the question-answer is valid."""
        return len(self.validate()) == 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'question_id': self.question_id,
            'content_id': self.content_id,
            'question_text': self.question_text,
            'answer_options': self.answer_options,
            'correct_answer': self.correct_answer,
            'explanation': self.explanation,
            'category': self.category,
            'difficulty': self.difficulty.value,
            'tags': self.tags
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QuestionAnswer':
        """Create instance from dictionary."""
        return cls(
            question_id=data['question_id'],
            content_id=data['content_id'],
            question_text=data['question_text'],
            answer_options=data['answer_options'],
            correct_answer=data['correct_answer'],
            explanation=data.get('explanation'),
            category=data.get('category', ''),
            difficulty=DifficultyLevel(data.get('difficulty', 'intermediate')),
            tags=data.get('tags', [])
        )


@dataclass
class UserProgress:
    """
    Model for tracking user progress and interactions.
    
    Records user interactions with content including completion status,
    scores, and time spent.
    """
    user_id: str
    content_id: str
    progress_type: ProgressType
    score: Optional[float] = None
    time_spent: int = 0  # seconds
    timestamp: datetime = field(default_factory=datetime.utcnow)
    session_id: str = ""

    def validate(self) -> List[str]:
        """
        Validate the user progress data.
        
        Returns:
            List of validation error messages. Empty list if valid.
        """
        errors = []
        
        if not self.user_id or not self.user_id.strip():
            errors.append("user_id is required and cannot be empty")
        
        if not self.content_id or not self.content_id.strip():
            errors.append("content_id is required and cannot be empty")
        
        if self.score is not None and (self.score < 0 or self.score > 100):
            errors.append("score must be between 0 and 100")
        
        if self.time_spent < 0:
            errors.append("time_spent cannot be negative")
        
        return errors

    def is_valid(self) -> bool:
        """Check if the user progress is valid."""
        return len(self.validate()) == 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'user_id': self.user_id,
            'content_id': self.content_id,
            'progress_type': self.progress_type.value,
            'score': self.score,
            'time_spent': self.time_spent,
            'timestamp': self.timestamp.isoformat(),
            'session_id': self.session_id
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserProgress':
        """Create instance from dictionary."""
        return cls(
            user_id=data['user_id'],
            content_id=data['content_id'],
            progress_type=ProgressType(data['progress_type']),
            score=data.get('score'),
            time_spent=data.get('time_spent', 0),
            timestamp=datetime.fromisoformat(data['timestamp']),
            session_id=data.get('session_id', '')
        )


@dataclass
class VectorDocument:
    """
    Model for vector embeddings and associated document chunks.
    
    Represents text chunks with their vector embeddings for semantic search,
    including certification-specific metadata for improved RAG filtering.
    """
    document_id: str
    content_id: str
    chunk_index: int
    text: str
    vector_embedding: List[float]
    certification_type: CertificationType
    certification_level: str = ""  # foundational, associate, professional, specialty
    content_type: ContentType = ContentType.STUDY_GUIDE
    category: str = ""
    subcategory: Optional[str] = None
    difficulty_level: DifficultyLevel = DifficultyLevel.INTERMEDIATE
    tags: List[str] = field(default_factory=list)
    source_file: str = ""
    source_bucket: str = ""
    chunk_size: int = 0
    processed_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> List[str]:
        """
        Validate the vector document data.
        
        Returns:
            List of validation error messages. Empty list if valid.
        """
        errors = []
        
        if not self.document_id or not self.document_id.strip():
            errors.append("document_id is required and cannot be empty")
        
        if not self.content_id or not self.content_id.strip():
            errors.append("content_id is required and cannot be empty")
        
        if self.chunk_index < 0:
            errors.append("chunk_index cannot be negative")
        
        if not self.text or not self.text.strip():
            errors.append("text is required and cannot be empty")
        
        if not self.vector_embedding or len(self.vector_embedding) == 0:
            errors.append("vector_embedding is required and cannot be empty")
        
        # Validate embedding dimensions (flexible for different models)
        # Titan: 1536, Claude: varies by model, OpenAI: 1536/3072
        valid_dimensions = [1536, 3072, 1024, 768]  # Common embedding dimensions
        if len(self.vector_embedding) not in valid_dimensions:
            errors.append(f"vector_embedding must have valid dimensions. Got {len(self.vector_embedding)}, expected one of {valid_dimensions}")
        
        return errors

    def is_valid(self) -> bool:
        """Check if the vector document is valid."""
        return len(self.validate()) == 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'document_id': self.document_id,
            'content_id': self.content_id,
            'chunk_index': self.chunk_index,
            'text': self.text,
            'vector_embedding': self.vector_embedding,
            'certification_type': self.certification_type.value,
            'certification_level': self.certification_level,
            'content_type': self.content_type.value,
            'category': self.category,
            'subcategory': self.subcategory,
            'difficulty_level': self.difficulty_level.value,
            'tags': self.tags,
            'source_file': self.source_file,
            'source_bucket': self.source_bucket,
            'chunk_size': self.chunk_size,
            'processed_at': self.processed_at.isoformat(),
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VectorDocument':
        """Create instance from dictionary."""
        return cls(
            document_id=data['document_id'],
            content_id=data['content_id'],
            chunk_index=data['chunk_index'],
            text=data['text'],
            vector_embedding=data['vector_embedding'],
            certification_type=CertificationType(data['certification_type']),
            certification_level=data.get('certification_level', ''),
            content_type=ContentType(data.get('content_type', 'study_guide')),
            category=data.get('category', ''),
            subcategory=data.get('subcategory'),
            difficulty_level=DifficultyLevel(data.get('difficulty_level', 'intermediate')),
            tags=data.get('tags', []),
            source_file=data.get('source_file', ''),
            source_bucket=data.get('source_bucket', ''),
            chunk_size=data.get('chunk_size', 0),
            processed_at=datetime.fromisoformat(data.get('processed_at', datetime.utcnow().isoformat())),
            metadata=data.get('metadata', {})
        )


# Certification detection utilities
def detect_certification_from_filename(filename: str, admin_override: Optional[str] = None) -> CertificationType:
    """
    Detect certification type from filename using 3-letter codes or admin override.
    
    Expected format: {CODE}-{number}.{extension}
    Examples: SAA-1.pdf, CCP-study-guide.pdf, DVA-2.docx
    
    Args:
        filename: The filename or S3 key
        admin_override: Optional admin-selected certification code (takes precedence)
        
    Returns:
        CertificationType enum value (defaults to GENERAL if no match)
    """
    # Admin override takes precedence
    if admin_override:
        admin_override = admin_override.upper().strip()
        for cert_type in CertificationType:
            if cert_type.value == admin_override:
                return cert_type
        # If admin_override doesn't match any valid certification, log warning but continue
        print(f"Warning: Admin override '{admin_override}' is not a valid certification type")
    
    # Extract just the filename from path
    base_filename = filename.split('/')[-1].upper()
    
    # Try to find certification code at the beginning (preferred format)
    for cert_type in CertificationType:
        if cert_type == CertificationType.GENERAL:
            continue
        if base_filename.startswith(f"{cert_type.value}-"):
            return cert_type
    
    # Fallback: check if code appears anywhere in filename
    for cert_type in CertificationType:
        if cert_type == CertificationType.GENERAL:
            continue
        if cert_type.value in base_filename:
            return cert_type
    
    # Default to GENERAL if no certification code found
    return CertificationType.GENERAL


def get_certification_display_name(cert_type: CertificationType) -> str:
    """
    Get the full display name for a certification type.
    
    Args:
        cert_type: CertificationType enum value
        
    Returns:
        Full certification name
    """
    display_names = {
        CertificationType.CCP: "AWS Certified Cloud Practitioner",
        CertificationType.AIP: "AWS Certified AI Practitioner",
        CertificationType.MLA: "AWS Certified Machine Learning Engineer - Associate",
        CertificationType.DEA: "AWS Certified Data Engineer - Associate",
        CertificationType.DVA: "AWS Certified Developer - Associate",
        CertificationType.SAA: "AWS Certified Solutions Architect - Associate",
        CertificationType.SOA: "AWS Certified SysOps Administrator - Associate",
        CertificationType.DOP: "AWS Certified DevOps Engineer - Professional",
        CertificationType.SAP: "AWS Certified Solutions Architect - Professional",
        CertificationType.ANS: "AWS Certified Advanced Networking - Specialty",
        CertificationType.MLS: "AWS Certified Machine Learning - Specialty",
        CertificationType.SCS: "AWS Certified Security - Specialty",
        CertificationType.GENERAL: "General Content"
    }
    return display_names.get(cert_type, "Unknown Certification")


def get_certification_level(cert_type: CertificationType) -> str:
    """
    Get the certification level (foundational, associate, professional, specialty).
    
    Args:
        cert_type: CertificationType enum value
        
    Returns:
        Certification level in lowercase for consistency
    """
    foundational = [CertificationType.CCP, CertificationType.AIP]
    associate = [CertificationType.MLA, CertificationType.DEA, CertificationType.DVA, 
                CertificationType.SAA, CertificationType.SOA]
    professional = [CertificationType.DOP, CertificationType.SAP]
    specialty = [CertificationType.ANS, CertificationType.MLS, CertificationType.SCS]
    
    if cert_type in foundational:
        return "foundational"
    elif cert_type in associate:
        return "associate"
    elif cert_type in professional:
        return "professional"
    elif cert_type in specialty:
        return "specialty"
    else:
        return "general"


def get_certifications_for_dropdown() -> List[Dict[str, str]]:
    """
    Get all certifications formatted for admin dropdown interface.
    
    Returns:
        List of dictionaries with code, name, and level for each certification
    """
    certifications = []
    
    for cert_type in CertificationType:
        certifications.append({
            "code": cert_type.value,
            "name": get_certification_display_name(cert_type),
            "level": get_certification_level(cert_type),
            "sort_order": _get_sort_order(cert_type)
        })
    
    # Sort by level and then by name
    certifications.sort(key=lambda x: (x["sort_order"], x["name"]))
    return certifications


def _get_sort_order(cert_type: CertificationType) -> int:
    """Helper function to determine sort order for certifications."""
    level_order = {
        "General": 0,
        "Foundational": 1,
        "Associate": 2,
        "Professional": 3,
        "Specialty": 4
    }
    return level_order.get(get_certification_level(cert_type), 5)


def validate_certification_code(code: str) -> bool:
    """
    Validate if a certification code is valid.
    
    Args:
        code: Certification code to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not code:
        return False
    
    code = code.upper().strip()
    return any(cert_type.value == code for cert_type in CertificationType)


# Validation helper functions
def validate_model(model: Union[ContentMetadata, QuestionAnswer, UserProgress, VectorDocument]) -> bool:
    """
    Validate any model instance.
    
    Args:
        model: Instance of any data model
        
    Returns:
        True if valid, False otherwise
        
    Raises:
        ValueError: If validation fails with details
    """
    errors = model.validate()
    if errors:
        raise ValueError(f"Validation failed: {'; '.join(errors)}")
    return True


def validate_models(models: List[Union[ContentMetadata, QuestionAnswer, UserProgress, VectorDocument]]) -> bool:
    """
    Validate a list of model instances.
    
    Args:
        models: List of model instances
        
    Returns:
        True if all valid, False otherwise
        
    Raises:
        ValueError: If any validation fails with details
    """
    for i, model in enumerate(models):
        try:
            validate_model(model)
        except ValueError as e:
            raise ValueError(f"Model at index {i} failed validation: {str(e)}")
    return True