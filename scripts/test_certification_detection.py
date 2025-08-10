#!/usr/bin/env python3
"""
Test script to demonstrate certification detection scenarios.
"""

def simulate_detection(bucket_name: str, filename: str, content_keywords: list) -> dict:
    """Simulate the certification detection logic."""
    
    # Step 1: S3 Context Detection
    cert_from_bucket = 'GENERAL'
    if 'ccp' in bucket_name.lower():
        cert_from_bucket = 'CCP'
    elif 'dva' in bucket_name.lower():
        cert_from_bucket = 'DVA'
    elif 'saa' in bucket_name.lower():
        cert_from_bucket = 'SAA'
    elif 'soa' in bucket_name.lower():
        cert_from_bucket = 'SOA'
    # ... other certifications
    
    # Step 2: Filename Detection
    cert_from_filename = 'GENERAL'
    filename_upper = filename.upper()
    if filename_upper.startswith('DVA-'):
        cert_from_filename = 'DVA'
    elif filename_upper.startswith('SAA-'):
        cert_from_filename = 'SAA'
    elif filename_upper.startswith('CCP-'):
        cert_from_filename = 'CCP'
    # ... other patterns
    
    # Step 3: Content Analysis
    cert_from_content = 'GENERAL'
    content_text = ' '.join(content_keywords).upper()
    if 'DEVELOPER ASSOCIATE' in content_text or 'DVA-C02' in content_text:
        cert_from_content = 'DVA'
    elif 'CLOUD PRACTITIONER' in content_text or 'CLF-C02' in content_text:
        cert_from_content = 'CCP'
    elif 'SOLUTIONS ARCHITECT' in content_text or 'SAA-C03' in content_text:
        cert_from_content = 'SAA'
    # ... other patterns
    
    # Current Logic: S3 context wins unless it's GENERAL
    current_logic = cert_from_bucket if cert_from_bucket != 'GENERAL' else cert_from_content
    
    # Improved Logic: Consider conflicts
    improved_logic = current_logic
    if cert_from_bucket != 'GENERAL' and cert_from_content != 'GENERAL':
        if cert_from_bucket != cert_from_content:
            # Conflict detected - use content analysis as it's more reliable
            improved_logic = cert_from_content
    
    return {
        'bucket_detection': cert_from_bucket,
        'filename_detection': cert_from_filename,
        'content_detection': cert_from_content,
        'current_result': current_logic,
        'improved_result': improved_logic,
        'has_conflict': cert_from_bucket != 'GENERAL' and cert_from_content != 'GENERAL' and cert_from_bucket != cert_from_content
    }

def main():
    """Test various scenarios."""
    print("🧪 Certification Detection Test Scenarios")
    print("=" * 60)
    
    scenarios = [
        {
            'name': 'Correct Upload',
            'bucket': 'procert-materials-dva-353207798766',
            'filename': 'DVA-practice-exam.pdf',
            'content': ['AWS Certified Developer Associate', 'DVA-C02']
        },
        {
            'name': 'Wrong Bucket (DVA content in CCP bucket)',
            'bucket': 'procert-materials-ccp-353207798766',
            'filename': 'DVA-practice-exam.pdf',
            'content': ['AWS Certified Developer Associate', 'DVA-C02']
        },
        {
            'name': 'Generic Filename (DVA content in General bucket)',
            'bucket': 'procert-materials-general-353207798766',
            'filename': 'aws-practice-exam.pdf',
            'content': ['AWS Certified Developer Associate', 'DVA-C02']
        },
        {
            'name': 'Ambiguous Content',
            'bucket': 'procert-materials-saa-353207798766',
            'filename': 'general-aws-guide.pdf',
            'content': ['AWS services', 'cloud computing']
        }
    ]
    
    for scenario in scenarios:
        print(f"\n📋 Scenario: {scenario['name']}")
        print("-" * 40)
        print(f"Bucket: {scenario['bucket']}")
        print(f"File: {scenario['filename']}")
        print(f"Content: {scenario['content']}")
        
        result = simulate_detection(
            scenario['bucket'],
            scenario['filename'], 
            scenario['content']
        )
        
        print(f"\n🔍 Detection Results:")
        print(f"  Bucket → {result['bucket_detection']}")
        print(f"  Filename → {result['filename_detection']}")
        print(f"  Content → {result['content_detection']}")
        print(f"  Current Logic → {result['current_result']}")
        print(f"  Improved Logic → {result['improved_result']}")
        
        if result['has_conflict']:
            print(f"  ⚠️  CONFLICT DETECTED!")
            if result['current_result'] != result['improved_result']:
                print(f"  💡 Improved logic would fix this")
        else:
            print(f"  ✅ No conflicts")
        
        print()

if __name__ == "__main__":
    main()