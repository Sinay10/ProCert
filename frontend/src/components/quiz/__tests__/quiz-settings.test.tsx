import { render, screen, fireEvent } from '@testing-library/react'
import { vi } from 'vitest'
import { QuizSettings } from '../quiz-settings'

describe('QuizSettings', () => {
  const mockOnStartQuiz = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders all form elements', () => {
    render(
      <QuizSettings
        onStartQuiz={mockOnStartQuiz}
        loading={false}
        error={null}
      />
    )

    expect(screen.getByText('Quiz Settings')).toBeInTheDocument()
    expect(screen.getByText('Certification')).toBeInTheDocument()
    expect(screen.getByText('Difficulty Level')).toBeInTheDocument()
    expect(screen.getByText('Number of Questions')).toBeInTheDocument()
    expect(screen.getByText('Start Quiz')).toBeInTheDocument()
  })

  it('has default values set correctly', () => {
    render(
      <QuizSettings
        onStartQuiz={mockOnStartQuiz}
        loading={false}
        error={null}
      />
    )

    const certificationSelect = screen.getByDisplayValue('AWS Cloud Practitioner')
    expect(certificationSelect).toBeInTheDocument()

    const mixedDifficulty = screen.getByDisplayValue('mixed')
    expect(mixedDifficulty).toBeChecked()

    const tenQuestions = screen.getByRole('button', { name: '10' })
    expect(tenQuestions).toHaveClass('bg-primary-600')
  })

  it('uses initial certification when provided', () => {
    render(
      <QuizSettings
        onStartQuiz={mockOnStartQuiz}
        loading={false}
        error={null}
        initialCertification="aws-solutions-architect-associate"
      />
    )

    const certificationSelect = screen.getByDisplayValue('AWS Solutions Architect Associate')
    expect(certificationSelect).toBeInTheDocument()
  })

  it('allows changing certification', () => {
    render(
      <QuizSettings
        onStartQuiz={mockOnStartQuiz}
        loading={false}
        error={null}
      />
    )

    const certificationSelect = screen.getByRole('combobox')
    fireEvent.change(certificationSelect, { target: { value: 'aws-developer-associate' } })

    expect(screen.getByDisplayValue('AWS Developer Associate')).toBeInTheDocument()
  })

  it('allows changing difficulty level', () => {
    render(
      <QuizSettings
        onStartQuiz={mockOnStartQuiz}
        loading={false}
        error={null}
      />
    )

    const beginnerOption = screen.getByDisplayValue('beginner')
    fireEvent.click(beginnerOption)

    expect(beginnerOption).toBeChecked()
  })

  it('allows changing question count', () => {
    render(
      <QuizSettings
        onStartQuiz={mockOnStartQuiz}
        loading={false}
        error={null}
      />
    )

    const fifteenQuestions = screen.getByRole('button', { name: '15' })
    fireEvent.click(fifteenQuestions)

    expect(fifteenQuestions).toHaveClass('bg-primary-600')
  })

  it('shows estimated time based on question count', () => {
    render(
      <QuizSettings
        onStartQuiz={mockOnStartQuiz}
        loading={false}
        error={null}
      />
    )

    // Default 10 questions = 15 minutes
    expect(screen.getByText('Estimated time: 15 minutes')).toBeInTheDocument()

    const twentyQuestions = screen.getByRole('button', { name: '20' })
    fireEvent.click(twentyQuestions)

    // 20 questions = 30 minutes
    expect(screen.getByText('Estimated time: 30 minutes')).toBeInTheDocument()
  })

  it('calls onStartQuiz with correct settings when form is submitted', () => {
    render(
      <QuizSettings
        onStartQuiz={mockOnStartQuiz}
        loading={false}
        error={null}
      />
    )

    // Change settings
    const certificationSelect = screen.getByRole('combobox')
    fireEvent.change(certificationSelect, { target: { value: 'aws-developer-associate' } })

    const advancedOption = screen.getByDisplayValue('advanced')
    fireEvent.click(advancedOption)

    const fifteenQuestions = screen.getByRole('button', { name: '15' })
    fireEvent.click(fifteenQuestions)

    // Submit form
    const startButton = screen.getByText('Start Quiz')
    fireEvent.click(startButton)

    expect(mockOnStartQuiz).toHaveBeenCalledWith({
      certification: 'aws-developer-associate',
      difficulty: 'advanced',
      count: 15
    })
  })

  it('shows loading state', () => {
    render(
      <QuizSettings
        onStartQuiz={mockOnStartQuiz}
        loading={true}
        error={null}
      />
    )

    const startButton = screen.getByText('Start Quiz')
    expect(startButton).toBeDisabled()
  })

  it('displays error message', () => {
    const errorMessage = 'Failed to generate quiz'
    render(
      <QuizSettings
        onStartQuiz={mockOnStartQuiz}
        loading={false}
        error={errorMessage}
      />
    )

    expect(screen.getByText(errorMessage)).toBeInTheDocument()
  })

  it('prevents form submission when loading', () => {
    render(
      <QuizSettings
        onStartQuiz={mockOnStartQuiz}
        loading={true}
        error={null}
      />
    )

    const startButton = screen.getByText('Start Quiz')
    fireEvent.click(startButton)

    expect(mockOnStartQuiz).not.toHaveBeenCalled()
  })
})