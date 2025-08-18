import { render, screen, fireEvent } from '@testing-library/react'
import { vi } from 'vitest'
import { QuizResults } from '../quiz-results'
import { QuizResult, QuizResponse } from '@/types/api'
import { it } from 'node:test'
import { it } from 'node:test'
import { it } from 'node:test'
import { it } from 'node:test'
import { it } from 'node:test'
import { it } from 'node:test'
import { it } from 'node:test'
import { it } from 'node:test'
import { it } from 'node:test'
import { it } from 'node:test'
import { it } from 'node:test'
import { beforeEach } from 'node:test'
import { describe } from 'node:test'

const mockQuiz: QuizResponse = {
  quiz_id: 'test-quiz-id',
  questions: [
    {
      question_id: 'q1',
      question_text: 'What is AWS Lambda?',
      options: ['Serverless compute', 'Database service', 'Storage service', 'Network service'],
      correct_answer: 'Serverless compute',
      explanation: 'AWS Lambda is a serverless compute service.'
    },
    {
      question_id: 'q2',
      question_text: 'What is Amazon S3?',
      options: ['Compute service', 'Storage service', 'Database service', 'Network service'],
      correct_answer: 'Storage service',
      explanation: 'Amazon S3 is an object storage service.'
    }
  ],
  metadata: {
    certification: 'aws-cloud-practitioner',
    difficulty: 'beginner',
    estimated_time: 10
  }
}

const mockResult: QuizResult = {
  score: 75,
  results: [
    {
      question_id: 'q1',
      correct: true,
      user_answer: 'Serverless compute',
      correct_answer: 'Serverless compute'
    },
    {
      question_id: 'q2',
      correct: false,
      user_answer: 'Database service',
      correct_answer: 'Storage service'
    }
  ],
  feedback: [
    {
      question_id: 'q1',
      explanation: 'AWS Lambda is a serverless compute service.',
      additional_resources: ['AWS Lambda Documentation']
    },
    {
      question_id: 'q2',
      explanation: 'Amazon S3 is an object storage service.',
      additional_resources: ['Amazon S3 User Guide']
    }
  ]
}

const mockUserAnswers = ['Serverless compute', 'Database service']

