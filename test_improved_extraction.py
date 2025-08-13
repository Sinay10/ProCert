#!/usr/bin/env python3
"""
Test improved question extraction patterns for AWS sample questions format.
"""

import re
from typing import List, Dict, Any

def extract_questions_improved(text: str, certification_type: str) -> List[Dict[str, Any]]:
    """
    Improved question extraction for AWS sample questions format.
    """
    questions = []
    
    # AWS sample questions format: numbered questions with A), B), C), D) options
    # Pattern to match: number) question text... A) option B) option C) option D) option
    pattern = r'(\d+\)\s*(.+?))\s*A\)\s*(.+?)\s*B\)\s*(.+?)\s*C\)\s*(.+?)\s*D\)\s*(.+?)(?=\d+\)|$)'
    
    # More flexible pattern for AWS format
    aws_pattern = r'(\d+\)\s*(.+?)(?=\s*A\)))\s*A\)\s*(.+?)(?=\s*B\))\s*B\)\s*(.+?)(?=\s*C\))\s*C\)\s*(.+?)(?=\s*D\))\s*D\)\s*(.+?)(?=\s*\d+\)|Answer:|$)'
    
    print(f"Testing question extraction patterns...")
    
    # Try the AWS-specific pattern
    matches = re.finditer(aws_pattern, text, re.MULTILINE | re.DOTALL | re.IGNORECASE)
    
    for match in matches:
        try:
            question_number = match.group(1).strip()
            question_text = match.group(2).strip()
            option_a = match.group(3).strip()
            option_b = match.group(4).strip()
            option_c = match.group(5).strip()
            option_d = match.group(6).strip()
            
            # Clean up the question text
            if question_text.endswith('?'):
                full_question = question_text
            else:
                # Look for the question part that ends with ?
                question_parts = question_text.split('?')
                if len(question_parts) > 1:
                    full_question = question_parts[0] + '?'
                else:
                    full_question = question_text
            
            options = [option_a, option_b, option_c, option_d]
            # Clean up options
            options = [opt.strip() for opt in options if opt.strip()]
            
            if len(options) >= 4 and len(full_question) > 20:
                question_data = {
                    'question_number': question_number,
                    'question_text': full_question,
                    'answer_options': options,
                    'certification_type': certification_type,
                    'question_type': 'multiple_choice',
                    'extracted_by': 'aws_format_pattern'
                }
                questions.append(question_data)
                print(f"Extracted question: {question_number} - {full_question[:100]}...")
                
        except (IndexError, AttributeError) as e:
            print(f"Error processing question match: {e}")
            continue
    
    print(f"Total questions extracted: {len(questions)}")
    return questions

def test_extraction_with_sample():
    """Test extraction with the sample text we got from the PDF."""
    
    sample_text = """
1) A gaming company is planning to launch a globally available game that is hosted in one AWS Region. 
The game backend is hosted on Amazon EC2 instances that are part of an Auto Scaling  group. The game 
uses the gRPC protocol for bidirectional streaming between game clients and the backend. The company 
needs to filter incoming traffic based on the source IP address to protect the game.  
 
Which solution will meet these requirements? 
 
A) Configure an AWS Global Accelerator accelerator with an Application Load Balancer (ALB) endpoint. 
Attach the ALB to the Auto Scaling group. Configure an AWS WAF web ACL for the ALB to filter traffic 
based on the source IP address. 
B) Configure an AWS Global Accelerator accelerator with a Network Load Balancer (NLB) endpoint. Attach 
the NLB to the Auto Scaling group. Configure security groups for the EC2 instances to filter traffic based 
on the source IP address. 
C) Configure an Amazon CloudFront distribution with an Application Load Balancer (ALB) endpoint. Attach 
the ALB to the Auto Scaling group. Configure an AWS WAF web ACL for the ALB to filter traffic based on 
the source IP address. 
D) Configure an Amazon CloudFront distribution with a Network Load Balancer (NLB) endpoint. Attach the 
NLB to the Auto Scaling group. Configure security groups for the EC2 instances to filter traffic based on 
the source IP address. 
 
2) A company has multiple VPCs in the us-east-1 Region. The company has deployed a website in one of 
the VPCs. The company wants to implement split-view DNS so that the website is accessible internally 
from the VPCs and externally over the internet with the same domain name, example.com.  
 
Which solution will meet these requirements? 
 
A) Change the DHCP options for each VPC to use the IP address of an on-premises DNS server. Create a 
private hosted zone and a public hosted zone for example.com. Map the private hosted zone to the 
website's internal IP address. Map the public hosted zone to the website's external IP address.
B) Create Amazon Route 53 private hosted zones and public hosted zones that have the same name, 
example.com. Associate the VPCs with the private hosted zone. Create records in each hosted zone that 
determine how traffic is routed.
C) Create an Amazon Route 53 Resolver inbound endpoint for resolving example.com internally. Create a 
Route 53 public hosted zone for routing external DNS queries.
D) Create an Amazon Route 53 Resolver outbound endpoint for resolving example.com externally. Create a 
Route 53 private hosted zone for routing internal DNS queries.
"""
    
    print("🧪 Testing Question Extraction with Sample Text...")
    questions = extract_questions_improved(sample_text, "ANS")
    
    print(f"\n📋 Extracted Questions:")
    for i, q in enumerate(questions, 1):
        print(f"\nQuestion {i}:")
        print(f"  Number: {q['question_number']}")
        print(f"  Text: {q['question_text']}")
        print(f"  Options: {len(q['answer_options'])}")
        for j, option in enumerate(q['answer_options']):
            print(f"    {chr(65+j)}) {option[:100]}...")

if __name__ == "__main__":
    test_extraction_with_sample()