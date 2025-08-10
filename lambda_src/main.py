# lambda_src/main.py

import os
import json
import boto3
import re
import traceback
from urllib.parse import unquote_plus
from pypdf import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from botocore.exceptions import ClientError, BotoCoreError

# Global variables for AWS clients (initialized with error handling)
s3_client = None
bedrock_runtime = None
opensearch_client = None
opensearch_endpoint = None
opensearch_index = None

def initialize_aws_clients():
    """Initialize AWS clients with comprehensive error handling."""
    global s3_client, bedrock_runtime, opensearch_client, opensearch_endpoint, opensearch_index
    
    try:
        # Get required environment variables
        opensearch_endpoint = os.environ.get('OPENSEARCH_ENDPOINT')
        opensearch_index = os.environ.get('OPENSEARCH_INDEX')
        aws_region = os.environ.get('AWS_REGION', 'us-east-1')
        
        if not opensearch_endpoint:
            raise ValueError("OPENSEARCH_ENDPOINT environment variable is required")
        if not opensearch_index:
            raise ValueError("OPENSEARCH_INDEX environment variable is required")
        
        # Initialize S3 client
        try:
            s3_client = boto3.client('s3', region_name=aws_region)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize S3 client: {str(e)}")
        
        # Initialize Bedrock client
        try:
            bedrock_runtime = boto3.client('bedrock-runtime', region_name=aws_region)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Bedrock client: {str(e)}")
        
        # Initialize OpenSearch client
        try:
            host = opensearch_endpoint.replace("https://", "")
            if not host:
                raise ValueError("Invalid OpenSearch endpoint format")
            
            credentials = boto3.Session().get_credentials()
            if not credentials:
                raise RuntimeError("AWS credentials not found")
            
            auth = AWSV4SignerAuth(credentials, aws_region, 'aoss')
            opensearch_client = OpenSearch(
                hosts=[{'host': host, 'port': 443}],
                http_auth=auth,
                use_ssl=True,
                verify_certs=True,
                connection_class=RequestsHttpConnection,
                pool_timeout=30,
                timeout=30,
                max_retries=3,
                retry_on_timeout=True
            )
            
            # Test OpenSearch connectivity
            opensearch_client.info()
            
        except Exception as e:
            raise RuntimeError(f"Failed to initialize OpenSearch client: {str(e)}")
        
        print("AWS clients initialized successfully")
        
    except Exception as e:
        print(f"Critical error initializing AWS clients: {str(e)}")
        raise

# Initialize clients on module load
try:
    initialize_aws_clients()
except Exception as e:
    print(f"Failed to initialize AWS clients on module load: {e}")
    # Don't raise here to allow Lambda to start, but clients will be None

def detect_certification_from_s3_context(bucket: str, key: str) -> str:
    """
    Detect certification type from S3 bucket name, path, and object tags.
    
    Args:
        bucket: S3 bucket name
        key: S3 object key
        
    Returns:
        Certification type code (e.g., 'SAA', 'CCP', 'GENERAL')
    """
    try:
        # First, try to get object tags
        try:
            response = s3_client.get_object_tagging(Bucket=bucket, Key=key)
            tags = {tag['Key']: tag['Value'] for tag in response.get('TagSet', [])}
            
            # Check for certification_type tag
            if 'certification_type' in tags:
                cert_type = tags['certification_type'].upper()
                if _is_valid_certification_code(cert_type):
                    print(f"Certification detected from S3 tag: {cert_type}")
                    return cert_type
        except Exception as e:
            print(f"Could not retrieve S3 tags: {e}")
        
        # Check bucket name for certification-specific patterns
        bucket_lower = bucket.lower()
        cert_patterns = {
            'saa': 'SAA', 'solutions-architect': 'SAA',
            'dva': 'DVA', 'developer': 'DVA',
            'soa': 'SOA', 'sysops': 'SOA',
            'ccp': 'CCP', 'cloud-practitioner': 'CCP',
            'dop': 'DOP', 'devops': 'DOP',
            'sap': 'SAP', 'solutions-architect-pro': 'SAP',
            'mls': 'MLS', 'machine-learning': 'MLS',
            'scs': 'SCS', 'security': 'SCS',
            'ans': 'ANS', 'networking': 'ANS',
            'aip': 'AIP', 'ai-practitioner': 'AIP',
            'mla': 'MLA', 'ml-engineer': 'MLA',
            'dea': 'DEA', 'data-engineer': 'DEA'
        }
        
        for pattern, cert_code in cert_patterns.items():
            if pattern in bucket_lower:
                print(f"Certification detected from bucket name: {cert_code}")
                return cert_code
        
        # Check S3 key path for certification folders
        key_parts = key.lower().split('/')
        for part in key_parts:
            for pattern, cert_code in cert_patterns.items():
                if pattern in part:
                    print(f"Certification detected from S3 path: {cert_code}")
                    return cert_code
        
        # Fallback to filename detection
        return detect_certification_from_filename(key)
        
    except Exception as e:
        print(f"Error in S3 context detection: {e}")
        return detect_certification_from_filename(key)


