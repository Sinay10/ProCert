#!/usr/bin/env python3
"""
Test script to verify the data models and interfaces work correctly.
This script can be run to validate the implementation.
"""

import sys
import os
from datetime import datetime

# Add the current directory to Python path so we can import shared
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from shared import (
    ContentMetadata, QuestionAnswer, UserProgress, VectorDocument,
    ContentType, CertificationType, DifficultyLevel, ProgressType,
    validate_model, validate_models, detect_certification_from_filename,
    get_certification_display_name, get_certification_level,
    get_certifications_for_dropdown, validate_certification_code
)


def test_content_metadata():
    """Test ContentMetadata model."""
    print("Testing ContentMetadata...")
    
    # Valid metadata
    metadata = ContentMetadata(
        content_id="test-content-001",
        title="AWS SAA Practice Questions",
        content_type=ContentType.QUESTION,
        certification_type=CertificationType.SAA,
        category="EC2",
        subcategory="Instance Types",
        difficulty_level=DifficultyLevel.INTERMEDIATE,
        tags=["compute", "instances"],
        source_file="saa-questions.pdf",
        source_bucket="procert-materials-saa",
        chunk_count=5,
        question_count=10
    )
    
    assert metadata.is_valid(), f"Valid metadata should pass validation: {metadata.validate()}"
    
    # Test serialization
    data_dict = metadata.to_dict()
    restored = ContentMetadata.from_dict(data_dict)
    assert restored.content_id == metadata.content_id
    assert restored.certification_type == metadata.certification_type
    
    # Test invalid metadata
    invalid_metadata = ContentMetadata(
        content_id="",  # Invalid: empty
        title="Test",
        content_type=ContentType.QUESTION,
        certification_type=CertificationType.SAA,
        category="Test",
        chunk_count=-1  # Invalid: negative
    )
    
    assert not invalid_metadata.is_valid(), "Invalid metadata should fail validation"
    errors = invalid_metadata.validate()
    assert len(errors) > 0, "Should have validation errors"
    
    print("✓ ContentMetadata tests passed")


def test_question_answer():
    """Test QuestionAnswer model."""
    print("Testing QuestionAnswer...")
    
    # Valid question
    question = QuestionAnswer(
        question_id="q-001",
        content_id="content-001",
        question_text="What is the maximum size of an EBS volume?",
        answer_options=["1 TB", "16 TB", "64 TB", "100 TB"],
        correct_answer="64 TB",
        explanation="EBS volumes can be up to 64 TB in size.",
        category="Storage",
        difficulty=DifficultyLevel.BEGINNER,
        tags=["ebs", "storage"]
    )
    
    assert question.is_valid(), f"Valid question should pass validation: {question.validate()}"
    
    # Test serialization
    data_dict = question.to_dict()
    restored = QuestionAnswer.from_dict(data_dict)
    assert restored.question_id == question.question_id
    assert restored.correct_answer == question.correct_answer
    
    # Test invalid question
    invalid_question = QuestionAnswer(
        question_id="",  # Invalid: empty
        content_id="content-001",
        question_text="Test question?",
        answer_options=["A"],  # Invalid: only one option
        correct_answer="B"  # Invalid: not in options
    )
    
    assert not invalid_question.is_valid(), "Invalid question should fail validation"
    
    print("✓ QuestionAnswer tests passed")


def test_user_progress():
    """Test UserProgress model."""
    print("Testing UserProgress...")
    
    # Valid progress
    progress = UserProgress(
        user_id="user-123",
        content_id="content-001",
        progress_type=ProgressType.COMPLETED,
        score=85.5,
        time_spent=300,  # 5 minutes
        session_id="session-abc"
    )
    
    assert progress.is_valid(), f"Valid progress should pass validation: {progress.validate()}"
    
    # Test serialization
    data_dict = progress.to_dict()
    restored = UserProgress.from_dict(data_dict)
    assert restored.user_id == progress.user_id
    assert restored.score == progress.score
    
    # Test invalid progress
    invalid_progress = UserProgress(
        user_id="",  # Invalid: empty
        content_id="content-001",
        progress_type=ProgressType.VIEWED,
        score=150,  # Invalid: > 100
        time_spent=-10  # Invalid: negative
    )
    
    assert not invalid_progress.is_valid(), "Invalid progress should fail validation"
    
    print("✓ UserProgress tests passed")


def test_vector_document():
    """Test VectorDocument model."""
    print("Testing VectorDocument...")
    
    # Create a mock embedding (1536 dimensions - common for many models)
    mock_embedding = [0.1] * 1536
    
    # Valid vector document
    vector_doc = VectorDocument(
        document_id="doc-001",
        content_id="content-001",
        chunk_index=0,
        text="This is a sample text chunk for testing.",
        vector_embedding=mock_embedding,
        certification_type=CertificationType.SAA,
        metadata={"source": "test.pdf", "page": 1}
    )
    
    assert vector_doc.is_valid(), f"Valid vector document should pass validation: {vector_doc.validate()}"
    
    # Test serialization
    data_dict = vector_doc.to_dict()
    restored = VectorDocument.from_dict(data_dict)
    assert restored.document_id == vector_doc.document_id
    assert len(restored.vector_embedding) == len(vector_doc.vector_embedding)
    
    # Test invalid vector document
    invalid_vector_doc = VectorDocument(
        document_id="",  # Invalid: empty
        content_id="content-001",
        chunk_index=-1,  # Invalid: negative
        text="",  # Invalid: empty
        vector_embedding=[0.1] * 100,  # Invalid: wrong dimensions
        certification_type=CertificationType.SAA
    )
    
    assert not invalid_vector_doc.is_valid(), "Invalid vector document should fail validation"
    
    print("✓ VectorDocument tests passed")


