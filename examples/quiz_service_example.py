"""
Example usage of the Quiz Generation Service.

This script demonstrates how to use the quiz service for generating quizzes,
submitting answers, and tracking user progress.
"""

import json
import requests
import time
from typing import Dict, Any, List


class QuizServiceExample:
    """Example client for the Quiz Generation Service."""
    
    def __init__(self, api_base_url: str, auth_token: str):
        """
        Initialize the quiz service client.
        
        Args:
            api_base_url: Base URL of the API Gateway
            auth_token: JWT authentication token
        """
        self.api_base_url = api_base_url.rstrip('/')
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {auth_token}'
        }
    
    def generate_quiz(self, user_id: str, certification_type: str, 
                     question_count: int = 10, difficulty: str = "mixed") -> Dict[str, Any]:
        """
        Generate a new quiz for a user.
        
        Args:
            user_id: User identifier
            certification_type: Certification type (e.g., 'SAA', 'DVA')
            question_count: Number of questions (1-50)
            difficulty: Difficulty preference ('easy', 'medium', 'hard', 'mixed')
            
        Returns:
            Quiz session data
        """
        url = f"{self.api_base_url}/quiz/generate"
        payload = {
            'user_id': user_id,
            'certification_type': certification_type,
            'question_count': question_count,
            'difficulty': difficulty
        }
        
        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        
        return response.json()
    
    def submit_quiz(self, quiz_id: str, answers: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Submit quiz answers and get results.
        
        Args:
            quiz_id: Quiz session identifier
            answers: List of answers with question_id and selected_answer
            
        Returns:
            Quiz results with score and feedback
        """
        url = f"{self.api_base_url}/quiz/submit"
        payload = {
            'quiz_id': quiz_id,
            'answers': answers
        }
        
        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        
        return response.json()
    
    def get_quiz_history(self, user_id: str, limit: int = 20) -> Dict[str, Any]:
        """
        Get user's quiz history.
        
        Args:
            user_id: User identifier
            limit: Maximum number of quizzes to return
            
        Returns:
            Quiz history data
        """
        url = f"{self.api_base_url}/quiz/history/{user_id}"
        params = {'limit': limit}
        
        response = requests.get(url, params=params, headers=self.headers)
        response.raise_for_status()
        
        return response.json()
    
    def get_quiz_details(self, quiz_id: str) -> Dict[str, Any]:
        """
        Get details of a specific quiz.
        
        Args:
            quiz_id: Quiz session identifier
            
        Returns:
            Quiz details
        """
        url = f"{self.api_base_url}/quiz/{quiz_id}"
        
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        
        return response.json()


def demonstrate_quiz_workflow():
    """Demonstrate a complete quiz workflow."""
    # Configuration (replace with actual values)
    API_BASE_URL = "https://your-api-gateway-url.amazonaws.com/prod"
    AUTH_TOKEN = "your-jwt-token-here"
    USER_ID = "demo-user-123"
    CERTIFICATION_TYPE = "SAA"
    
    # Initialize client
    client = QuizServiceExample(API_BASE_URL, AUTH_TOKEN)
    
    print("🎯 Quiz Generation Service Demo")
    print("=" * 50)
    
    try:
        # Step 1: Generate a quiz
        print("\n📝 Step 1: Generating quiz...")
        quiz_response = client.generate_quiz(
            user_id=USER_ID,
            certification_type=CERTIFICATION_TYPE,
            question_count=5,
            difficulty="mixed"
        )
        
        quiz = quiz_response['quiz']
        quiz_id = quiz['quiz_id']
        questions = quiz['questions']
        
        print(f"✅ Quiz generated successfully!")
        print(f"   Quiz ID: {quiz_id}")
        print(f"   Questions: {len(questions)}")
        print(f"   Certification: {quiz['certification_type']}")
        
        # Display questions
        print("\n📋 Quiz Questions:")
        for i, question in enumerate(questions, 1):
            print(f"\n{i}. {question['question_text']}")
            for j, option in enumerate(question['options'], 1):
                print(f"   {j}) {option}")
        
        # Step 2: Simulate user answers
        print("\n✏️  Step 2: Submitting answers...")
        answers = []
        
        for question in questions:
            # For demo, select first option for each question
            selected_answer = question['options'][0] if question['options'] else ""
            answers.append({
                'question_id': question['question_id'],
                'selected_answer': selected_answer
            })
        
        # Submit answers
        results_response = client.submit_quiz(quiz_id, answers)
        results = results_response['results']
        
        print(f"✅ Quiz submitted successfully!")
        print(f"   Score: {results['score']:.1f}%")
        print(f"   Correct: {results['correct_answers']}/{results['total_questions']}")
        print(f"   Grade: {results['performance_summary'].get('grade', 'N/A')}")
        
        # Display detailed results
        print("\n📊 Detailed Results:")
        for result in results['results']:
            status = "✅ Correct" if result['is_correct'] else "❌ Incorrect"
            print(f"\n{status}: {result['question_text']}")
            print(f"   Your answer: {result['user_answer']}")
            print(f"   Correct answer: {result['correct_answer']}")
            if result.get('explanation'):
                print(f"   Explanation: {result['explanation']}")
        
        # Step 3: Get quiz history
        print("\n📚 Step 3: Getting quiz history...")
        history_response = client.get_quiz_history(USER_ID, limit=5)
        quiz_history = history_response['quiz_history']
        
        print(f"✅ Found {len(quiz_history)} recent quizzes:")
        for quiz in quiz_history:
            status = quiz.get('status', 'unknown')
            score = quiz.get('score', 'N/A')
            cert_type = quiz.get('certification_type', 'N/A')
            started_at = quiz.get('started_at', 'N/A')
            
            print(f"   • {cert_type} quiz - Score: {score}% - Status: {status}")
            print(f"     Started: {started_at}")
        
        # Step 4: Demonstrate adaptive selection
        print("\n🧠 Step 4: Demonstrating adaptive selection...")
        print("Generating another quiz to show adaptive question selection...")
        
        adaptive_quiz_response = client.generate_quiz(
            user_id=USER_ID,
            certification_type=CERTIFICATION_TYPE,
            question_count=3,
            difficulty="mixed"
        )
        
        adaptive_quiz = adaptive_quiz_response['quiz']
        print(f"✅ Adaptive quiz generated!")
        print(f"   Quiz ID: {adaptive_quiz['quiz_id']}")
        print(f"   Questions: {len(adaptive_quiz['questions'])}")
        
        # Check if metadata indicates adaptive selection was used
        metadata = adaptive_quiz.get('metadata', {})
        if metadata.get('adaptive_selection'):
            print("   🎯 Adaptive selection was used based on your performance!")
            if metadata.get('user_performance_considered'):
                print("   📈 Your previous performance was considered")
        
        print("\n🎉 Quiz workflow demonstration completed!")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ API Error: {e}")
    except KeyError as e:
        print(f"❌ Response format error: Missing key {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def demonstrate_quiz_analytics():
    """Demonstrate quiz analytics and performance tracking."""
    print("\n📊 Quiz Analytics Demo")
    print("=" * 30)
    
    # This would typically involve calling additional analytics endpoints
    # For now, we'll show what kind of analytics could be derived
    
    sample_quiz_history = [
        {"certification_type": "SAA", "score": 85, "category_scores": {"storage": 90, "compute": 80}},
        {"certification_type": "SAA", "score": 78, "category_scores": {"storage": 85, "compute": 70}},
        {"certification_type": "DVA", "score": 92, "category_scores": {"lambda": 95, "api_gateway": 88}},
    ]
    
    print("Sample Performance Analytics:")
    
    # Calculate overall performance
    total_score = sum(quiz['score'] for quiz in sample_quiz_history)
    avg_score = total_score / len(sample_quiz_history)
    
    print(f"   Overall Average Score: {avg_score:.1f}%")
    
    # Identify weak areas
    all_categories = {}
    for quiz in sample_quiz_history:
        for category, score in quiz.get('category_scores', {}).items():
            if category not in all_categories:
                all_categories[category] = []
            all_categories[category].append(score)
    
    print("\n   Category Performance:")
    weak_areas = []
    for category, scores in all_categories.items():
        avg_category_score = sum(scores) / len(scores)
        print(f"   • {category.title()}: {avg_category_score:.1f}%")
        
        if avg_category_score < 75:
            weak_areas.append(category)
    
    if weak_areas:
        print(f"\n   🎯 Recommended focus areas: {', '.join(weak_areas)}")
    else:
        print("\n   ✅ Strong performance across all categories!")


if __name__ == "__main__":
    print("Quiz Generation Service Example")
    print("This is a demonstration of the quiz service functionality.")
    print("\nTo run this example with real data:")
    print("1. Deploy the infrastructure with CDK")
    print("2. Update API_BASE_URL with your API Gateway URL")
    print("3. Obtain a valid JWT token for authentication")
    print("4. Update USER_ID and CERTIFICATION_TYPE as needed")
    
    print("\n" + "="*60)
    print("DEMO MODE - Showing expected workflow")
    print("="*60)
    
    # Run analytics demo (doesn't require API calls)
    demonstrate_quiz_analytics()
    
    print("\n" + "="*60)
    print("To run the full demo, uncomment the line below and provide valid credentials:")
    print("# demonstrate_quiz_workflow()")