def detect_certification_from_filename(filename: str) -> str:
    """
    Detect certification type from filename using 3-letter codes.
    
    Args:
        filename: The filename or S3 key
        
    Returns:
        Certification type code (defaults to 'GENERAL' if no match)
    """
    # Extract just the filename from path
    base_filename = filename.split('/')[-1].upper()
    
    # Valid certification codes
    valid_codes = ['CCP', 'AIP', 'MLA', 'DEA', 'DVA', 'SAA', 'SOA', 'DOP', 'SAP', 'ANS', 'MLS', 'SCS']
    
    # Try to find certification code at the beginning (preferred format)
    for code in valid_codes:
        if base_filename.startswith(f"{code}-"):
            return code
    
    # Fallback: check if code appears anywhere in filename
    for code in valid_codes:
        if code in base_filename:
            return code
    
    # Default to GENERAL if no certification code found
    return 'GENERAL'


def detect_certification_from_content(text: str) -> str:
    """
    Detect certification type from document content headers and text.
    
    Args:
        text: Document text content
        
    Returns:
        Certification type code or 'GENERAL'
    """
    if not text:
        return 'GENERAL'
    
    # Convert to uppercase for pattern matching
    text_upper = text.upper()
    
    # Look for explicit certification mentions in headers/titles
    cert_patterns = {
        'SAA': [
            'SOLUTIONS ARCHITECT ASSOCIATE',
            'AWS CERTIFIED SOLUTIONS ARCHITECT',
            'SAA-C03', 'SAA-C02', 'SAA-C01'
        ],
        'DVA': [
            'DEVELOPER ASSOCIATE',
            'AWS CERTIFIED DEVELOPER',
            'DVA-C02', 'DVA-C01'
        ],
        'SOA': [
            'SYSOPS ADMINISTRATOR',
            'AWS CERTIFIED SYSOPS',
            'SOA-C02', 'SOA-C01'
        ],
        'CCP': [
            'CLOUD PRACTITIONER',
            'AWS CERTIFIED CLOUD PRACTITIONER',
            'CLF-C02', 'CLF-C01'
        ],
        'DOP': [
            'DEVOPS ENGINEER PROFESSIONAL',
            'AWS CERTIFIED DEVOPS',
            'DOP-C02', 'DOP-C01'
        ],
        'SAP': [
            'SOLUTIONS ARCHITECT PROFESSIONAL',
            'AWS CERTIFIED SOLUTIONS ARCHITECT PROFESSIONAL',
            'SAP-C02', 'SAP-C01'
        ],
        'MLS': [
            'MACHINE LEARNING SPECIALTY',
            'AWS CERTIFIED MACHINE LEARNING',
            'MLS-C01'
        ],
        'SCS': [
            'SECURITY SPECIALTY',
            'AWS CERTIFIED SECURITY',
            'SCS-C02', 'SCS-C01'
        ],
        'ANS': [
            'ADVANCED NETWORKING SPECIALTY',
            'AWS CERTIFIED ADVANCED NETWORKING',
            'ANS-C01'
        ],
        'AIP': [
            'AI PRACTITIONER',
            'AWS CERTIFIED AI PRACTITIONER',
            'AIF-C01'
        ],
        'MLA': [
            'MACHINE LEARNING ENGINEER ASSOCIATE',
            'AWS CERTIFIED MACHINE LEARNING ENGINEER',
            'MLA-C01'
        ],
        'DEA': [
            'DATA ENGINEER ASSOCIATE',
            'AWS CERTIFIED DATA ENGINEER',
            'DEA-C01'
        ]
    }
    
    # Check first 2000 characters for certification patterns (headers/titles)
    header_text = text_upper[:2000]
    
    for cert_code, patterns in cert_patterns.items():
        for pattern in patterns:
            if pattern in header_text:
                print(f"Certification detected from content: {cert_code} (pattern: {pattern})")
                return cert_code
    
    return 'GENERAL'


def _is_valid_certification_code(code: str) -> bool:
    """Check if a certification code is valid."""
    valid_codes = ['CCP', 'AIP', 'MLA', 'DEA', 'DVA', 'SAA', 'SOA', 'DOP', 'SAP', 'ANS', 'MLS', 'SCS', 'GENERAL']
    return code.upper() in valid_codes