def test_certification_detection():
    """Test certification detection utilities."""
    print("Testing certification detection...")
    
    # Test filename detection without admin override
    test_cases = [
        ("SAA-1.pdf", CertificationType.SAA),
        ("DVA-study-guide.pdf", CertificationType.DVA),
        ("CCP-2.docx", CertificationType.CCP),
        ("s3://bucket/SAA-practice-exam.pdf", CertificationType.SAA),
        ("MLS-specialty-guide.pdf", CertificationType.MLS),
        ("random-file.pdf", CertificationType.GENERAL),  # No code = GENERAL
        ("DOP-professional-exam.pdf", CertificationType.DOP),
        ("document-without-code.pdf", CertificationType.GENERAL)  # No code = GENERAL
    ]
    
    for filename, expected in test_cases:
        result = detect_certification_from_filename(filename)
        assert result == expected, f"Expected {expected} for {filename}, got {result}"
    
    print("✓ Filename detection tests passed")
    
    # Test admin override functionality
    admin_override_cases = [
        ("random-file.pdf", "SAA", CertificationType.SAA),  # Override wins
        ("DVA-guide.pdf", "CCP", CertificationType.CCP),    # Override wins over filename
        ("SAA-exam.pdf", "MLS", CertificationType.MLS),     # Override wins over filename
        ("any-file.pdf", "GENERAL", CertificationType.GENERAL),
        ("any-file.pdf", None, CertificationType.GENERAL),  # No override, no code = GENERAL
    ]
    
    for filename, admin_override, expected in admin_override_cases:
        result = detect_certification_from_filename(filename, admin_override)
        assert result == expected, f"Expected {expected} for {filename} with override {admin_override}, got {result}"
    
    print("✓ Admin override tests passed")
    
    # Test display names
    assert get_certification_display_name(CertificationType.SAA) == "AWS Certified Solutions Architect - Associate"
    assert get_certification_display_name(CertificationType.CCP) == "AWS Certified Cloud Practitioner"
    print("✓ Display name tests passed")
    
    # Test certification levels
    assert get_certification_level(CertificationType.CCP) == "Foundational"
    assert get_certification_level(CertificationType.SAA) == "Associate"
    assert get_certification_level(CertificationType.DOP) == "Professional"
    assert get_certification_level(CertificationType.MLS) == "Specialty"
    assert get_certification_level(CertificationType.GENERAL) == "General"
    print("✓ Certification level tests passed")
    
    # Test dropdown functionality
    dropdown_options = get_certifications_for_dropdown()
    assert len(dropdown_options) > 0, "Should have certification options"
    assert all("code" in opt and "name" in opt and "level" in opt for opt in dropdown_options), "All options should have required fields"
    print("✓ Dropdown options tests passed")
    
    # Test validation
    assert validate_certification_code("SAA") == True
    assert validate_certification_code("INVALID") == False
    assert validate_certification_code("") == False
    assert validate_certification_code(None) == False
    print("✓ Certification validation tests passed")
    
    print("✓ Certification detection tests passed")


def test_validation_helpers():
    """Test validation helper functions."""
    print("Testing validation helpers...")
    
    # Valid model
    valid_metadata = ContentMetadata(
        content_id="test-001",
        title="Test Content",
        content_type=ContentType.STUDY_GUIDE,
        certification_type=CertificationType.GENERAL,
        category="Test"
    )
    
    # Should not raise exception
    try:
        validate_model(valid_metadata)
        print("✓ validate_model passed for valid model")
    except ValueError:
        assert False, "validate_model should not raise exception for valid model"
    
    # Invalid model
    invalid_metadata = ContentMetadata(
        content_id="",  # Invalid
        title="Test",
        content_type=ContentType.STUDY_GUIDE,
        certification_type=CertificationType.GENERAL,
        category="Test"
    )
    
    # Should raise exception
    try:
        validate_model(invalid_metadata)
        assert False, "validate_model should raise exception for invalid model"
    except ValueError:
        print("✓ validate_model correctly raised exception for invalid model")
    
    # Test validate_models
    models = [valid_metadata]
    try:
        validate_models(models)
        print("✓ validate_models passed for valid models")
    except ValueError:
        assert False, "validate_models should not raise exception for valid models"
    
    print("✓ Validation helper tests passed")


def main():
    """Run all tests."""
    print("Running data model tests...\n")
    
    try:
        test_content_metadata()
        test_question_answer()
        test_user_progress()
        test_vector_document()
        test_certification_detection()
        test_validation_helpers()
        
        print("\n🎉 All tests passed! The data models are working correctly.")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)