import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { vi } from 'vitest'
import { useSession } from 'next-auth/react'
import { QuizHistory } from '../quiz-history'
import { apiClient } from '@/lib/api-client'
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
import { it } from 'node:test'
import { beforeEach } from 'node:test'
import { describe } from 'node:test'

// Mock dependencies
vi.mock('next-auth/react')
vi.mock('@/lib/api-client')

const mockUseSession = useSession as any
const mockApiClient = apiClient as any

const mockSession = {
  user: { email: 'test@example.com' },
  accessToken: 'mock-token',
  userId: 'test-user-id'
}

const mockHistoryResponse = {
  quizzes: [
    {
      quiz_id: 'quiz-1',
      certification: 'aws-cloud-practitioner',
      difficulty: 'beginner',
      score: 85,
      questions_count: 10,
      completed_at: '2024-01-15T10:30:00Z',
      time_taken: 900 // 15 minutes
    },
    {
      quiz_id: 'quiz-2',
      certification: 'aws-solutions-architect-associate',
      difficulty: 'intermediate',
      score: 72,
      questions_count: 15,
      completed_at: '2024-01-14T14:20:00Z',
      time_taken: 1200 // 20 minutes
    }
  ],
  statistics: {
    total_quizzes: 2,
    average_score: 78.5,
    best_score: 85,
    total_questions_answered: 25,
    by_certification: {
      'aws-cloud-practitioner': {
        count: 1,
        average_score: 85,
        best_score: 85
      },
      'aws-solutions-architect-associate': {
        count: 1,
        average_score: 72,
        best_score: 72
      }
    }
  }
}