def extract_questions_and_answers(text: str, certification_type: str) -> List[Dict[str, Any]]:
    """
    Extract questions and answers from content with certification context.
    
    Args:
        text: Document text content
        certification_type: Detected certification type for context
        
    Returns:
        List of question-answer dictionaries
    """
    questions = []
    
    # Common question patterns for AWS certification materials
    question_patterns = [
        # Multiple choice patterns
        r'(?:Question\s*\d+[:\.]?\s*)?(.+?\?)\s*(?:\n|\r\n?)\s*(?:A[:\.\)]\s*(.+?)(?:\n|\r\n?)\s*B[:\.\)]\s*(.+?)(?:\n|\r\n?)\s*C[:\.\)]\s*(.+?)(?:\n|\r\n?)\s*D[:\.\)]\s*(.+?))',
        
        # Numbered question patterns
        r'(\d+\.\s*.+?\?)\s*(?:\n|\r\n?)\s*(?:A[:\.\)]\s*(.+?)(?:\n|\r\n?)\s*B[:\.\)]\s*(.+?)(?:\n|\r\n?)\s*C[:\.\)]\s*(.+?)(?:\n|\r\n?)\s*D[:\.\)]\s*(.+?))',
        
        # Simple Q&A patterns
        r'(?:Q[:\.]?\s*)?(.+?\?)\s*(?:\n|\r\n?)\s*(?:A[:\.]?\s*)?(.+?)(?=(?:\n|\r\n?)\s*(?:Q[:\.]?|Question|\d+\.|$))'
    ]
    
    for i, pattern in enumerate(question_patterns):
        matches = re.finditer(pattern, text, re.MULTILINE | re.DOTALL | re.IGNORECASE)
        
        for match in matches:
            try:
                if i < 2:  # Multiple choice patterns
                    question_text = match.group(1).strip()
                    options = [
                        match.group(2).strip() if match.group(2) else "",
                        match.group(3).strip() if match.group(3) else "",
                        match.group(4).strip() if match.group(4) else "",
                        match.group(5).strip() if match.group(5) else ""
                    ]
                    # Filter out empty options
                    options = [opt for opt in options if opt]
                    
                    if len(options) >= 2:  # At least 2 options required
                        question_data = {
                            'question_text': question_text,
                            'answer_options': options,
                            'certification_type': certification_type,
                            'question_type': 'multiple_choice',
                            'extracted_by': f'pattern_{i+1}'
                        }
                        questions.append(question_data)
                        
                else:  # Simple Q&A pattern
                    question_text = match.group(1).strip()
                    answer_text = match.group(2).strip()
                    
                    if question_text and answer_text:
                        question_data = {
                            'question_text': question_text,
                            'answer_text': answer_text,
                            'certification_type': certification_type,
                            'question_type': 'open_ended',
                            'extracted_by': f'pattern_{i+1}'
                        }
                        questions.append(question_data)
                        
            except (IndexError, AttributeError) as e:
                print(f"Error processing question match: {e}")
                continue
    
    # Remove duplicates based on question text
    seen_questions = set()
    unique_questions = []
    
    for q in questions:
        question_key = q['question_text'].lower().strip()
        if question_key not in seen_questions and len(question_key) > 10:  # Minimum question length
            seen_questions.add(question_key)
            unique_questions.append(q)
    
    print(f"Extracted {len(unique_questions)} unique questions for {certification_type}")
    return unique_questions


def classify_content_difficulty(text: str, certification_type: str) -> str:
    """
    Classify content difficulty based on text analysis and certification context.
    
    Args:
        text: Document text content
        certification_type: Certification type for context
        
    Returns:
        Difficulty level: 'beginner', 'intermediate', or 'advanced'
    """
    if not text:
        return 'intermediate'
    
    text_lower = text.lower()
    
    # Professional and Specialty certifications are generally advanced
    if certification_type in ['DOP', 'SAP', 'MLS', 'SCS', 'ANS']:
        return 'advanced'
    
    # Foundational certifications are generally beginner
    if certification_type in ['CCP', 'AIP']:
        return 'beginner'
    
    # Analyze text for complexity indicators
    advanced_keywords = [
        'architecture', 'design patterns', 'best practices', 'optimization',
        'troubleshooting', 'performance tuning', 'security hardening',
        'enterprise', 'scalability', 'high availability', 'disaster recovery'
    ]
    
    beginner_keywords = [
        'introduction', 'basics', 'getting started', 'overview',
        'fundamentals', 'what is', 'simple', 'basic'
    ]
    
    advanced_count = sum(1 for keyword in advanced_keywords if keyword in text_lower)
    beginner_count = sum(1 for keyword in beginner_keywords if keyword in text_lower)
    
    if advanced_count > beginner_count and advanced_count > 3:
        return 'advanced'
    elif beginner_count > advanced_count and beginner_count > 2:
        return 'beginner'
    else:
        return 'intermediate'


def extract_text(bucket, key):
    # ... (this function remains the same)
    file_extension = os.path.splitext(key)[1].lower()
    temp_file_path = f"/tmp/{os.path.basename(key)}"
    s3_client.download_file(bucket, key, temp_file_path)
    text = ""
    if file_extension == ".pdf":
        with open(temp_file_path, 'rb') as f:
            reader = PdfReader(f)
            for page in reader.pages:
                text += page.extract_text()
    else:
        print(f"Unsupported file type: {file_extension}")
    os.remove(temp_file_path)
    return text

def chunk_text_certification_aware(text, certification_type='GENERAL', chunk_size=1000, chunk_overlap=200):
    """
    Enhanced text chunking with certification-aware strategies.
    
    Args:
        text: Text to chunk
        certification_type: Certification type for context-aware chunking
        chunk_size: Base chunk size
        chunk_overlap: Overlap between chunks
        
    Returns:
        List of text chunks optimized for the certification type
    """
    # Adjust chunking parameters based on certification type
    if certification_type in ['CCP', 'AIP']:  # Foundational - smaller chunks for basic concepts
        chunk_size = 800
        chunk_overlap = 150
        separators = ["\n\n", "\n", ". ", " ", ""]
    elif certification_type in ['DOP', 'SAP']:  # Professional - larger chunks for complex topics
        chunk_size = 1200
        chunk_overlap = 250
        separators = ["\n\n", "\n", ". ", " ", ""]
    elif certification_type in ['MLS', 'SCS', 'ANS']:  # Specialty - preserve technical context
        chunk_size = 1100
        chunk_overlap = 300  # Higher overlap to preserve technical relationships
        separators = ["\n\n", "\n", ". ", " ", ""]
    else:  # Associate level and general
        chunk_size = 1000
        chunk_overlap = 200
        separators = ["\n\n", "\n", ". ", " ", ""]
    
    # Use certification-aware separators to avoid breaking important content
    cert_aware_separators = _get_certification_aware_separators(certification_type) + separators
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, 
        chunk_overlap=chunk_overlap,
        length_function=len, 
        separators=cert_aware_separators,
    )
    
    chunks = text_splitter.split_text(text)
    
    # Post-process chunks to avoid breaking certification-specific content
    processed_chunks = _post_process_certification_chunks(chunks, certification_type)
    
    print(f"Created {len(processed_chunks)} certification-aware chunks for {certification_type}")
    return processed_chunks


