#!/usr/bin/env python3
"""
Script to list all ProCert certification buckets and their purposes.
"""

import boto3
import json
from typing import Dict, List

def get_certification_info() -> Dict[str, Dict[str, str]]:
    """Get information about all AWS certifications and their buckets."""
    return {
        'general': {
            'name': 'General AWS Content',
            'level': 'Mixed',
            'description': 'General AWS content, mixed materials, or unspecified certification type',
            'bucket_suffix': 'general'
        },
        'ccp': {
            'name': 'AWS Certified Cloud Practitioner',
            'level': 'Foundational',
            'description': 'Entry-level certification covering basic AWS cloud concepts',
            'bucket_suffix': 'ccp'
        },
        'aip': {
            'name': 'AWS Certified AI Practitioner',
            'level': 'Foundational',
            'description': 'Foundational AI and machine learning concepts on AWS',
            'bucket_suffix': 'aip'
        },
        'saa': {
            'name': 'AWS Certified Solutions Architect Associate',
            'level': 'Associate',
            'description': 'Designing distributed systems and architectures on AWS',
            'bucket_suffix': 'saa'
        },
        'dva': {
            'name': 'AWS Certified Developer Associate',
            'level': 'Associate',
            'description': 'Developing and maintaining applications on AWS',
            'bucket_suffix': 'dva'
        },
        'soa': {
            'name': 'AWS Certified SysOps Administrator Associate',
            'level': 'Associate',
            'description': 'Operating and managing systems on AWS',
            'bucket_suffix': 'soa'
        },
        'mla': {
            'name': 'AWS Certified Machine Learning Engineer Associate',
            'level': 'Associate',
            'description': 'Implementing and maintaining ML solutions on AWS',
            'bucket_suffix': 'mla'
        },
        'dea': {
            'name': 'AWS Certified Data Engineer Associate',
            'level': 'Associate',
            'description': 'Designing and implementing data solutions on AWS',
            'bucket_suffix': 'dea'
        },
        'dop': {
            'name': 'AWS Certified DevOps Engineer Professional',
            'level': 'Professional',
            'description': 'Advanced DevOps practices and automation on AWS',
            'bucket_suffix': 'dop'
        },
        'sap': {
            'name': 'AWS Certified Solutions Architect Professional',
            'level': 'Professional',
            'description': 'Advanced architectural design and complex solutions on AWS',
            'bucket_suffix': 'sap'
        },
        'mls': {
            'name': 'AWS Certified Machine Learning Specialty',
            'level': 'Specialty',
            'description': 'Specialized machine learning implementations on AWS',
            'bucket_suffix': 'mls'
        },
        'scs': {
            'name': 'AWS Certified Security Specialty',
            'level': 'Specialty',
            'description': 'Specialized security implementations and best practices on AWS',
            'bucket_suffix': 'scs'
        },
        'ans': {
            'name': 'AWS Certified Advanced Networking Specialty',
            'level': 'Specialty',
            'description': 'Advanced networking concepts and implementations on AWS',
            'bucket_suffix': 'ans'
        }
    }

def get_account_id() -> str:
    """Get the current AWS account ID."""
    try:
        sts = boto3.client('sts')
        return sts.get_caller_identity()['Account']
    except Exception as e:
        print(f"Error getting account ID: {e}")
        return "UNKNOWN"

def list_existing_buckets() -> List[str]:
    """List existing ProCert buckets."""
    try:
        s3 = boto3.client('s3')
        response = s3.list_buckets()
        return [bucket['Name'] for bucket in response['Buckets'] if 'procert-materials' in bucket['Name']]
    except Exception as e:
        print(f"Error listing buckets: {e}")
        return []

def main():
    """Main function to display certification bucket information."""
    print("🎓 ProCert AWS Certification Buckets")
    print("=" * 60)
    
    account_id = get_account_id()
    existing_buckets = list_existing_buckets()
    cert_info = get_certification_info()
    
    print(f"AWS Account: {account_id}")
    print(f"Existing ProCert buckets: {len(existing_buckets)}")
    print()
    
    # Group by certification level
    levels = {
        'Mixed': [],
        'Foundational': [],
        'Associate': [],
        'Professional': [],
        'Specialty': []
    }
    
    for cert_code, info in cert_info.items():
        levels[info['level']].append((cert_code, info))
    
    # Display buckets by level
    for level, certs in levels.items():
        if not certs:
            continue
            
        print(f"\n📚 {level} Level Certifications:")
        print("-" * 40)
        
        for cert_code, info in certs:
            bucket_name = f"procert-materials-{info['bucket_suffix']}-{account_id}"
            exists = "✅" if bucket_name in existing_buckets else "❌"
            
            print(f"{exists} {cert_code.upper()}: {info['name']}")
            print(f"    Bucket: {bucket_name}")
            print(f"    Purpose: {info['description']}")
            print()
    
    # Upload instructions
    print("\n📤 How to Upload Documents:")
    print("-" * 30)
    print("AWS CLI:")
    print("  aws s3 cp your-document.pdf s3://procert-materials-[certification]-[account]/")
    print()
    print("Examples:")
    print(f"  aws s3 cp saa-practice-exam.pdf s3://procert-materials-saa-{account_id}/")
    print(f"  aws s3 cp general-aws-guide.pdf s3://procert-materials-general-{account_id}/")
    print()
    print("💡 Tip: The system will auto-detect certification type from:")
    print("   • Bucket name (primary)")
    print("   • Filename patterns (e.g., SAA-exam.pdf)")
    print("   • Document content analysis")

if __name__ == "__main__":
    main()