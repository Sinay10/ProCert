"""
Service interfaces for the ProCert content management system.

This module defines the abstract interfaces for all services in the system,
providing clear contracts for implementation and enabling dependency injection.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

from .models import (
    ContentMetadata, QuestionAnswer, UserProgress, VectorDocument,
    ContentType, CertificationType, DifficultyLevel, ProgressType,
    Achievement, PerformanceTrend, CertificationReadiness
)


# Result classes for service operations
class ProcessingResult:
    """Result of content processing operations."""
    
    def __init__(self, success: bool, message: str = "", data: Any = None, errors: List[str] = None):
        self.success = success
        self.message = message
        self.data = data
        self.errors = errors or []


class ValidationResult:
    """Result of content validation operations."""
    
    def __init__(self, is_valid: bool, errors: List[str] = None, warnings: List[str] = None):
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []


class SearchResult:
    """Result of search operations."""
    
    def __init__(self, content_id: str, title: str, text: str, score: float, metadata: Dict[str, Any] = None):
        self.content_id = content_id
        self.title = title
        self.text = text
        self.score = score
        self.metadata = metadata or {}


class ContentClassification:
    """Result of content classification operations."""
    
    def __init__(self, content_type: ContentType, category: str, subcategory: Optional[str] = None,
                 difficulty: DifficultyLevel = DifficultyLevel.INTERMEDIATE, tags: List[str] = None):
        self.content_type = content_type
        self.category = category
        self.subcategory = subcategory
        self.difficulty = difficulty
        self.tags = tags or []


class ContentChunk:
    """Represents a chunk of processed content."""
    
    def __init__(self, text: str, index: int, metadata: Dict[str, Any] = None):
        self.text = text
        self.index = index
        self.metadata = metadata or {}


class PerformanceMetrics:
    """User performance analytics data."""
    
    def __init__(self, user_id: str, total_content_viewed: int, total_questions_answered: int,
                 average_score: float, time_spent_total: int, completion_rate: float):
        self.user_id = user_id
        self.total_content_viewed = total_content_viewed
        self.total_questions_answered = total_questions_answered
        self.average_score = average_score
        self.time_spent_total = time_spent_total
        self.completion_rate = completion_rate


class InteractionData:
    """Data for user interactions with content."""
    
    def __init__(self, interaction_type: str, score: Optional[float] = None, 
                 time_spent: int = 0, additional_data: Dict[str, Any] = None):
        self.interaction_type = interaction_type
        self.score = score
        self.time_spent = time_spent
        self.additional_data = additional_data or {}


# Service Interfaces

class IContentIngestionService(ABC):
    """Interface for content ingestion and initial processing."""
    
    @abstractmethod
    def process_upload(self, bucket: str, key: str) -> ProcessingResult:
        """
        Process an uploaded file from S3.
        
        Args:
            bucket: S3 bucket name
            key: S3 object key
            
        Returns:
            ProcessingResult with success status and details
        """
        pass
    
    @abstractmethod
    def validate_content(self, content: bytes, content_type: str) -> ValidationResult:
        """
        Validate uploaded content format and structure.
        
        Args:
            content: Raw content bytes
            content_type: MIME type or file extension
            
        Returns:
            ValidationResult with validation status and errors
        """
        pass
    
    @abstractmethod
    def extract_metadata(self, content: bytes, file_format: str, source_info: Dict[str, Any]) -> ContentMetadata:
        """
        Extract metadata from content.
        
        Args:
            content: Raw content bytes
            file_format: File format (pdf, txt, etc.)
            source_info: Source file information (bucket, key, etc.)
            
        Returns:
            ContentMetadata instance
        """
        pass


class IContentProcessor(ABC):
    """Interface for content processing and transformation."""
    
    @abstractmethod
    def extract_questions_answers(self, text: str, certification_type: CertificationType) -> List[QuestionAnswer]:
        """
        Extract questions and answers from text content.
        
        Args:
            text: Raw text content
            certification_type: Type of certification for context
            
        Returns:
            List of QuestionAnswer instances
        """
        pass
    
    @abstractmethod
    def classify_content(self, text: str, source_metadata: Dict[str, Any]) -> ContentClassification:
        """
        Classify content by type, category, and difficulty.
        
        Args:
            text: Content text
            source_metadata: Additional metadata for classification
            
        Returns:
            ContentClassification result
        """
        pass
    
    @abstractmethod
    def chunk_content(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[ContentChunk]:
        """
        Split content into chunks for processing.
        
        Args:
            text: Content to chunk
            chunk_size: Maximum chunk size
            overlap: Overlap between chunks
            
        Returns:
            List of ContentChunk instances
        """
        pass
    
    @abstractmethod
    def generate_embeddings(self, chunks: List[str]) -> List[List[float]]:
        """
        Generate vector embeddings for text chunks.
        
        Args:
            chunks: List of text chunks
            
        Returns:
            List of embedding vectors
        """
        pass
    
    @abstractmethod
    def detect_certification_type(self, text: str, source_path: str) -> CertificationType:
        """
        Detect certification type from content and source.
        
        Args:
            text: Content text
            source_path: Source file path or bucket
            
        Returns:
            Detected CertificationType
        """
        pass


class IStorageManager(ABC):
    """Interface for managing data persistence across storage systems."""
    
    @abstractmethod
    def store_content_metadata(self, metadata: ContentMetadata) -> str:
        """
        Store content metadata in DynamoDB.
        
        Args:
            metadata: ContentMetadata to store
            
        Returns:
            Stored content ID
        """
        pass
    
    @abstractmethod
    def store_vector_embeddings(self, embeddings: List[VectorDocument]) -> bool:
        """
        Store vector embeddings in OpenSearch.
        
        Args:
            embeddings: List of VectorDocument instances
            
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    def store_user_progress(self, user_id: str, progress: UserProgress) -> bool:
        """
        Store user progress data.
        
        Args:
            user_id: User identifier
            progress: UserProgress data
            
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    def retrieve_content_by_id(self, content_id: str) -> Optional[ContentMetadata]:
        """
        Retrieve content metadata by ID.
        
        Args:
            content_id: Content identifier
            
        Returns:
            ContentMetadata if found, None otherwise
        """
        pass
    
    @abstractmethod
    def retrieve_content_by_certification(self, certification_type: CertificationType, 
                                        limit: int = 50) -> List[ContentMetadata]:
        """
        Retrieve content by certification type.
        
        Args:
            certification_type: Type of certification
            limit: Maximum number of results
            
        Returns:
            List of ContentMetadata instances
        """
        pass
    
    @abstractmethod
    def update_content_metadata(self, content_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update content metadata.
        
        Args:
            content_id: Content identifier
            updates: Fields to update
            
        Returns:
            True if successful
        """
        pass