def _get_certification_aware_separators(certification_type: str) -> List[str]:
    """Get certification-specific separators to preserve important content boundaries."""
    base_separators = [
        "\n\n# ",  # Markdown headers
        "\n## ",   # Subheaders
        "\n### ",  # Sub-subheaders
        "\nQuestion ",  # Question boundaries
        "\nQ: ",   # Q&A format
        "\nA: ",   # Answer boundaries
    ]
    
    # Add certification-specific separators
    if certification_type in ['SAA', 'SAP']:  # Architecture certifications
        base_separators.extend([
            "\nArchitecture Pattern:",
            "\nDesign Principle:",
            "\nBest Practice:",
            "\nService:",
        ])
    elif certification_type in ['DVA']:  # Developer certification
        base_separators.extend([
            "\nCode Example:",
            "\nAPI:",
            "\nSDK:",
            "\nFunction:",
        ])
    elif certification_type in ['SOA', 'DOP']:  # Operations certifications
        base_separators.extend([
            "\nMonitoring:",
            "\nDeployment:",
            "\nConfiguration:",
            "\nTroubleshooting:",
        ])
    elif certification_type in ['SCS']:  # Security certification
        base_separators.extend([
            "\nSecurity Control:",
            "\nCompliance:",
            "\nEncryption:",
            "\nAccess Control:",
        ])
    elif certification_type in ['MLS', 'MLA']:  # ML certifications
        base_separators.extend([
            "\nAlgorithm:",
            "\nModel:",
            "\nTraining:",
            "\nInference:",
        ])
    
    return base_separators


def _post_process_certification_chunks(chunks: List[str], certification_type: str) -> List[str]:
    """Post-process chunks to ensure certification-specific content integrity."""
    processed_chunks = []
    
    for chunk in chunks:
        # Ensure questions aren't split across chunks
        if _contains_partial_question(chunk):
            # Try to merge with previous chunk if it makes sense
            if processed_chunks and len(processed_chunks[-1]) + len(chunk) < 1500:
                processed_chunks[-1] += " " + chunk
                continue
        
        # Ensure code examples aren't split (for DVA certification)
        if certification_type == 'DVA' and _contains_partial_code(chunk):
            if processed_chunks and len(processed_chunks[-1]) + len(chunk) < 1500:
                processed_chunks[-1] += " " + chunk
                continue
        
        processed_chunks.append(chunk)
    
    return processed_chunks


def _contains_partial_question(chunk: str) -> bool:
    """Check if chunk contains a partial question that should be merged."""
    # Look for question patterns that might be incomplete
    question_starts = ['What is', 'How does', 'Which of', 'When should', 'Why would']
    question_ends = ['?', 'A)', 'B)', 'C)', 'D)']
    
    has_question_start = any(start in chunk for start in question_starts)
    has_question_end = any(end in chunk for end in question_ends)
    
    # If it starts like a question but doesn't end properly, it might be partial
    return has_question_start and not has_question_end


def _contains_partial_code(chunk: str) -> bool:
    """Check if chunk contains partial code that should be merged."""
    code_indicators = ['```', 'import ', 'def ', 'class ', 'function', '{', '}']
    
    # Count opening and closing braces/brackets
    open_braces = chunk.count('{') + chunk.count('[') + chunk.count('(')
    close_braces = chunk.count('}') + chunk.count(']') + chunk.count(')')
    
    # If there are unmatched braces or code indicators, it might be partial
    has_code = any(indicator in chunk for indicator in code_indicators)
    unmatched_braces = abs(open_braces - close_braces) > 2
    
    return has_code and unmatched_braces


# Maintain backward compatibility
def chunk_text(text, chunk_size=1000, chunk_overlap=200):
    """Backward compatible wrapper for certification-aware chunking."""
    return chunk_text_certification_aware(text, 'GENERAL', chunk_size, chunk_overlap)

def get_embeddings(chunks):
    # ... (this function remains the same)
    embeddings = []
    for chunk in chunks:
        body = json.dumps({"inputText": chunk})
        response = bedrock_runtime.invoke_model(
            body=body, modelId="amazon.titan-embed-text-v1",
            accept="application/json", contentType="application/json"
        )
        response_body = json.loads(response.get("body").read())
        embedding = response_body.get("embedding")
        embeddings.append(embedding)
    return embeddings

