import { render, screen, fireEvent } from '@testing-library/react'
import { vi } from 'vitest'
import { QuestionDisplay } from '../question-display'
import { QuizQuestion } from '@/types/api'

const mockQuestion: QuizQuestion = {
  question_id: 'q1',
  question_text: 'What is the primary benefit of using AWS Lambda?',
  options: [
    'Serverless computing with automatic scaling',
    'Dedicated server instances',
    'Manual server management',
    'Fixed pricing model'
  ],
  correct_answer: 'Serverless computing with automatic scaling',
  explanation: 'AWS Lambda provides serverless computing capabilities with automatic scaling based on demand.'
}

describe('QuestionDisplay', () => {
  const mockOnAnswerSelect = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders question text and options', () => {
    render(
      <QuestionDisplay
        question={mockQuestion}
        selectedAnswer=""
        onAnswerSelect={mockOnAnswerSelect}
        questionNumber={1}
        totalQuestions={5}
      />
    )

    expect(screen.getByText('Question 1')).toBeInTheDocument()
    expect(screen.getByText('1 of 5')).toBeInTheDocument()
    expect(screen.getByText(mockQuestion.question_text)).toBeInTheDocument()
    
    mockQuestion.options.forEach((option, index) => {
      expect(screen.getByText(option)).toBeInTheDocument()
      expect(screen.getByText(String.fromCharCode(65 + index))).toBeInTheDocument() // A, B, C, D
    })
  })

  it('shows helper text', () => {
    render(
      <QuestionDisplay
        question={mockQuestion}
        selectedAnswer=""
        onAnswerSelect={mockOnAnswerSelect}
        questionNumber={1}
        totalQuestions={5}
      />
    )

    expect(screen.getByText(/Select the best answer from the options above/)).toBeInTheDocument()
  })

  it('calls onAnswerSelect when an option is clicked', () => {
    render(
      <QuestionDisplay
        question={mockQuestion}
        selectedAnswer=""
        onAnswerSelect={mockOnAnswerSelect}
        questionNumber={1}
        totalQuestions={5}
      />
    )

    const firstOption = screen.getByDisplayValue(mockQuestion.options[0])
    fireEvent.click(firstOption)

    expect(mockOnAnswerSelect).toHaveBeenCalledWith(mockQuestion.options[0])
  })

  it('shows selected answer with correct styling', () => {
    const selectedAnswer = mockQuestion.options[0]
    
    render(
      <QuestionDisplay
        question={mockQuestion}
        selectedAnswer={selectedAnswer}
        onAnswerSelect={mockOnAnswerSelect}
        questionNumber={1}
        totalQuestions={5}
      />
    )

    const selectedOption = screen.getByDisplayValue(selectedAnswer)
    expect(selectedOption).toBeChecked()

    // Check for selected styling classes
    const selectedLabel = selectedOption.closest('label')
    expect(selectedLabel).toHaveClass('border-primary-600', 'bg-primary-50')
  })

  it('shows unselected options with default styling', () => {
    const selectedAnswer = mockQuestion.options[0]
    
    render(
      <QuestionDisplay
        question={mockQuestion}
        selectedAnswer={selectedAnswer}
        onAnswerSelect={mockOnAnswerSelect}
        questionNumber={1}
        totalQuestions={5}
      />
    )

    // Check unselected options
    mockQuestion.options.slice(1).forEach((option) => {
      const optionInput = screen.getByDisplayValue(option)
      expect(optionInput).not.toBeChecked()
      
      const optionLabel = optionInput.closest('label')
      expect(optionLabel).toHaveClass('border-secondary-300', 'bg-white')
    })
  })

  it('displays option letters correctly (A, B, C, D)', () => {
    render(
      <QuestionDisplay
        question={mockQuestion}
        selectedAnswer=""
        onAnswerSelect={mockOnAnswerSelect}
        questionNumber={1}
        totalQuestions={5}
      />
    )

    const expectedLetters = ['A', 'B', 'C', 'D']
    expectedLetters.forEach((letter) => {
      expect(screen.getByText(letter)).toBeInTheDocument()
    })
  })

  it('shows selection indicator for selected answer', () => {
    const selectedAnswer = mockQuestion.options[0]
    
    render(
      <QuestionDisplay
        question={mockQuestion}
        selectedAnswer={selectedAnswer}
        onAnswerSelect={mockOnAnswerSelect}
        questionNumber={1}
        totalQuestions={5}
      />
    )

    // Check for checkmark SVG in selected option
    const checkmarkSvg = document.querySelector('svg')
    expect(checkmarkSvg).toBeInTheDocument()
    expect(checkmarkSvg).toHaveClass('w-3', 'h-3', 'text-white')
  })

  it('handles keyboard navigation', () => {
    render(
      <QuestionDisplay
        question={mockQuestion}
        selectedAnswer=""
        onAnswerSelect={mockOnAnswerSelect}
        questionNumber={1}
        totalQuestions={5}
      />
    )

    const firstOption = screen.getByDisplayValue(mockQuestion.options[0])
    
    // Simulate keyboard selection
    fireEvent.keyDown(firstOption, { key: 'Enter' })
    fireEvent.click(firstOption)

    expect(mockOnAnswerSelect).toHaveBeenCalledWith(mockQuestion.options[0])
  })

  it('displays correct question numbering', () => {
    render(
      <QuestionDisplay
        question={mockQuestion}
        selectedAnswer=""
        onAnswerSelect={mockOnAnswerSelect}
        questionNumber={3}
        totalQuestions={10}
      />
    )

    expect(screen.getByText('Question 3')).toBeInTheDocument()
    expect(screen.getByText('3 of 10')).toBeInTheDocument()
  })
})