class ISearchService(ABC):
    """Interface for content search and retrieval."""
    
    @abstractmethod
    def semantic_search(self, query: str, certification_type: Optional[CertificationType] = None,
                       filters: Dict[str, Any] = None, limit: int = 10) -> List[SearchResult]:
        """
        Perform semantic search using vector embeddings.
        
        Args:
            query: Search query
            certification_type: Filter by certification type
            filters: Additional filters
            limit: Maximum results
            
        Returns:
            List of SearchResult instances
        """
        pass
    
    @abstractmethod
    def get_related_content(self, content_id: str, limit: int = 5) -> List[ContentMetadata]:
        """
        Get content related to a specific item.
        
        Args:
            content_id: Reference content ID
            limit: Maximum results
            
        Returns:
            List of related ContentMetadata
        """
        pass
    
    @abstractmethod
    def search_by_category(self, category: str, certification_type: Optional[CertificationType] = None,
                          limit: int = 20) -> List[ContentMetadata]:
        """
        Search content by category.
        
        Args:
            category: Content category
            certification_type: Filter by certification type
            limit: Maximum results
            
        Returns:
            List of ContentMetadata instances
        """
        pass
    
    @abstractmethod
    def get_user_recommended_content(self, user_id: str, limit: int = 10) -> List[ContentMetadata]:
        """
        Get personalized content recommendations.
        
        Args:
            user_id: User identifier
            limit: Maximum results
            
        Returns:
            List of recommended ContentMetadata
        """
        pass