def store_embeddings_enhanced(chunks, embeddings, file_key, content_metadata):
    """
    Stores text chunks and their embeddings using the enhanced vector storage service.
    
    Args:
        chunks: List of text chunks
        embeddings: List of embedding vectors
        file_key: S3 object key
        content_metadata: Content metadata dictionary
    """
    try:
        # Import the enhanced models and services
        import sys
        import os
        
        # Add shared directory to path for imports
        shared_path = '/opt/python/shared' if os.path.exists('/opt/python/shared') else '/tmp/shared'
        if shared_path not in sys.path:
            sys.path.append(shared_path)
        
        from shared.models import (
            VectorDocument, ContentMetadata, CertificationType, 
            ContentType, DifficultyLevel, get_certification_level
        )
        from shared.vector_storage_service import VectorStorageService
        
        # Convert content_metadata dict to ContentMetadata object
        cert_type = CertificationType(content_metadata.get('certification_type', 'GENERAL'))
        content_type = ContentType(content_metadata.get('content_type', 'study_guide'))
        difficulty = DifficultyLevel(content_metadata.get('difficulty_level', 'intermediate'))
        
        content_meta_obj = ContentMetadata(
            content_id=content_metadata['content_id'],
            title=content_metadata.get('title', os.path.basename(file_key)),
            content_type=content_type,
            certification_type=cert_type,
            category=content_metadata.get('category', 'general'),
            subcategory=content_metadata.get('subcategory'),
            difficulty_level=difficulty,
            tags=content_metadata.get('tags', []),
            created_at=datetime.fromisoformat(content_metadata.get('created_at', datetime.utcnow().isoformat())),
            version=content_metadata.get('version', '1.0'),
            source_file=file_key,
            source_bucket=content_metadata.get('source_bucket', ''),
            chunk_count=len(chunks),
            question_count=content_metadata.get('question_count', 0)
        )
        
        # Initialize vector storage service
        vector_service = VectorStorageService(
            opensearch_endpoint=opensearch_endpoint,
            index_name=opensearch_index,
            region_name=os.environ.get('AWS_REGION', 'us-east-1')
        )
        
        # Create certification-aware vector documents
        vector_docs = vector_service.create_certification_aware_chunks(
            content_metadata=content_meta_obj,
            text=' '.join(chunks),  # Reconstruct full text for context
            embeddings=embeddings,
            chunk_texts=chunks
        )
        
        # Store with certification-aware indexing
        success = vector_service.store_vector_documents(vector_docs, use_certification_indices=True)
        
        if success:
            print(f"Successfully stored {len(vector_docs)} certification-aware documents for {cert_type.value}")
        else:
            print(f"Failed to store some documents for {cert_type.value}")
        
        return success
        
    except Exception as e:
        print(f"Error in enhanced vector storage: {e}")
        # Fallback to original storage method
        return store_embeddings_fallback(chunks, embeddings, file_key, content_metadata)


def store_embeddings_fallback(chunks, embeddings, file_key, content_metadata):
    """
    Fallback storage method using the original approach.
    
    Args:
        chunks: List of text chunks
        embeddings: List of embedding vectors
        file_key: S3 object key
        content_metadata: Content metadata dictionary
    """
    certification_type = content_metadata.get('certification_type', 'GENERAL')
    
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        # Create enhanced document with certification context
        document = {
            'document_id': f"{content_metadata['content_id']}-chunk-{i}",
            'content_id': content_metadata['content_id'],
            'chunk_index': i,
            'text': chunk,
            'vector_field': embedding,  # OpenSearch vector field
            'certification_type': certification_type,
            'certification_level': _get_cert_level_from_type(certification_type),
            'source_file': file_key,
            'source_bucket': content_metadata.get('source_bucket', ''),
            'chunk_size': len(chunk),
            'processed_at': content_metadata.get('created_at', datetime.utcnow().isoformat()),
            'difficulty_level': content_metadata.get('difficulty_level', 'intermediate'),
            'content_type': content_metadata.get('content_type', 'study_guide'),
            'category': content_metadata.get('category', 'general'),
            'subcategory': content_metadata.get('subcategory'),
            'tags': content_metadata.get('tags', []),
            'metadata': {
                'extraction_method': content_metadata.get('extraction_method', 'automatic'),
                'question_count': content_metadata.get('question_count', 0),
                'total_chunks': len(chunks),
                'version': content_metadata.get('version', '1.0'),
                'language': 'en',
                'chunk_position': i / len(chunks),
                'chunk_overlap_info': {
                    'has_previous': i > 0,
                    'has_next': i < len(chunks) - 1,
                    'is_first': i == 0,
                    'is_last': i == len(chunks) - 1
                }
            }
        }
        
        try:
            opensearch_client.index(index=opensearch_index, body=document)
        except Exception as e:
            print(f"Error indexing chunk {i}: {e}")
            # Continue with other chunks even if one fails
            continue
            
    print(f"Successfully indexed {len(chunks)} certification-aware documents into OpenSearch for {certification_type}")
    return True


def _get_cert_level_from_type(cert_type: str) -> str:
    """Get certification level from certification type."""
    foundational = ['CCP', 'AIP']
    associate = ['MLA', 'DEA', 'DVA', 'SAA', 'SOA']
    professional = ['DOP', 'SAP']
    specialty = ['ANS', 'MLS', 'SCS']
    
    if cert_type in foundational:
        return 'foundational'
    elif cert_type in associate:
        return 'associate'
    elif cert_type in professional:
        return 'professional'
    elif cert_type in specialty:
        return 'specialty'
    else:
        return 'general'


