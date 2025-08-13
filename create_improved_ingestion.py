#!/usr/bin/env python3
"""
Create an improved version of the question extraction function and update the ingestion Lambda.
"""

def create_improved_extraction_function():
    """Create the improved question extraction function code."""
    
    improved_function = '''
def extract_questions_and_answers(text: str, certification_type: str) -> List[Dict[str, Any]]:
    """
    Extract questions and answers from content with certification context.
    Enhanced to handle AWS sample questions format.
    
    Args:
        text: Document text content
        certification_type: Detected certification type for context
        
    Returns:
        List of question-answer dictionaries
    """
    questions = []
    
    # AWS Sample Questions Format Pattern
    # Matches: number) question text... A) option B) option C) option D) option
    aws_pattern = r'(\\d+)\\)\\s*(.+?)(?=\\s*A\\))\\s*A\\)\\s*(.+?)(?=\\s*B\\))\\s*B\\)\\s*(.+?)(?=\\s*C\\))\\s*C\\)\\s*(.+?)(?=\\s*D\\))\\s*D\\)\\s*(.+?)(?=\\s*(?:\\d+\\)|Answer:|Domain:|$))'
    
    print(f"Extracting questions using AWS format pattern...")
    matches = re.finditer(aws_pattern, text, re.MULTILINE | re.DOTALL | re.IGNORECASE)
    
    for match in matches:
        try:
            question_number = match.group(1).strip()
            question_text = match.group(2).strip()
            option_a = match.group(3).strip()
            option_b = match.group(4).strip()
            option_c = match.group(5).strip()
            option_d = match.group(6).strip()
            
            # Clean up question text - find the actual question
            question_lines = question_text.split('\\n')
            clean_question = ""
            for line in question_lines:
                line = line.strip()
                if line:
                    clean_question += line + " "
            
            clean_question = clean_question.strip()
            
            # Ensure question ends with a question mark or add context
            if not clean_question.endswith('?'):
                # Look for question indicators
                question_indicators = ['Which', 'What', 'How', 'Where', 'When', 'Why']
                last_sentence = clean_question.split('.')[-1].strip()
                if any(indicator in last_sentence for indicator in question_indicators):
                    clean_question = last_sentence + "?"
                else:
                    clean_question += " Which solution will meet these requirements?"
            
            # Clean up options
            options = []
            for opt in [option_a, option_b, option_c, option_d]:
                clean_opt = ' '.join(opt.split())  # Remove extra whitespace
                if clean_opt:
                    options.append(clean_opt)
            
            if len(options) >= 4 and len(clean_question) > 20:
                question_data = {
                    'question_text': clean_question,
                    'answer_options': options,
                    'certification_type': certification_type,
                    'question_type': 'multiple_choice',
                    'extracted_by': 'aws_format_enhanced',
                    'question_number': question_number
                }
                questions.append(question_data)
                print(f"Extracted Q{question_number}: {clean_question[:100]}...")
                
        except (IndexError, AttributeError) as e:
            print(f"Error processing question match: {e}")
            continue
    
    # Fallback to original patterns if AWS pattern doesn't work
    if not questions:
        print("AWS pattern didn't match, trying fallback patterns...")
        
        # Original patterns for other formats
        fallback_patterns = [
            # Multiple choice patterns
            r'(?:Question\\s*\\d+[:\\.]?\\s*)?(.+?\\?)\\s*(?:\\n|\\r\\n?)\\s*(?:A[:\\.]\\s*(.+?)(?:\\n|\\r\\n?)\\s*B[:\\.]\\s*(.+?)(?:\\n|\\r\\n?)\\s*C[:\\.]\\s*(.+?)(?:\\n|\\r\\n?)\\s*D[:\\.]\\s*(.+?))',
            
            # Numbered question patterns
            r'(\\d+\\.\\s*.+?\\?)\\s*(?:\\n|\\r\\n?)\\s*(?:A[:\\.]\\s*(.+?)(?:\\n|\\r\\n?)\\s*B[:\\.]\\s*(.+?)(?:\\n|\\r\\n?)\\s*C[:\\.]\\s*(.+?)(?:\\n|\\r\\n?)\\s*D[:\\.]\\s*(.+?))',
        ]
        
        for i, pattern in enumerate(fallback_patterns):
            matches = re.finditer(pattern, text, re.MULTILINE | re.DOTALL | re.IGNORECASE)
            
            for match in matches:
                try:
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
                            'extracted_by': f'fallback_pattern_{i+1}'
                        }
                        questions.append(question_data)
                        
                except (IndexError, AttributeError) as e:
                    print(f"Error processing fallback question match: {e}")
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
'''
    
    return improved_function

def main():
    print("📝 Creating Improved Question Extraction Function...")
    
    improved_code = create_improved_extraction_function()
    
    print("✅ Improved extraction function created!")
    print("\nTo update the ingestion Lambda:")
    print("1. Replace the extract_questions_and_answers function in lambda_src/main.py")
    print("2. Redeploy the Lambda function")
    print("3. Re-run the ingestion process")
    
    # Save the improved function to a file
    with open('improved_extraction_function.py', 'w') as f:
        f.write(improved_code)
    
    print("\n💾 Saved improved function to 'improved_extraction_function.py'")

if __name__ == "__main__":
    main()