class IProgressTracker(ABC):
    """Interface for tracking user progress and interactions."""
    
    @abstractmethod
    def record_interaction(self, user_id: str, content_id: str, interaction: InteractionData) -> bool:
        """
        Record a user interaction with content.
        
        Args:
            user_id: User identifier
            content_id: Content identifier
            interaction: Interaction data
            
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    def get_user_progress(self, user_id: str, certification_type: Optional[CertificationType] = None) -> List[UserProgress]:
        """
        Get user progress data.
        
        Args:
            user_id: User identifier
            certification_type: Filter by certification type
            
        Returns:
            List of UserProgress instances
        """
        pass
    
    @abstractmethod
    def calculate_completion_rate(self, user_id: str, category: str, 
                                certification_type: Optional[CertificationType] = None) -> float:
        """
        Calculate completion rate for a category.
        
        Args:
            user_id: User identifier
            category: Content category
            certification_type: Filter by certification type
            
        Returns:
            Completion rate as percentage (0-100)
        """
        pass
    
    @abstractmethod
    def get_performance_analytics(self, user_id: str, 
                                certification_type: Optional[CertificationType] = None) -> PerformanceMetrics:
        """
        Get comprehensive performance analytics.
        
        Args:
            user_id: User identifier
            certification_type: Filter by certification type
            
        Returns:
            PerformanceMetrics instance
        """
        pass
    
    @abstractmethod
    def get_user_activity_summary(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Get user activity summary for specified period.
        
        Args:
            user_id: User identifier
            days: Number of days to include
            
        Returns:
            Dictionary with activity summary data
        """
        pass
    
    @abstractmethod
    def get_performance_trends(self, user_id: str, certification_type: Optional[CertificationType] = None, 
                             days: int = 30) -> List['PerformanceTrend']:
        """
        Get performance trends over time with detailed breakdowns.
        
        Args:
            user_id: User identifier
            certification_type: Filter by certification type
            days: Number of days to include
            
        Returns:
            List of PerformanceTrend instances
        """
        pass
    
    @abstractmethod
    def calculate_certification_readiness(self, user_id: str, certification_type: CertificationType) -> 'CertificationReadiness':
        """
        Calculate certification readiness assessment with estimated study time.
        
        Args:
            user_id: User identifier
            certification_type: Target certification type
            
        Returns:
            CertificationReadiness instance
        """
        pass
    
    @abstractmethod
    def check_achievements(self, user_id: str) -> List['Achievement']:
        """
        Check for new achievements and milestones based on user progress.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of newly earned Achievement instances
        """
        pass
    
    @abstractmethod
    def get_user_achievements(self, user_id: str, certification_type: Optional[CertificationType] = None) -> List['Achievement']:
        """
        Get all achievements earned by a user.
        
        Args:
            user_id: User identifier
            certification_type: Filter by certification type
            
        Returns:
            List of Achievement instances
        """
        pass
    
    @abstractmethod
    def get_dashboard_data(self, user_id: str) -> Dict[str, Any]:
        """
        Get comprehensive dashboard data aggregation for progress visualization.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary with dashboard data including progress, trends, achievements
        """
        pass


# Factory interface for dependency injection
class IServiceFactory(ABC):
    """Interface for service factory to enable dependency injection."""
    
    @abstractmethod
    def create_content_ingestion_service(self) -> IContentIngestionService:
        """Create content ingestion service instance."""
        pass
    
    @abstractmethod
    def create_content_processor(self) -> IContentProcessor:
        """Create content processor instance."""
        pass
    
    @abstractmethod
    def create_storage_manager(self) -> IStorageManager:
        """Create storage manager instance."""
        pass
    
    @abstractmethod
    def create_search_service(self) -> ISearchService:
        """Create search service instance."""
        pass
    
    @abstractmethod
    def create_progress_tracker(self) -> IProgressTracker:
        """Create progress tracker instance."""
        pass


# Configuration interface
class IConfiguration(ABC):
    """Interface for system configuration management."""
    
    @abstractmethod
    def get_opensearch_config(self) -> Dict[str, Any]:
        """Get OpenSearch configuration."""
        pass
    
    @abstractmethod
    def get_dynamodb_config(self) -> Dict[str, Any]:
        """Get DynamoDB configuration."""
        pass
    
    @abstractmethod
    def get_s3_config(self) -> Dict[str, Any]:
        """Get S3 configuration."""
        pass
    
    @abstractmethod
    def get_bedrock_config(self) -> Dict[str, Any]:
        """Get Bedrock configuration."""
        pass
    
    @abstractmethod
    def get_processing_config(self) -> Dict[str, Any]:
        """Get content processing configuration."""
        pass