# Maintain backward compatibility
def store_embeddings(chunks, embeddings, file_key, content_metadata):
    """Backward compatible wrapper for enhanced storage."""
    return store_embeddings_enhanced(chunks, embeddings, file_key, content_metadata)

def handler(event, context):
    """
    Enhanced Lambda handler with certification-aware content processing and comprehensive error handling.
    
    Processes S3 upload events with:
    - Multi-level certification detection (S3 context, filename, content)
    - Question/answer extraction with certification context
    - Automatic content classification and difficulty assessment
    - Structured metadata creation and storage
    - Comprehensive error handling and retry logic
    """
    # Initialize response structure
    response = {
        'statusCode': 200,
        'body': json.dumps({'status': 'success', 'message': 'Processing completed'})
    }
    
    try:
        # Validate event structure
        if not event or 'Records' not in event or not event['Records']:
            raise ValueError("Invalid event structure: missing Records")
        
        # Ensure AWS clients are initialized
        if not _validate_aws_clients():
            raise RuntimeError("AWS clients not properly initialized")
        
        # Extract S3 event information with validation
        record = event['Records'][0]
        bucket, key = _extract_s3_info(record)
        
        print(f"Processing new file: s3://{bucket}/{key}")
        
        # Process the document with comprehensive error handling
        processing_result = _process_document_with_error_handling(bucket, key)
        
        if processing_result['success']:
            print(f"Successfully processed document: {processing_result['content_id']}")
            response['body'] = json.dumps({
                'status': 'success',
                'message': 'Document processed successfully',
                'content_id': processing_result['content_id'],
                'certification_type': processing_result['certification_type'],
                'chunks_processed': processing_result['chunks_processed']
            })
        else:
            print(f"Document processing failed: {processing_result['error']}")
            response = {
                'statusCode': 500,
                'body': json.dumps({
                    'status': 'error',
                    'message': processing_result['error'],
                    'error_type': processing_result.get('error_type', 'ProcessingError')
                })
            }
        
        return response
        
    except ValueError as e:
        error_msg = f"Validation error: {str(e)}"
        print(error_msg)
        return {
            'statusCode': 400,
            'body': json.dumps({
                'status': 'error',
                'message': error_msg,
                'error_type': 'ValidationError'
            })
        }
        
    except Exception as e:
        error_msg = f"Unexpected error in Lambda handler: {str(e)}"
        print(error_msg)
        print(f"Traceback: {traceback.format_exc()}")
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'status': 'error',
                'message': error_msg,
                'error_type': 'InternalError'
            })
        }


def _validate_aws_clients() -> bool:
    """Validate that all required AWS clients are initialized."""
    global s3_client, bedrock_runtime, opensearch_client
    
    if not s3_client:
        print("S3 client not initialized")
        return False
    if not bedrock_runtime:
        print("Bedrock client not initialized")
        return False
    if not opensearch_client:
        print("OpenSearch client not initialized")
        return False
    
    return True


def _extract_s3_info(record: Dict[str, Any]) -> Tuple[str, str]:
    """Extract and validate S3 bucket and key from event record."""
    try:
        if 's3' not in record:
            raise ValueError("Invalid record structure: missing s3 section")
        
        s3_info = record['s3']
        
        if 'bucket' not in s3_info or 'name' not in s3_info['bucket']:
            raise ValueError("Invalid record structure: missing bucket name")
        
        if 'object' not in s3_info or 'key' not in s3_info['object']:
            raise ValueError("Invalid record structure: missing object key")
        
        bucket = s3_info['bucket']['name']
        key = unquote_plus(s3_info['object']['key'])
        
        # Validate bucket and key
        if not bucket or not key:
            raise ValueError("Empty bucket name or object key")
        
        # Basic security check for key
        if '..' in key or key.startswith('/'):
            raise ValueError("Invalid object key format")
        
        return bucket, key
        
    except Exception as e:
        raise ValueError(f"Failed to extract S3 information: {str(e)}")


def _process_document_with_error_handling(bucket: str, key: str) -> Dict[str, Any]:
    """Process document with comprehensive error handling and retry logic."""
    result = {
        'success': False,
        'error': None,
        'error_type': None,
        'content_id': None,
        'certification_type': None,
        'chunks_processed': 0
    }
    
    try:
        # Step 1: Extract text content with retry logic
        document_text = _extract_text_with_retry(bucket, key)
        if not document_text:
            result['error'] = 'No text content could be extracted from the document'
            result['error_type'] = 'ContentExtractionError'
            return result
        
        print(f"Extracted {len(document_text)} characters of text")
        
        # Step 2: Multi-level certification detection with error handling
        certification_result = _detect_certification_with_error_handling(bucket, key, document_text)
        final_certification = certification_result['certification_type']
        
        print(f"Certification detection results:")
        print(f"  - From S3 context: {certification_result['s3_detection']}")
        print(f"  - From content: {certification_result['content_detection']}")
        print(f"  - Final decision: {final_certification}")
        
        # Step 3: Extract questions and answers with error handling
        extracted_questions = _extract_questions_with_error_handling(document_text, final_certification)
        
        # Step 4: Classify content difficulty with fallback
        difficulty_level = _classify_difficulty_with_fallback(document_text, final_certification)
        
        # Step 5: Determine content type
        content_type = 'practice_exam' if len(extracted_questions) > 5 else 'study_guide'
        
        # Step 6: Create certification-aware content chunks with error handling
        text_chunks = _create_chunks_with_error_handling(document_text, final_certification)
        
        # Step 7: Generate embeddings with retry logic
        chunk_embeddings = _generate_embeddings_with_retry(text_chunks)
        
        # Step 8: Create and validate content metadata
        content_metadata = _create_content_metadata_with_validation(
            bucket, key, final_certification, content_type, difficulty_level, 
            len(text_chunks), len(extracted_questions)
        )
        
        # Step 9: Store embeddings with retry logic
        storage_success = _store_embeddings_with_retry(
            text_chunks, chunk_embeddings, key, content_metadata
        )
        
        if storage_success:
            result['success'] = True
            result['content_id'] = content_metadata['content_id']
            result['certification_type'] = final_certification
            result['chunks_processed'] = len(text_chunks)
        else:
            result['error'] = 'Failed to store document embeddings'
            result['error_type'] = 'StorageError'
        
        return result
        
    except Exception as e:
        error_msg = f"Document processing failed: {str(e)}"
        print(error_msg)
        print(f"Traceback: {traceback.format_exc()}")
        
        result['error'] = error_msg
        result['error_type'] = type(e).__name__
        return result