describe('QuizResults', () => {
  const mockOnRetakeQuiz = vi.fn()
  const mockOnViewHistory = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('displays overall score and performance', () => {
    render(
      <QuizResults
        result={mockResult}
        quiz={mockQuiz}
        userAnswers={mockUserAnswers}
        onRetakeQuiz={mockOnRetakeQuiz}
        onViewHistory={mockOnViewHistory}
      />
    )

    expect(screen.getByText('Quiz Complete!')).toBeInTheDocument()
    expect(screen.getByText('75%')).toBeInTheDocument()
    expect(screen.getByText('1 out of 2 correct')).toBeInTheDocument()
  })

  it('shows appropriate performance message based on score', () => {
    // Test different score ranges
    const highScoreResult = { ...mockResult, score: 95 }
    const { rerender } = render(
      <QuizResults
        result={highScoreResult}
        quiz={mockQuiz}
        userAnswers={mockUserAnswers}
        onRetakeQuiz={mockOnRetakeQuiz}
        onViewHistory={mockOnViewHistory}
      />
    )

    expect(screen.getByText(/Excellent work!/)).toBeInTheDocument()

    const lowScoreResult = { ...mockResult, score: 45 }
    rerender(
      <QuizResults
        result={lowScoreResult}
        quiz={mockQuiz}
        userAnswers={mockUserAnswers}
        onRetakeQuiz={mockOnRetakeQuiz}
        onViewHistory={mockOnViewHistory}
      />
    )

    expect(screen.getByText(/Keep studying!/)).toBeInTheDocument()
  })

  it('displays quiz metadata', () => {
    render(
      <QuizResults
        result={mockResult}
        quiz={mockQuiz}
        userAnswers={mockUserAnswers}
        onRetakeQuiz={mockOnRetakeQuiz}
        onViewHistory={mockOnViewHistory}
      />
    )

    expect(screen.getByText('Quiz Details')).toBeInTheDocument()
    expect(screen.getByText('aws-cloud-practitioner')).toBeInTheDocument()
    expect(screen.getByText('beginner')).toBeInTheDocument()
    expect(screen.getByText('2')).toBeInTheDocument()
  })

  it('shows question-by-question review', () => {
    render(
      <QuizResults
        result={mockResult}
        quiz={mockQuiz}
        userAnswers={mockUserAnswers}
        onRetakeQuiz={mockOnRetakeQuiz}
        onViewHistory={mockOnViewHistory}
      />
    )

    expect(screen.getByText('Question Review')).toBeInTheDocument()
    
    // Check first question (correct)
    expect(screen.getByText('Question 1')).toBeInTheDocument()
    expect(screen.getByText('What is AWS Lambda?')).toBeInTheDocument()
    expect(screen.getByText('Correct')).toBeInTheDocument()
    
    // Check second question (incorrect)
    expect(screen.getByText('Question 2')).toBeInTheDocument()
    expect(screen.getByText('What is Amazon S3?')).toBeInTheDocument()
    expect(screen.getByText('Incorrect')).toBeInTheDocument()
  })

  it('shows user answers and correct answers', () => {
    render(
      <QuizResults
        result={mockResult}
        quiz={mockQuiz}
        userAnswers={mockUserAnswers}
        onRetakeQuiz={mockOnRetakeQuiz}
        onViewHistory={mockOnViewHistory}
      />
    )

    // Check user answers are displayed
    expect(screen.getByText('Serverless compute')).toBeInTheDocument()
    expect(screen.getByText('Database service')).toBeInTheDocument()
    
    // Check correct answer is shown for incorrect question
    expect(screen.getByText('Storage service')).toBeInTheDocument()
  })

  it('displays explanations for each question', () => {
    render(
      <QuizResults
        result={mockResult}
        quiz={mockQuiz}
        userAnswers={mockUserAnswers}
        onRetakeQuiz={mockOnRetakeQuiz}
        onViewHistory={mockOnViewHistory}
      />
    )

    expect(screen.getByText('AWS Lambda is a serverless compute service.')).toBeInTheDocument()
    expect(screen.getByText('Amazon S3 is an object storage service.')).toBeInTheDocument()
  })

  it('shows additional resources when available', () => {
    render(
      <QuizResults
        result={mockResult}
        quiz={mockQuiz}
        userAnswers={mockUserAnswers}
        onRetakeQuiz={mockOnRetakeQuiz}
        onViewHistory={mockOnViewHistory}
      />
    )

    expect(screen.getAllByText('Additional Resources:')).toHaveLength(2)
    expect(screen.getByText('AWS Lambda Documentation')).toBeInTheDocument()
    expect(screen.getByText('Amazon S3 User Guide')).toBeInTheDocument()
  })

  it('calls onRetakeQuiz when Take Another Quiz is clicked', () => {
    render(
      <QuizResults
        result={mockResult}
        quiz={mockQuiz}
        userAnswers={mockUserAnswers}
        onRetakeQuiz={mockOnRetakeQuiz}
        onViewHistory={mockOnViewHistory}
      />
    )

    const retakeButton = screen.getByText('Take Another Quiz')
    fireEvent.click(retakeButton)

    expect(mockOnRetakeQuiz).toHaveBeenCalledTimes(1)
  })

  it('calls onViewHistory when View History is clicked', () => {
    render(
      <QuizResults
        result={mockResult}
        quiz={mockQuiz}
        userAnswers={mockUserAnswers}
        onRetakeQuiz={mockOnRetakeQuiz}
        onViewHistory={mockOnViewHistory}
      />
    )

    const historyButton = screen.getByText('View History')
    fireEvent.click(historyButton)

    expect(mockOnViewHistory).toHaveBeenCalledTimes(1)
  })

  it('applies correct styling for correct and incorrect answers', () => {
    render(
      <QuizResults
        result={mockResult}
        quiz={mockQuiz}
        userAnswers={mockUserAnswers}
        onRetakeQuiz={mockOnRetakeQuiz}
        onViewHistory={mockOnViewHistory}
      />
    )

    // Find the question containers by their styling classes
    const successContainer = document.querySelector('.border-success-200.bg-success-50')
    const errorContainer = document.querySelector('.border-error-200.bg-error-50')

    // Check that both containers exist
    expect(successContainer).toBeInTheDocument()
    expect(errorContainer).toBeInTheDocument()
  })

  it('uses appropriate score colors based on performance', () => {
    const { rerender } = render(
      <QuizResults
        result={{ ...mockResult, score: 90 }}
        quiz={mockQuiz}
        userAnswers={mockUserAnswers}
        onRetakeQuiz={mockOnRetakeQuiz}
        onViewHistory={mockOnViewHistory}
      />
    )

    expect(screen.getByText('90%')).toHaveClass('text-success-600')

    rerender(
      <QuizResults
        result={{ ...mockResult, score: 65 }}
        quiz={mockQuiz}
        userAnswers={mockUserAnswers}
        onRetakeQuiz={mockOnRetakeQuiz}
        onViewHistory={mockOnViewHistory}
      />
    )

    expect(screen.getByText('65%')).toHaveClass('text-warning-600')

    rerender(
      <QuizResults
        result={{ ...mockResult, score: 45 }}
        quiz={mockQuiz}
        userAnswers={mockUserAnswers}
        onRetakeQuiz={mockOnRetakeQuiz}
        onViewHistory={mockOnViewHistory}
      />
    )

    expect(screen.getByText('45%')).toHaveClass('text-error-600')
  })
})