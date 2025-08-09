"""
Example of how admin upload with certification selection would work.

This shows how an admin interface could handle document uploads with 
certification type selection.
"""

import json
from typing import Dict, Any, Optional
from shared import (
    ContentMetadata, ContentType, CertificationType,
    detect_certification_from_filename, get_certifications_for_dropdown,
    validate_certification_code, get_certification_display_name
)


def admin_upload_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for admin document uploads with certification selection.
    
    Expected event structure:
    {
        "body": {
            "filename": "SAA-practice-exam.pdf",
            "admin_selected_certification": "SAA",  # Optional override
            "content_type": "PRACTICE_EXAM",
            "title": "Solutions Architect Practice Exam",
            "category": "Practice Tests"
        }
    }
    """
    try:
        # Parse request body
        if isinstance(event.get("body"), str):
            body = json.loads(event["body"])
        else:
            body = event.get("body", {})
        
        filename = body.get("filename")
        admin_certification = body.get("admin_selected_certification")
        content_type_str = body.get("content_type", "STUDY_GUIDE")
        title = body.get("title")
        category = body.get("category", "General")
        
        if not filename:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "filename is required"})
            }
        
        # Detect certification type (admin override takes precedence)
        detected_cert = detect_certification_from_filename(filename, admin_certification)
        
        # Validate admin selection if provided
        if admin_certification and not validate_certification_code(admin_certification):
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "error": f"Invalid certification code: {admin_certification}",
                    "valid_codes": [cert["code"] for cert in get_certifications_for_dropdown()]
                })
            }
        
        # Create content metadata
        content_id = f"content-{filename.replace('.', '-').replace('/', '-')}"
        
        try:
            content_type = ContentType(content_type_str)
        except ValueError:
            content_type = ContentType.STUDY_GUIDE
        
        metadata = ContentMetadata(
            content_id=content_id,
            title=title or filename,
            content_type=content_type,
            certification_type=detected_cert,
            category=category,
            source_file=filename
        )
        
        # Validate metadata
        if not metadata.is_valid():
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "error": "Invalid metadata",
                    "details": metadata.validate()
                })
            }
        
        # Success response with detected/selected certification
        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Document classification successful",
                "content_id": content_id,
                "detected_certification": {
                    "code": detected_cert.value,
                    "name": get_certification_display_name(detected_cert)
                },
                "filename_detection": detect_certification_from_filename(filename).value,
                "admin_override": admin_certification,
                "metadata": metadata.to_dict()
            })
        }
        
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Internal server error",
                "details": str(e)
            })
        }


def get_certification_options_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler to get certification options for admin dropdown.
    
    Returns all available certifications grouped by level.
    """
    try:
        certifications = get_certifications_for_dropdown()
        
        # Group by level for better UI organization
        grouped = {}
        for cert in certifications:
            level = cert["level"]
            if level not in grouped:
                grouped[level] = []
            grouped[level].append({
                "code": cert["code"],
                "name": cert["name"]
            })
        
        return {
            "statusCode": 200,
            "body": json.dumps({
                "certifications": certifications,
                "grouped_by_level": grouped
            })
        }
        
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Failed to get certification options",
                "details": str(e)
            })
        }


# Example usage and testing
if __name__ == "__main__":
    # Test automatic detection
    test_cases = [
        {
            "filename": "SAA-practice-exam.pdf",
            "admin_override": None,
            "expected": "SAA"
        },
        {
            "filename": "random-document.pdf",
            "admin_override": None,
            "expected": "GENERAL"
        },
        {
            "filename": "random-document.pdf",
            "admin_override": "CCP",
            "expected": "CCP"
        },
        {
            "filename": "DVA-study-guide.pdf",
            "admin_override": "SAA",  # Admin override should win
            "expected": "SAA"
        }
    ]
    
    print("Testing certification detection...")
    for i, case in enumerate(test_cases):
        result = detect_certification_from_filename(
            case["filename"], 
            case["admin_override"]
        )
        expected = CertificationType(case["expected"])
        
        if result == expected:
            print(f"✓ Test {i+1}: {case['filename']} -> {result.value}")
        else:
            print(f"✗ Test {i+1}: Expected {expected.value}, got {result.value}")
    
    # Test dropdown options
    print("\nAvailable certifications for dropdown:")
    options = get_certifications_for_dropdown()
    for opt in options:
        print(f"  {opt['code']}: {opt['name']} ({opt['level']})")