def _extract_text_with_retry(bucket: str, key: str, max_retries: int = 3) -> str:
    """Extract text from document with retry logic."""
    for attempt in range(max_retries):
        try:
            return extract_text(bucket, key)
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code in ['NoSuchKey', 'NoSuchBucket', 'AccessDenied']:
                # These errors are not retryable
                raise
            
            if attempt == max_retries - 1:
                raise
            
            print(f"Text extraction attempt {attempt + 1} failed: {error_code}. Retrying...")
            
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            
            print(f"Text extraction attempt {attempt + 1} failed: {str(e)}. Retrying...")
    
    return ""


def _detect_certification_with_error_handling(bucket: str, key: str, document_text: str) -> Dict[str, str]:
    """Detect certification type with comprehensive error handling."""
    result = {
        'certification_type': 'GENERAL',
        's3_detection': 'GENERAL',
        'content_detection': 'GENERAL'
    }
    
    try:
        # Detect from S3 context with error handling
        try:
            result['s3_detection'] = detect_certification_from_s3_context(bucket, key)
        except Exception as e:
            print(f"S3 context detection failed: {e}")
            result['s3_detection'] = 'GENERAL'
        
        # Detect from document content with error handling
        try:
            result['content_detection'] = detect_certification_from_content(document_text)
        except Exception as e:
            print(f"Content detection failed: {e}")
            result['content_detection'] = 'GENERAL'
        
        # Use S3 context if available, otherwise use content detection
        result['certification_type'] = (
            result['s3_detection'] if result['s3_detection'] != 'GENERAL' 
            else result['content_detection']
        )
        
    except Exception as e:
        print(f"Certification detection failed: {e}")
        result['certification_type'] = 'GENERAL'
    
    return result


def _extract_questions_with_error_handling(document_text: str, certification_type: str) -> List[Dict[str, Any]]:
    """Extract questions and answers with error handling."""
    try:
        return extract_questions_and_answers(document_text, certification_type)
    except Exception as e:
        print(f"Question extraction failed: {e}")
        return []


def _classify_difficulty_with_fallback(document_text: str, certification_type: str) -> str:
    """Classify content difficulty with fallback logic."""
    try:
        return classify_content_difficulty(document_text, certification_type)
    except Exception as e:
        print(f"Difficulty classification failed: {e}")
        # Fallback based on certification type
        if certification_type in ['DOP', 'SAP', 'MLS', 'SCS', 'ANS']:
            return 'advanced'
        elif certification_type in ['CCP', 'AIP']:
            return 'beginner'
        else:
            return 'intermediate'


def _create_chunks_with_error_handling(document_text: str, certification_type: str) -> List[str]:
    """Create text chunks with error handling."""
    try:
        return chunk_text_certification_aware(document_text, certification_type)
    except Exception as e:
        print(f"Certification-aware chunking failed: {e}. Falling back to basic chunking.")
        try:
            return chunk_text(document_text)
        except Exception as e2:
            print(f"Basic chunking also failed: {e2}")
            # Last resort: split by paragraphs
            chunks = document_text.split('\n\n')
            return [chunk.strip() for chunk in chunks if chunk.strip()]


def _generate_embeddings_with_retry(text_chunks: List[str], max_retries: int = 3) -> List[List[float]]:
    """Generate embeddings with retry logic."""
    for attempt in range(max_retries):
        try:
            return get_embeddings(text_chunks)
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code in ['ValidationException', 'AccessDeniedException']:
                # These errors are not retryable
                raise
            
            if attempt == max_retries - 1:
                raise
            
            print(f"Embedding generation attempt {attempt + 1} failed: {error_code}. Retrying...")
            
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            
            print(f"Embedding generation attempt {attempt + 1} failed: {str(e)}. Retrying...")
    
    return []


