#!/usr/bin/env python3
"""
Download and examine the content of the ANS sample questions PDF to understand its structure.
"""

import boto3
import json
from pypdf import PdfReader
import io

def examine_pdf_content():
    """Download and examine PDF content."""
    print("📄 Examining ANS Sample Questions PDF Content...")
    
    s3_client = boto3.client('s3')
    
    # Get the ANS bucket
    buckets = s3_client.list_buckets()
    ans_bucket = None
    
    for bucket in buckets['Buckets']:
        bucket_name = bucket['Name']
        if 'ans' in bucket_name.lower() and 'procert' in bucket_name.lower():
            ans_bucket = bucket_name
            break
    
    if not ans_bucket:
        print("❌ ANS bucket not found!")
        return
    
    print(f"Found ANS bucket: {ans_bucket}")
    
    # Download the sample questions PDF
    sample_file = "AWS-Certified-Advanced-Networking-Specialty_Sample-Questions.pdf"
    
    try:
        print(f"Downloading {sample_file}...")
        response = s3_client.get_object(Bucket=ans_bucket, Key=sample_file)
        pdf_content = response['Body'].read()
        
        print(f"Downloaded {len(pdf_content)} bytes")
        
        # Parse the PDF
        pdf_reader = PdfReader(io.BytesIO(pdf_content))
        print(f"PDF has {len(pdf_reader.pages)} pages")
        
        # Extract text from all pages
        full_text = ""
        for i, page in enumerate(pdf_reader.pages):
            page_text = page.extract_text()
            full_text += page_text + "\n"
            print(f"Page {i+1}: {len(page_text)} characters")
        
        print(f"\nTotal text length: {len(full_text)} characters")
        
        # Show first 2000 characters to understand the format
        print(f"\n📋 First 2000 characters of the PDF:")
        print("=" * 80)
        print(full_text[:2000])
        print("=" * 80)
        
        # Look for question patterns
        import re
        
        # Try to find questions using different patterns
        patterns = [
            r'Question\s*\d+',
            r'\d+\.\s*[A-Z]',
            r'[A-D]\)\s*',
            r'[A-D]\.\s*',
            r'\?\s*\n',
            r'Which\s+of\s+the\s+following',
            r'What\s+is\s+the',
            r'How\s+would\s+you'
        ]
        
        print(f"\n🔍 Pattern Analysis:")
        for pattern in patterns:
            matches = re.findall(pattern, full_text, re.IGNORECASE)
            print(f"   '{pattern}': {len(matches)} matches")
            if matches and len(matches) <= 10:
                print(f"      Examples: {matches[:3]}")
        
        # Look for specific sections
        sections = ['Question', 'Answer', 'Explanation', 'Domain', 'Subdomain']
        print(f"\n📋 Section Analysis:")
        for section in sections:
            count = full_text.lower().count(section.lower())
            print(f"   '{section}': appears {count} times")
        
        # Try to identify the actual question format by looking at line breaks
        lines = full_text.split('\n')
        print(f"\n📋 Line Analysis (first 50 lines):")
        for i, line in enumerate(lines[:50]):
            if line.strip():
                print(f"   {i+1:2d}: {line.strip()[:100]}")
        
    except Exception as e:
        print(f"❌ Error examining PDF: {e}")

if __name__ == "__main__":
    examine_pdf_content()