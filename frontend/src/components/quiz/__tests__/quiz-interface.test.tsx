import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { vi } from 'vitest'
import { useSession } from 'next-auth/react'
import { QuizInterface } from '../quiz-interface'
import { apiClient } from '@/lib/api-client'

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

const mockQuizResponse = {
  quiz_id: 'test-quiz-id',
  questions: [
    {
      question_id: 'q1',
      question_text: 'What is AWS?',
      options: ['Option A', 'Option B', 'Option C', 'Option D'],
      correct_answer: 'Option A',
      explanation: 'AWS stands for Amazon Web Services'
    }
  ],
  metadata: {
    certification: 'aws-cloud-practitioner',
    difficulty: 'beginner',
    estimated_time: 10
  }
}

const mockQuizResult = {
  score: 100,
  results: [
    {
      question_id: 'q1',
      correct: true,
      user_answer: 'Option A',
      correct_answer: 'Option A'
    }
  ],
  feedback: [
    {
      question_id: 'q1',
      explanation: 'AWS stands for Amazon Web Services'
    }
  ]
}

describe('QuizInterface', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockUseSession.mockReturnValue({
      data: mockSession,
      status: 'authenticated'
    })
  })

  it('renders quiz settings by default', () => {
    render(<QuizInterface />)
    
    expect(screen.getByText('Practice Quizzes')).toBeInTheDocument()
    expect(screen.getByText('Quiz Settings')).toBeInTheDocument()
    expect(screen.getByText('Start Quiz')).toBeInTheDocument()
  })

  it('starts a quiz when settings are submitted', async () => {
    mockApiClient.post.mockResolvedValueOnce(mockQuizResponse)
    
    render(<QuizInterface />)
    
    // Fill out quiz settings
    const certificationSelect = screen.getByDisplayValue('AWS Cloud Practitioner')
    expect(certificationSelect).toBeInTheDocument()
    
    const startButton = screen.getByText('Start Quiz')
    fireEvent.click(startButton)
    
    await waitFor(() => {
      expect(mockApiClient.post).toHaveBeenCalledWith('/quiz/generate', {
        certification: 'aws-cloud-practitioner',
        difficulty: 'mixed',
        count: 10,
        user_id: 'test-user-id'
      })
    })
  })

  it('displays quiz questions when quiz is active', async () => {
    mockApiClient.post.mockResolvedValueOnce(mockQuizResponse)
    
    render(<QuizInterface />)
    
    const startButton = screen.getByText('Start Quiz')
    fireEvent.click(startButton)
    
    await waitFor(() => {
      expect(screen.getByText('What is AWS?')).toBeInTheDocument()
      expect(screen.getByText('Option A')).toBeInTheDocument()
      expect(screen.getByText('Question 1 of 1')).toBeInTheDocument()
    })
  })

  it('allows selecting answers and navigating questions', async () => {
    mockApiClient.post.mockResolvedValueOnce(mockQuizResponse)
    
    render(<QuizInterface />)
    
    const startButton = screen.getByText('Start Quiz')
    fireEvent.click(startButton)
    
    await waitFor(() => {
      const optionA = screen.getByLabelText(/Option A/)
      fireEvent.click(optionA)
      
      expect(optionA).toBeChecked()
    })
  })

  it('submits quiz and shows results', async () => {
    mockApiClient.post
      .mockResolvedValueOnce(mockQuizResponse)
      .mockResolvedValueOnce(mockQuizResult)
    
    render(<QuizInterface />)
    
    // Start quiz
    const startButton = screen.getByText('Start Quiz')
    fireEvent.click(startButton)
    
    await waitFor(() => {
      // Select answer
      const optionA = screen.getByLabelText(/Option A/)
      fireEvent.click(optionA)
      
      // Submit quiz
      const submitButton = screen.getByText('Submit Quiz')
      fireEvent.click(submitButton)
    })
    
    await waitFor(() => {
      expect(mockApiClient.post).toHaveBeenCalledWith('/quiz/submit', {
        quiz_id: 'test-quiz-id',
        answers: ['Option A'],
        user_id: 'test-user-id'
      })
    })
    
    await waitFor(() => {
      expect(screen.getByText('Quiz Complete!')).toBeInTheDocument()
      expect(screen.getByText('100%')).toBeInTheDocument()
    })
  })

  it('handles API errors gracefully', async () => {
    mockApiClient.post.mockRejectedValueOnce(new Error('API Error'))
    
    render(<QuizInterface />)
    
    const startButton = screen.getByText('Start Quiz')
    fireEvent.click(startButton)
    
    await waitFor(() => {
      expect(screen.getByText(/Failed to generate quiz/)).toBeInTheDocument()
    })
  })

  it('requires authentication', () => {
    mockUseSession.mockReturnValue({
      data: null,
      status: 'unauthenticated'
    } as any)
    
    render(<QuizInterface />)
    
    const startButton = screen.getByText('Start Quiz')
    fireEvent.click(startButton)
    
    expect(screen.getByText(/Please sign in to take quizzes/)).toBeInTheDocument()
  })

  it('navigates to history view', () => {
    render(<QuizInterface />)
    
    const historyButton = screen.getByText('View History')
    fireEvent.click(historyButton)
    
    expect(screen.getByText('Quiz History')).toBeInTheDocument()
  })
})