def _create_content_metadata_with_validation(bucket: str, key: str, certification_type: str,
                                           content_type: str, difficulty_level: str,
                                           chunk_count: int, question_count: int) -> Dict[str, Any]:
    """Create content metadata with validation."""
    try:
        content_id = f"content-{key.replace('/', '-').replace('.', '-')}-{int(datetime.utcnow().timestamp())}"
        
        # Validate content_id format
        if not re.match(r'^[a-zA-Z0-9\-_]+$', content_id):
            raise ValueError(f"Invalid content_id format: {content_id}")
        
        metadata = {
            'content_id': content_id,
            'title': os.path.basename(key),
            'content_type': content_type,
            'certification_type': certification_type,
            'category': _determine_category_from_certification(certification_type),
            'difficulty_level': difficulty_level,
            'source_file': key,
            'source_bucket': bucket,
            'created_at': datetime.utcnow().isoformat(),
            'version': '1.0',
            'chunk_count': chunk_count,
            'question_count': question_count,
            'tags': _generate_tags_from_certification(certification_type),
            'extraction_method': 'certification_aware_processing'
        }
        
        # Validate required fields
        required_fields = ['content_id', 'title', 'content_type', 'certification_type']
        for field in required_fields:
            if not metadata.get(field):
                raise ValueError(f"Required field '{field}' is missing or empty")
        
        return metadata
        
    except Exception as e:
        raise ValueError(f"Failed to create content metadata: {str(e)}")


def _store_embeddings_with_retry(text_chunks: List[str], embeddings: List[List[float]], 
                                key: str, metadata: Dict[str, Any], max_retries: int = 3) -> bool:
    """Store embeddings with retry logic."""
    for attempt in range(max_retries):
        try:
            return store_embeddings_enhanced(text_chunks, embeddings, key, metadata)
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"Final storage attempt failed: {str(e)}")
                return False
            
            print(f"Storage attempt {attempt + 1} failed: {str(e)}. Retrying...")
    
    return Falsemat(),
            'chunk_count': len(text_chunks),
            'question_count': len(extracted_questions),
            'extraction_method': 'enhanced_lambda_v2',
            'tags': _generate_tags_from_content(document_text, final_certification),
            'detection_details': {
                'cert_from_s3': cert_from_s3,
                'cert_from_content': cert_from_content,
                'final_certification': final_certification
            }
        }
        
        # Store embeddings with enhanced certification-aware metadata
        storage_success = store_embeddings_enhanced(text_chunks, chunk_embeddings, key, content_metadata)
        
        # Log extracted questions for debugging (first 3 only)
        if extracted_questions:
            print(f"Sample extracted questions:")
            for i, q in enumerate(extracted_questions[:3]):
                print(f"  Q{i+1}: {q['question_text'][:100]}...")
        
        return {
            'statusCode': 200, 
            'body': json.dumps({
                'message': 'Document processed successfully with certification-aware extraction!',
                'content_id': content_metadata['content_id'],
                'certification_detected': final_certification,
                'chunks_processed': len(text_chunks),
                'questions_extracted': len(extracted_questions),
                'difficulty_level': difficulty_level,
                'content_type': content_type,
                'detection_method': {
                    's3_context': cert_from_s3,
                    'content_analysis': cert_from_content,
                    'final_decision': final_certification
                }
            })
        }
            
    except Exception as e:
        print(f"Error processing file {key}: {e}")
        import traceback
        traceback.print_exc()
        return {'statusCode': 500, 'body': json.dumps(f'An error occurred: {str(e)}')}


def _determine_category_from_certification(cert_type: str) -> str:
    """Determine content category based on certification type."""
    category_mapping = {
        'SAA': 'Solutions Architecture',
        'DVA': 'Development',
        'SOA': 'System Operations',
        'CCP': 'Cloud Fundamentals',
        'DOP': 'DevOps',
        'SAP': 'Advanced Architecture',
        'MLS': 'Machine Learning',
        'SCS': 'Security',
        'ANS': 'Networking',
        'AIP': 'AI/ML Fundamentals',
        'MLA': 'ML Engineering',
        'DEA': 'Data Engineering',
        'GENERAL': 'General AWS'
    }
    return category_mapping.get(cert_type, 'General AWS')


def _generate_tags_from_content(text: str, cert_type: str) -> List[str]:
    """Generate relevant tags based on content analysis."""
    tags = [cert_type.lower()]
    
    # Add certification level tag
    level_mapping = {
        'CCP': 'foundational', 'AIP': 'foundational',
        'SAA': 'associate', 'DVA': 'associate', 'SOA': 'associate', 'MLA': 'associate', 'DEA': 'associate',
        'DOP': 'professional', 'SAP': 'professional',
        'MLS': 'specialty', 'SCS': 'specialty', 'ANS': 'specialty'
    }
    
    if cert_type in level_mapping:
        tags.append(level_mapping[cert_type])
    
    # Add service-specific tags based on content
    text_lower = text.lower()
    service_keywords = {
        'ec2': ['ec2', 'elastic compute', 'instances'],
        's3': ['s3', 'simple storage', 'bucket'],
        'rds': ['rds', 'relational database', 'mysql', 'postgresql'],
        'lambda': ['lambda', 'serverless', 'function'],
        'vpc': ['vpc', 'virtual private cloud', 'networking'],
        'iam': ['iam', 'identity', 'access management', 'permissions'],
        'cloudformation': ['cloudformation', 'infrastructure as code', 'template'],
        'cloudwatch': ['cloudwatch', 'monitoring', 'metrics', 'logs']
    }
    
    for service, keywords in service_keywords.items():
        if any(keyword in text_lower for keyword in keywords):
            tags.append(service)
    
    return list(set(tags))  # Remove duplicates