describe('QuizHistory', () => {
  const mockOnStartNewQuiz = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    mockUseSession.mockReturnValue({
      data: mockSession,
      status: 'authenticated'
    })
  })

  it('shows loading state initially', () => {
    mockApiClient.get.mockImplementation(() => new Promise(() => {})) // Never resolves
    
    render(<QuizHistory onStartNewQuiz={mockOnStartNewQuiz} />)
    
    expect(screen.getByText('Loading quiz history...')).toBeInTheDocument()
    expect(document.querySelector('.loading-spinner')).toBeInTheDocument() // Loading spinner
  })

  it('displays performance overview when data is loaded', async () => {
    mockApiClient.get.mockResolvedValueOnce(mockHistoryResponse)
    
    render(<QuizHistory onStartNewQuiz={mockOnStartNewQuiz} />)
    
    await waitFor(() => {
      expect(screen.getByText('Performance Overview')).toBeInTheDocument()
      expect(screen.getByText('2')).toBeInTheDocument() // Total quizzes
      expect(screen.getByText('79%')).toBeInTheDocument() // Average score (rounded)
      expect(screen.getAllByText('85%')).toHaveLength(4) // Best score appears multiple times
      expect(screen.getByText('25')).toBeInTheDocument() // Total questions
    })
  })

  it('displays performance by certification', async () => {
    mockApiClient.get.mockResolvedValueOnce(mockHistoryResponse)
    
    render(<QuizHistory onStartNewQuiz={mockOnStartNewQuiz} />)
    
    await waitFor(() => {
      expect(screen.getByText('Performance by Certification')).toBeInTheDocument()
      expect(screen.getAllByText('aws cloud practitioner')).toHaveLength(2)
      expect(screen.getAllByText('aws solutions architect associate')).toHaveLength(2)
      expect(screen.getAllByText('1 quiz completed')).toHaveLength(2)
    })
  })

  it('displays recent quiz history', async () => {
    mockApiClient.get.mockResolvedValueOnce(mockHistoryResponse)
    
    render(<QuizHistory onStartNewQuiz={mockOnStartNewQuiz} />)
    
    await waitFor(() => {
      expect(screen.getByText('Recent Quizzes')).toBeInTheDocument()
      expect(screen.getAllByText('aws cloud practitioner')).toHaveLength(2)
      expect(screen.getAllByText('aws solutions architect associate')).toHaveLength(2)
      expect(screen.getByText('10 questions')).toBeInTheDocument()
      expect(screen.getByText('15 questions')).toBeInTheDocument()
      expect(screen.getByText('15 min')).toBeInTheDocument()
      expect(screen.getByText('20 min')).toBeInTheDocument()
    })
  })

  it('formats dates correctly', async () => {
    mockApiClient.get.mockResolvedValueOnce(mockHistoryResponse)
    
    render(<QuizHistory onStartNewQuiz={mockOnStartNewQuiz} />)
    
    await waitFor(() => {
      // Check that dates are formatted (exact format may vary by locale)
      expect(screen.getByText(/Jan 15, 2024/)).toBeInTheDocument()
      expect(screen.getByText(/Jan 14, 2024/)).toBeInTheDocument()
    })
  })

  it('applies correct score colors', async () => {
    mockApiClient.get.mockResolvedValueOnce(mockHistoryResponse)
    
    render(<QuizHistory onStartNewQuiz={mockOnStartNewQuiz} />)
    
    await waitFor(() => {
      // High score (85%) should be green
      const highScore = screen.getAllByText('85%')[0]
      expect(highScore).toHaveClass('text-success-600')
      
      // Medium score (72%) should be warning color
      const mediumScores = screen.getAllByText('72%')
      expect(mediumScores[0]).toHaveClass('text-warning-600')
    })
  })

  it('shows empty state when no quizzes exist', async () => {
    const emptyResponse = {
      quizzes: [],
      statistics: {
        total_quizzes: 0,
        average_score: 0,
        best_score: 0,
        total_questions_answered: 0,
        by_certification: {}
      }
    }
    
    mockApiClient.get.mockResolvedValueOnce(emptyResponse)
    
    render(<QuizHistory onStartNewQuiz={mockOnStartNewQuiz} />)
    
    await waitFor(() => {
      expect(screen.getByText('No Quiz History')).toBeInTheDocument()
      expect(screen.getByText(/You haven't taken any quizzes yet/)).toBeInTheDocument()
      expect(screen.getByText('Take Your First Quiz')).toBeInTheDocument()
    })
  })

  it('calls onStartNewQuiz when Take Your First Quiz is clicked', async () => {
    const emptyResponse = {
      quizzes: [],
      statistics: {
        total_quizzes: 0,
        average_score: 0,
        best_score: 0,
        total_questions_answered: 0,
        by_certification: {}
      }
    }
    
    mockApiClient.get.mockResolvedValueOnce(emptyResponse)
    
    render(<QuizHistory onStartNewQuiz={mockOnStartNewQuiz} />)
    
    await waitFor(() => {
      const startButton = screen.getByText('Take Your First Quiz')
      fireEvent.click(startButton)
      
      expect(mockOnStartNewQuiz).toHaveBeenCalledTimes(1)
    })
  })

  it('handles API errors gracefully', async () => {
    mockApiClient.get.mockRejectedValueOnce(new Error('API Error'))
    
    render(<QuizHistory onStartNewQuiz={mockOnStartNewQuiz} />)
    
    await waitFor(() => {
      expect(screen.getByText('Failed to load quiz history. Please try again.')).toBeInTheDocument()
      expect(screen.getByText('Try Again')).toBeInTheDocument()
    })
  })

  it('retries loading when Try Again is clicked', async () => {
    mockApiClient.get
      .mockRejectedValueOnce(new Error('API Error'))
      .mockResolvedValueOnce(mockHistoryResponse)
    
    render(<QuizHistory onStartNewQuiz={mockOnStartNewQuiz} />)
    
    await waitFor(() => {
      const tryAgainButton = screen.getByText('Try Again')
      fireEvent.click(tryAgainButton)
    })
    
    await waitFor(() => {
      expect(screen.getByText('Performance Overview')).toBeInTheDocument()
    })
    
    expect(mockApiClient.get).toHaveBeenCalledTimes(2)
  })

  it('fetches history on mount when user is authenticated', async () => {
    mockApiClient.get.mockResolvedValueOnce(mockHistoryResponse)
    
    render(<QuizHistory onStartNewQuiz={mockOnStartNewQuiz} />)
    
    await waitFor(() => {
      expect(mockApiClient.get).toHaveBeenCalled()
    })
  })

  it('does not fetch history when user is not authenticated', () => {
    mockUseSession.mockReturnValue({
      data: null,
      status: 'unauthenticated'
    } as any)
    
    render(<QuizHistory onStartNewQuiz={mockOnStartNewQuiz} />)
    
    expect(mockApiClient.get).not.toHaveBeenCalled()
  })
})