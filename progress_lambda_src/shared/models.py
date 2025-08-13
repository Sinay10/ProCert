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


@dataclass
class ConversationMessage:
    """
    Model for individual messages in a conversation.
    """
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    sources: List[str] = field(default_factory=list)
    mode_used: Optional[str] = None  # 'rag' or 'enhanced'
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> List[str]:
        """Validate the conversation message."""
        errors = []
        
        if not self.role or self.role not in ['user', 'assistant']:
            errors.append("role must be 'user' or 'assistant'")
        
        if not self.content or not self.content.strip():
            errors.append("content is required and cannot be empty")
        
        if self.mode_used and self.mode_used not in ['rag', 'enhanced']:
            errors.append("mode_used must be 'rag' or 'enhanced' if specified")
        
        return errors

    def is_valid(self) -> bool:
        """Check if the conversation message is valid."""
        return len(self.validate()) == 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'role': self.role,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'sources': self.sources,
            'mode_used': self.mode_used,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationMessage':
        """Create instance from dictionary."""
        return cls(
            role=data['role'],
            content=data['content'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            sources=data.get('sources', []),
            mode_used=data.get('mode_used'),
            metadata=data.get('metadata', {})
        )


@dataclass
class ConversationContext:
    """
    Model for conversation context and message history.
    """
    conversation_id: str
    user_id: str
    messages: List[ConversationMessage] = field(default_factory=list)
    certification_context: Optional[str] = None
    preferred_mode: str = "rag"  # 'rag' or 'enhanced'
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    ttl: int = field(default_factory=lambda: int((datetime.utcnow().timestamp() + 86400 * 7)))  # 7 days TTL
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> List[str]:
        """Validate the conversation context."""
        errors = []
        
        if not self.conversation_id or not self.conversation_id.strip():
            errors.append("conversation_id is required and cannot be empty")
        
        if not self.user_id or not self.user_id.strip():
            errors.append("user_id is required and cannot be empty")
        
        if self.preferred_mode not in ['rag', 'enhanced']:
            errors.append("preferred_mode must be 'rag' or 'enhanced'")
        
        # Validate all messages
        for i, message in enumerate(self.messages):
            message_errors = message.validate()
            if message_errors:
                errors.extend([f"Message {i}: {error}" for error in message_errors])
        
        return errors

    def is_valid(self) -> bool:
        """Check if the conversation context is valid."""
        return len(self.validate()) == 0

    def add_message(self, message: ConversationMessage) -> None:
        """Add a message to the conversation."""
        self.messages.append(message)
        self.updated_at = datetime.utcnow()

    def get_recent_context(self, max_messages: int = 10) -> List[ConversationMessage]:
        """Get recent messages for context."""
        return self.messages[-max_messages:] if len(self.messages) > max_messages else self.messages

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'conversation_id': self.conversation_id,
            'user_id': self.user_id,
            'messages': [msg.to_dict() for msg in self.messages],
            'certification_context': self.certification_context,
            'preferred_mode': self.preferred_mode,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'ttl': self.ttl,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationContext':
        """Create instance from dictionary."""
        messages = [ConversationMessage.from_dict(msg_data) for msg_data in data.get('messages', [])]
        return cls(
            conversation_id=data['conversation_id'],
            user_id=data['user_id'],
            messages=messages,
            certification_context=data.get('certification_context'),
            preferred_mode=data.get('preferred_mode', 'rag'),
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            ttl=data.get('ttl', int((datetime.utcnow().timestamp() + 86400 * 7))),
            metadata=data.get('metadata', {})
        )


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
def validate_model(model: Union[ContentMetadata, QuestionAnswer, UserProgress, VectorDocument, 'UserProfile', 'QuizSession', 'StudyRecommendation']) -> bool:
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


@dataclass
class Achievement:
    """
    Model for user achievements and milestones.
    """
    achievement_id: str
    user_id: str
    achievement_type: str  # 'streak', 'score', 'completion', 'time', 'milestone'
    title: str
    description: str
    criteria: Dict[str, Any]  # Achievement criteria (e.g., {'streak_days': 7, 'certification': 'SAA'})
    earned_at: datetime = field(default_factory=datetime.utcnow)
    certification_type: Optional[CertificationType] = None
    badge_icon: str = ""
    points: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> List[str]:
        """Validate achievement data."""
        errors = []
        
        if not self.achievement_id or not self.achievement_id.strip():
            errors.append("achievement_id is required and cannot be empty")
        
        if not self.user_id or not self.user_id.strip():
            errors.append("user_id is required and cannot be empty")
        
        if not self.achievement_type or self.achievement_type not in ['streak', 'score', 'completion', 'time', 'milestone']:
            errors.append("achievement_type must be one of: streak, score, completion, time, milestone")
        
        if not self.title or not self.title.strip():
            errors.append("title is required and cannot be empty")
        
        if not self.description or not self.description.strip():
            errors.append("description is required and cannot be empty")
        
        if self.points < 0:
            errors.append("points cannot be negative")
        
        return errors

    def is_valid(self) -> bool:
        """Check if achievement is valid."""
        return len(self.validate()) == 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'achievement_id': self.achievement_id,
            'user_id': self.user_id,
            'achievement_type': self.achievement_type,
            'title': self.title,
            'description': self.description,
            'criteria': self.criteria,
            'earned_at': self.earned_at.isoformat(),
            'certification_type': self.certification_type.value if self.certification_type else None,
            'badge_icon': self.badge_icon,
            'points': self.points,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Achievement':
        """Create instance from dictionary."""
        return cls(
            achievement_id=data['achievement_id'],
            user_id=data['user_id'],
            achievement_type=data['achievement_type'],
            title=data['title'],
            description=data['description'],
            criteria=data.get('criteria', {}),
            earned_at=datetime.fromisoformat(data['earned_at']),
            certification_type=CertificationType(data['certification_type']) if data.get('certification_type') else None,
            badge_icon=data.get('badge_icon', ''),
            points=data.get('points', 0),
            metadata=data.get('metadata', {})
        )


@dataclass
class PerformanceTrend:
    """
    Model for performance trend data over time.
    """
    user_id: str
    certification_type: CertificationType
    date: datetime
    metrics: Dict[str, float]  # e.g., {'avg_score': 85.5, 'completion_rate': 60.0, 'time_spent': 120}
    category_breakdown: Dict[str, Dict[str, float]] = field(default_factory=dict)
    difficulty_breakdown: Dict[str, Dict[str, float]] = field(default_factory=dict)

    def validate(self) -> List[str]:
        """Validate performance trend data."""
        errors = []
        
        if not self.user_id or not self.user_id.strip():
            errors.append("user_id is required and cannot be empty")
        
        if not self.metrics:
            errors.append("metrics cannot be empty")
        
        return errors

    def is_valid(self) -> bool:
        """Check if performance trend is valid."""
        return len(self.validate()) == 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'user_id': self.user_id,
            'certification_type': self.certification_type.value,
            'date': self.date.isoformat(),
            'metrics': self.metrics,
            'category_breakdown': self.category_breakdown,
            'difficulty_breakdown': self.difficulty_breakdown
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PerformanceTrend':
        """Create instance from dictionary."""
        return cls(
            user_id=data['user_id'],
            certification_type=CertificationType(data['certification_type']),
            date=datetime.fromisoformat(data['date']),
            metrics=data.get('metrics', {}),
            category_breakdown=data.get('category_breakdown', {}),
            difficulty_breakdown=data.get('difficulty_breakdown', {})
        )


@dataclass
class CertificationReadiness:
    """
    Model for certification readiness assessment.
    """
    user_id: str
    certification_type: CertificationType
    readiness_score: float  # 0-100 percentage
    estimated_study_time_hours: int
    weak_areas: List[str]
    strong_areas: List[str]
    recommended_actions: List[str]
    assessment_date: datetime = field(default_factory=datetime.utcnow)
    confidence_level: str = "low"  # low, medium, high
    predicted_pass_probability: float = 0.0  # 0-100 percentage

    def validate(self) -> List[str]:
        """Validate certification readiness data."""
        errors = []
        
        if not self.user_id or not self.user_id.strip():
            errors.append("user_id is required and cannot be empty")
        
        if self.readiness_score < 0 or self.readiness_score > 100:
            errors.append("readiness_score must be between 0 and 100")
        
        if self.estimated_study_time_hours < 0:
            errors.append("estimated_study_time_hours cannot be negative")
        
        if self.confidence_level not in ["low", "medium", "high"]:
            errors.append("confidence_level must be 'low', 'medium', or 'high'")
        
        if self.predicted_pass_probability < 0 or self.predicted_pass_probability > 100:
            errors.append("predicted_pass_probability must be between 0 and 100")
        
        return errors

    def is_valid(self) -> bool:
        """Check if certification readiness is valid."""
        return len(self.validate()) == 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'user_id': self.user_id,
            'certification_type': self.certification_type.value,
            'readiness_score': self.readiness_score,
            'estimated_study_time_hours': self.estimated_study_time_hours,
            'weak_areas': self.weak_areas,
            'strong_areas': self.strong_areas,
            'recommended_actions': self.recommended_actions,
            'assessment_date': self.assessment_date.isoformat(),
            'confidence_level': self.confidence_level,
            'predicted_pass_probability': self.predicted_pass_probability
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CertificationReadiness':
        """Create instance from dictionary."""
        return cls(
            user_id=data['user_id'],
            certification_type=CertificationType(data['certification_type']),
            readiness_score=data.get('readiness_score', 0.0),
            estimated_study_time_hours=data.get('estimated_study_time_hours', 0),
            weak_areas=data.get('weak_areas', []),
            strong_areas=data.get('strong_areas', []),
            recommended_actions=data.get('recommended_actions', []),
            assessment_date=datetime.fromisoformat(data.get('assessment_date', datetime.utcnow().isoformat())),
            confidence_level=data.get('confidence_level', 'low'),
            predicted_pass_probability=data.get('predicted_pass_probability', 0.0)
        )


@dataclass
class StudyPreferences:
    """
    Model for user study preferences.
    """
    daily_goal_minutes: int = 30
    preferred_difficulty: str = "intermediate"
    notification_settings: Dict[str, bool] = field(default_factory=lambda: {
        "email_reminders": True,
        "achievement_notifications": True,
        "study_recommendations": True
    })
    preferred_study_time: str = "evening"  # morning, afternoon, evening
    quiz_length_preference: int = 10  # default number of questions

    def validate(self) -> List[str]:
        """Validate study preferences."""
        errors = []
        
        if self.daily_goal_minutes < 0 or self.daily_goal_minutes > 480:  # max 8 hours
            errors.append("daily_goal_minutes must be between 0 and 480")
        
        if self.preferred_difficulty not in ["beginner", "intermediate", "advanced"]:
            errors.append("preferred_difficulty must be 'beginner', 'intermediate', or 'advanced'")
        
        if self.preferred_study_time not in ["morning", "afternoon", "evening"]:
            errors.append("preferred_study_time must be 'morning', 'afternoon', or 'evening'")
        
        if self.quiz_length_preference < 5 or self.quiz_length_preference > 50:
            errors.append("quiz_length_preference must be between 5 and 50")
        
        return errors

    def is_valid(self) -> bool:
        """Check if study preferences are valid."""
        return len(self.validate()) == 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'daily_goal_minutes': self.daily_goal_minutes,
            'preferred_difficulty': self.preferred_difficulty,
            'notification_settings': self.notification_settings,
            'preferred_study_time': self.preferred_study_time,
            'quiz_length_preference': self.quiz_length_preference
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StudyPreferences':
        """Create instance from dictionary."""
        return cls(
            daily_goal_minutes=data.get('daily_goal_minutes', 30),
            preferred_difficulty=data.get('preferred_difficulty', 'intermediate'),
            notification_settings=data.get('notification_settings', {
                "email_reminders": True,
                "achievement_notifications": True,
                "study_recommendations": True
            }),
            preferred_study_time=data.get('preferred_study_time', 'evening'),
            quiz_length_preference=data.get('quiz_length_preference', 10)
        )


@dataclass
class UserProfile:
    """
    Model for user profile and account information.
    """
    user_id: str
    email: str
    name: str
    target_certifications: List[str] = field(default_factory=list)
    study_preferences: StudyPreferences = field(default_factory=StudyPreferences)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_active: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True
    subscription_tier: str = "free"  # free, premium
    total_study_time: int = 0  # total minutes studied
    achievements: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> List[str]:
        """Validate user profile."""
        errors = []
        
        if not self.user_id or not self.user_id.strip():
            errors.append("user_id is required and cannot be empty")
        
        if not self.email or not self.email.strip():
            errors.append("email is required and cannot be empty")
        
        # Basic email validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, self.email):
            errors.append("email must be a valid email address")
        
        if not self.name or not self.name.strip():
            errors.append("name is required and cannot be empty")
        
        # Validate target certifications
        for cert in self.target_certifications:
            if not validate_certification_code(cert):
                errors.append(f"invalid certification code: {cert}")
        
        if self.subscription_tier not in ["free", "premium"]:
            errors.append("subscription_tier must be 'free' or 'premium'")
        
        if self.total_study_time < 0:
            errors.append("total_study_time cannot be negative")
        
        # Validate study preferences
        pref_errors = self.study_preferences.validate()
        if pref_errors:
            errors.extend([f"study_preferences: {error}" for error in pref_errors])
        
        return errors

    def is_valid(self) -> bool:
        """Check if user profile is valid."""
        return len(self.validate()) == 0

    def add_certification_target(self, certification: str) -> bool:
        """Add a certification to target list if valid."""
        if validate_certification_code(certification) and certification not in self.target_certifications:
            self.target_certifications.append(certification.upper())
            return True
        return False

    def remove_certification_target(self, certification: str) -> bool:
        """Remove a certification from target list."""
        if certification.upper() in self.target_certifications:
            self.target_certifications.remove(certification.upper())
            return True
        return False

    def add_achievement(self, achievement: str) -> None:
        """Add an achievement if not already present."""
        if achievement not in self.achievements:
            self.achievements.append(achievement)

    def update_last_active(self) -> None:
        """Update the last active timestamp."""
        self.last_active = datetime.utcnow()

    def add_study_time(self, minutes: int) -> None:
        """Add study time to total."""
        if minutes > 0:
            self.total_study_time += minutes

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'user_id': self.user_id,
            'email': self.email,
            'name': self.name,
            'target_certifications': self.target_certifications,
            'study_preferences': self.study_preferences.to_dict(),
            'created_at': self.created_at.isoformat(),
            'last_active': self.last_active.isoformat(),
            'is_active': self.is_active,
            'subscription_tier': self.subscription_tier,
            'total_study_time': self.total_study_time,
            'achievements': self.achievements,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserProfile':
        """Create instance from dictionary."""
        study_prefs_data = data.get('study_preferences', {})
        study_preferences = StudyPreferences.from_dict(study_prefs_data)
        
        return cls(
            user_id=data['user_id'],
            email=data['email'],
            name=data['name'],
            target_certifications=data.get('target_certifications', []),
            study_preferences=study_preferences,
            created_at=datetime.fromisoformat(data.get('created_at', datetime.utcnow().isoformat())),
            last_active=datetime.fromisoformat(data.get('last_active', datetime.utcnow().isoformat())),
            is_active=data.get('is_active', True),
            subscription_tier=data.get('subscription_tier', 'free'),
            total_study_time=data.get('total_study_time', 0),
            achievements=data.get('achievements', []),
            metadata=data.get('metadata', {})
        )


@dataclass
class QuizSession:
    """
    Model for quiz sessions and results.
    """
    quiz_id: str
    user_id: str
    certification: str
    questions: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "in_progress"  # in_progress, completed, abandoned
    score: Optional[float] = None
    total_questions: int = 0
    correct_answers: int = 0
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    time_spent: int = 0  # seconds
    difficulty_level: str = "intermediate"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> List[str]:
        """Validate quiz session."""
        errors = []
        
        if not self.quiz_id or not self.quiz_id.strip():
            errors.append("quiz_id is required and cannot be empty")
        
        if not self.user_id or not self.user_id.strip():
            errors.append("user_id is required and cannot be empty")
        
        if not validate_certification_code(self.certification):
            errors.append(f"invalid certification code: {self.certification}")
        
        if self.status not in ["in_progress", "completed", "abandoned"]:
            errors.append("status must be 'in_progress', 'completed', or 'abandoned'")
        
        if self.score is not None and (self.score < 0 or self.score > 100):
            errors.append("score must be between 0 and 100")
        
        if self.total_questions < 0:
            errors.append("total_questions cannot be negative")
        
        if self.correct_answers < 0 or self.correct_answers > self.total_questions:
            errors.append("correct_answers must be between 0 and total_questions")
        
        if self.time_spent < 0:
            errors.append("time_spent cannot be negative")
        
        if self.difficulty_level not in ["beginner", "intermediate", "advanced"]:
            errors.append("difficulty_level must be 'beginner', 'intermediate', or 'advanced'")
        
        return errors

    def is_valid(self) -> bool:
        """Check if quiz session is valid."""
        return len(self.validate()) == 0

    def complete_quiz(self) -> None:
        """Mark quiz as completed and calculate score."""
        self.status = "completed"
        self.completed_at = datetime.utcnow()
        if self.total_questions > 0:
            self.score = (self.correct_answers / self.total_questions) * 100

    def abandon_quiz(self) -> None:
        """Mark quiz as abandoned."""
        self.status = "abandoned"
        self.completed_at = datetime.utcnow()

    def add_question_result(self, question_data: Dict[str, Any], is_correct: bool) -> None:
        """Add a question result to the session."""
        self.questions.append(question_data)
        self.total_questions += 1
        if is_correct:
            self.correct_answers += 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'quiz_id': self.quiz_id,
            'user_id': self.user_id,
            'certification': self.certification,
            'questions': self.questions,
            'status': self.status,
            'score': self.score,
            'total_questions': self.total_questions,
            'correct_answers': self.correct_answers,
            'started_at': self.started_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'time_spent': self.time_spent,
            'difficulty_level': self.difficulty_level,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QuizSession':
        """Create instance from dictionary."""
        completed_at = None
        if data.get('completed_at'):
            completed_at = datetime.fromisoformat(data['completed_at'])
        
        return cls(
            quiz_id=data['quiz_id'],
            user_id=data['user_id'],
            certification=data['certification'],
            questions=data.get('questions', []),
            status=data.get('status', 'in_progress'),
            score=data.get('score'),
            total_questions=data.get('total_questions', 0),
            correct_answers=data.get('correct_answers', 0),
            started_at=datetime.fromisoformat(data['started_at']),
            completed_at=completed_at,
            time_spent=data.get('time_spent', 0),
            difficulty_level=data.get('difficulty_level', 'intermediate'),
            metadata=data.get('metadata', {})
        )


@dataclass
class StudyRecommendation:
    """
    Model for study recommendations.
    """
    recommendation_id: str
    user_id: str
    type: str  # content, quiz, review
    priority: int = 1  # 1-5, higher is more important
    content_id: Optional[str] = None
    certification: Optional[str] = None
    title: str = ""
    description: str = ""
    reasoning: str = ""
    estimated_time: int = 0  # minutes
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: int = field(default_factory=lambda: int((datetime.utcnow().timestamp() + 86400 * 7)))  # 7 days TTL
    is_completed: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> List[str]:
        """Validate study recommendation."""
        errors = []
        
        if not self.recommendation_id or not self.recommendation_id.strip():
            errors.append("recommendation_id is required and cannot be empty")
        
        if not self.user_id or not self.user_id.strip():
            errors.append("user_id is required and cannot be empty")
        
        if self.type not in ["content", "quiz", "review"]:
            errors.append("type must be 'content', 'quiz', or 'review'")
        
        if self.priority < 1 or self.priority > 5:
            errors.append("priority must be between 1 and 5")
        
        if self.certification and not validate_certification_code(self.certification):
            errors.append(f"invalid certification code: {self.certification}")
        
        if self.estimated_time < 0:
            errors.append("estimated_time cannot be negative")
        
        return errors

    def is_valid(self) -> bool:
        """Check if study recommendation is valid."""
        return len(self.validate()) == 0

    def mark_completed(self) -> None:
        """Mark recommendation as completed."""
        self.is_completed = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'recommendation_id': self.recommendation_id,
            'user_id': self.user_id,
            'type': self.type,
            'priority': self.priority,
            'content_id': self.content_id,
            'certification': self.certification,
            'title': self.title,
            'description': self.description,
            'reasoning': self.reasoning,
            'estimated_time': self.estimated_time,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at,
            'is_completed': self.is_completed,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StudyRecommendation':
        """Create instance from dictionary."""
        return cls(
            recommendation_id=data['recommendation_id'],
            user_id=data['user_id'],
            type=data['type'],
            priority=data.get('priority', 1),
            content_id=data.get('content_id'),
            certification=data.get('certification'),
            title=data.get('title', ''),
            description=data.get('description', ''),
            reasoning=data.get('reasoning', ''),
            estimated_time=data.get('estimated_time', 0),
            created_at=datetime.fromisoformat(data['created_at']),
            expires_at=data.get('expires_at', int((datetime.utcnow().timestamp() + 86400 * 7))),
            is_completed=data.get('is_completed', False),
            metadata=data.get('metadata', {})
        )


def validate_models(models: List[Union[ContentMetadata, QuestionAnswer, UserProgress, VectorDocument, 'UserProfile', 'QuizSession', 'StudyRecommendation']]) -> bool:
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

@dataclass
class QuizSession:
    """
    Model for quiz sessions and their state.
    """
    quiz_id: str
    user_id: str
    certification_type: str
    questions: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "in_progress"  # in_progress, completed, abandoned
    score: Optional[float] = None
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    time_limit_minutes: int = 30
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> List[str]:
        """Validate the quiz session."""
        errors = []
        
        if not self.quiz_id or not self.quiz_id.strip():
            errors.append("quiz_id is required and cannot be empty")
        
        if not self.user_id or not self.user_id.strip():
            errors.append("user_id is required and cannot be empty")
        
        if not self.certification_type or not self.certification_type.strip():
            errors.append("certification_type is required and cannot be empty")
        
        if self.status not in ["in_progress", "completed", "abandoned"]:
            errors.append("status must be 'in_progress', 'completed', or 'abandoned'")
        
        if self.score is not None and (self.score < 0 or self.score > 100):
            errors.append("score must be between 0 and 100")
        
        if self.time_limit_minutes < 1:
            errors.append("time_limit_minutes must be positive")
        
        return errors

    def is_valid(self) -> bool:
        """Check if the quiz session is valid."""
        return len(self.validate()) == 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'quiz_id': self.quiz_id,
            'user_id': self.user_id,
            'certification_type': self.certification_type,
            'questions': self.questions,
            'status': self.status,
            'score': self.score,
            'started_at': self.started_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'time_limit_minutes': self.time_limit_minutes,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QuizSession':
        """Create instance from dictionary."""
        return cls(
            quiz_id=data['quiz_id'],
            user_id=data['user_id'],
            certification_type=data['certification_type'],
            questions=data.get('questions', []),
            status=data.get('status', 'in_progress'),
            score=data.get('score'),
            started_at=datetime.fromisoformat(data['started_at']),
            completed_at=datetime.fromisoformat(data['completed_at']) if data.get('completed_at') else None,
            time_limit_minutes=data.get('time_limit_minutes', 30),
            metadata=data.get('metadata', {})
        )


@dataclass
class QuizResult:
    """
    Model for quiz results and scoring.
    """
    quiz_id: str
    user_id: str
    score: float
    correct_answers: int
    total_questions: int
    percentage: float
    results: List[Dict[str, Any]] = field(default_factory=list)
    completed_at: datetime = field(default_factory=datetime.utcnow)
    time_taken_minutes: Optional[int] = None
    performance_summary: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> List[str]:
        """Validate the quiz result."""
        errors = []
        
        if not self.quiz_id or not self.quiz_id.strip():
            errors.append("quiz_id is required and cannot be empty")
        
        if not self.user_id or not self.user_id.strip():
            errors.append("user_id is required and cannot be empty")
        
        if self.score < 0 or self.score > 100:
            errors.append("score must be between 0 and 100")
        
        if self.correct_answers < 0:
            errors.append("correct_answers cannot be negative")
        
        if self.total_questions < 1:
            errors.append("total_questions must be positive")
        
        if self.correct_answers > self.total_questions:
            errors.append("correct_answers cannot exceed total_questions")
        
        if self.percentage < 0 or self.percentage > 100:
            errors.append("percentage must be between 0 and 100")
        
        return errors

    def is_valid(self) -> bool:
        """Check if the quiz result is valid."""
        return len(self.validate()) == 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'quiz_id': self.quiz_id,
            'user_id': self.user_id,
            'score': self.score,
            'correct_answers': self.correct_answers,
            'total_questions': self.total_questions,
            'percentage': self.percentage,
            'results': self.results,
            'completed_at': self.completed_at.isoformat(),
            'time_taken_minutes': self.time_taken_minutes,
            'performance_summary': self.performance_summary
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QuizResult':
        """Create instance from dictionary."""
        return cls(
            quiz_id=data['quiz_id'],
            user_id=data['user_id'],
            score=data['score'],
            correct_answers=data['correct_answers'],
            total_questions=data['total_questions'],
            percentage=data['percentage'],
            results=data.get('results', []),
            completed_at=datetime.fromisoformat(data['completed_at']),
            time_taken_minutes=data.get('time_taken_minutes'),
            performance_summary=data.get('performance_summary', {})
        )


@dataclass
class StudyRecommendation:
    """
    Model for personalized study recommendations.
    """
    recommendation_id: str
    user_id: str
    type: str  # 'content', 'quiz', 'review', 'practice'
    priority: int  # 1-10, higher is more important
    content_id: Optional[str] = None
    certification_type: Optional[str] = None
    category: Optional[str] = None
    reasoning: str = ""
    estimated_time_minutes: int = 30
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    is_completed: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> List[str]:
        """Validate the study recommendation."""
        errors = []
        
        if not self.recommendation_id or not self.recommendation_id.strip():
            errors.append("recommendation_id is required and cannot be empty")
        
        if not self.user_id or not self.user_id.strip():
            errors.append("user_id is required and cannot be empty")
        
        if self.type not in ['content', 'quiz', 'review', 'practice']:
            errors.append("type must be 'content', 'quiz', 'review', or 'practice'")
        
        if self.priority < 1 or self.priority > 10:
            errors.append("priority must be between 1 and 10")
        
        if self.estimated_time_minutes < 1:
            errors.append("estimated_time_minutes must be positive")
        
        return errors

    def is_valid(self) -> bool:
        """Check if the study recommendation is valid."""
        return len(self.validate()) == 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'recommendation_id': self.recommendation_id,
            'user_id': self.user_id,
            'type': self.type,
            'priority': self.priority,
            'content_id': self.content_id,
            'certification_type': self.certification_type,
            'category': self.category,
            'reasoning': self.reasoning,
            'estimated_time_minutes': self.estimated_time_minutes,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_completed': self.is_completed,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StudyRecommendation':
        """Create instance from dictionary."""
        return cls(
            recommendation_id=data['recommendation_id'],
            user_id=data['user_id'],
            type=data['type'],
            priority=data['priority'],
            content_id=data.get('content_id'),
            certification_type=data.get('certification_type'),
            category=data.get('category'),
            reasoning=data.get('reasoning', ''),
            estimated_time_minutes=data.get('estimated_time_minutes', 30),
            created_at=datetime.fromisoformat(data['created_at']),
            expires_at=datetime.fromisoformat(data['expires_at']) if data.get('expires_at') else None,
            is_completed=data.get('is_completed', False),
            metadata=data.get('metadata', {})
        )


# Update the validate_model function to include new models
def validate_model(model: Union[ContentMetadata, QuestionAnswer, UserProgress, VectorDocument, 
                               UserProfile, QuizSession, StudyRecommendation, QuizResult]) -> bool:
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