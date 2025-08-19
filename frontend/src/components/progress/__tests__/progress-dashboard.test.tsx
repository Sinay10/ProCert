import { render, screen, waitFor } from '@testing-library/react'
import { vi } from 'vitest'
import { useSession } from 'next-auth/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ProgressDashboard } from '../progress-dashboard'
import { apiClient } from '@/lib/api-client'

// Mock dependencies
vi.mock('next-auth/react')
vi.mock('@/lib/api-client')

const mockUseSession = useSession as any
const mockApiClient = apiClient as any

const mockProgressData = {
  overall: {
    total_study_time: 120,
    quizzes_completed: 5,
    average_score: 85,
    streak_days: 3
  },
  by_certification: {
    'aws-solutions-architect': {
      progress_percentage: 65,
      topics_completed: 13,
      total_topics: 20,
      last_activity: '2025-01-15T10:00:00Z'
    }
  },
  trends: [
    { date: '2025-01-10', score: 80, study_time: 30 },
    { date: '2025-01-11', score: 85, study_time: 25 },
    { date: '2025-01-12', score: 90, study_time: 35 }
  ]
}

const mockAnalyticsData = {
  performance: {
    strengths: ['EC2', 'S3', 'IAM'],
    weaknesses: ['Lambda', 'API Gateway'],
    improvement_rate: 0.15
  },
  predictions: {
    certification_readiness: {
      'aws-solutions-architect': 0.75
    },
    estimated_study_time: {
      'aws-solutions-architect': 40
    }
  },
  recommendations: [
    'Focus on Lambda functions and serverless architecture',
    'Practice more API Gateway configurations',
    'Review security best practices'
  ]
}

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false }
    }
  })
  
  const TestWrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
  
  return TestWrapper
}

describe('ProgressDashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders sign-in message when user is not authenticated', () => {
    mockUseSession.mockReturnValue({
      data: null,
      status: 'unauthenticated'
    } as any)

    render(<ProgressDashboard />, { wrapper: createWrapper() })

    expect(screen.getByText('Please sign in to view your progress.')).toBeInTheDocument()
  })

  it('renders loading state initially', () => {
    mockUseSession.mockReturnValue({
      data: { userId: 'user-123' },
      status: 'authenticated'
    } as any)

    mockApiClient.get.mockImplementation(() => new Promise(() => {})) // Never resolves

    render(<ProgressDashboard />, { wrapper: createWrapper() })

    expect(screen.getByText('Learning Progress')).toBeInTheDocument()
    expect(screen.getByText('Track your performance and study analytics')).toBeInTheDocument()
  })

  it('renders progress dashboard with data', async () => {
    mockUseSession.mockReturnValue({
      data: { userId: 'user-123' },
      status: 'authenticated'
    } as any)

    mockApiClient.get
      .mockResolvedValueOnce(mockProgressData)
      .mockResolvedValueOnce(mockAnalyticsData)

    render(<ProgressDashboard />, { wrapper: createWrapper() })

    await waitFor(() => {
      expect(screen.getByText('Learning Progress')).toBeInTheDocument()
    })

    // Check if timeframe selector is rendered
    expect(screen.getByText('Week')).toBeInTheDocument()
    expect(screen.getByText('Month')).toBeInTheDocument()
    expect(screen.getByText('Quarter')).toBeInTheDocument()
    expect(screen.getByText('Year')).toBeInTheDocument()
  })

  it('renders progress dashboard with mock data', async () => {
    mockUseSession.mockReturnValue({
      data: { userId: 'user-123' },
      status: 'authenticated'
    } as any)

    render(<ProgressDashboard />, { wrapper: createWrapper() })

    await waitFor(() => {
      expect(screen.getByText('Learning Progress')).toBeInTheDocument()
      expect(screen.getAllByText('3h 0m')).toHaveLength(2) // Appears in overview and study tracker
      expect(screen.getByText('8')).toBeInTheDocument() // Mock quizzes completed
      expect(screen.getByText('87%')).toBeInTheDocument() // Mock average score
    })
  })

  it('displays mock certification progress', async () => {
    mockUseSession.mockReturnValue({
      data: { userId: 'user-123' },
      status: 'authenticated'
    } as any)

    render(<ProgressDashboard />, { wrapper: createWrapper() })

    await waitFor(() => {
      expect(screen.getAllByText('AWS SOLUTIONS ARCHITECT')).toHaveLength(3) // Appears in multiple sections
      expect(screen.getAllByText('AWS DEVELOPER')).toHaveLength(3) // Appears in multiple sections
    })
  })
})