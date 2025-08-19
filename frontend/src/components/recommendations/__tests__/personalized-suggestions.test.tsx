import { render, screen, fireEvent } from '@testing-library/react'
import { vi, describe, it, beforeEach, expect } from 'vitest'
import { PersonalizedSuggestions } from '../personalized-suggestions'
import { UserAnalytics, StudyRecommendation } from '@/types/api'

const mockAnalytics: UserAnalytics = {
  performance: {
    strengths: ['EC2', 'S3'],
    weaknesses: ['VPC', 'Lambda'],
    improvement_rate: 0.75
  },
  predictions: {
    certification_readiness: {
      'AWS Solutions Architect': 0.8,
      'AWS Developer': 0.4
    },
    estimated_study_time: {
      'AWS Solutions Architect': 20,
      'AWS Developer': 60
    }
  },
  recommendations: ['Focus on VPC concepts', 'Practice Lambda functions']
}

const mockRecommendations: StudyRecommendation[] = [
  {
    recommendation_id: '1',
    type: 'content',
    priority: 8,
    content_id: 'vpc-content',
    reasoning: 'You need to improve VPC knowledge based on quiz performance.',
    estimated_time: 45,
    created_at: '2024-01-01T00:00:00Z'
  }
]

describe('PersonalizedSuggestions', () => {
  const mockOnSuggestionClick = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders personalized suggestions correctly', () => {
    render(
      <PersonalizedSuggestions
        analytics={mockAnalytics}
        recommendations={mockRecommendations}
        onSuggestionClick={mockOnSuggestionClick}
      />
    )

    expect(screen.getByText('Personalized Suggestions')).toBeInTheDocument()
    expect(screen.getByText('All Suggestions')).toBeInTheDocument()
  })

  it('generates weakness-focused suggestions', () => {
    render(
      <PersonalizedSuggestions
        analytics={mockAnalytics}
        recommendations={mockRecommendations}
        onSuggestionClick={mockOnSuggestionClick}
      />
    )

    expect(screen.getByText('Strengthen Your VPC Skills')).toBeInTheDocument()
    expect(screen.getByText('Focus on improving your understanding of VPC concepts')).toBeInTheDocument()
  })

  it('generates strength-building suggestions', () => {
    render(
      <PersonalizedSuggestions
        analytics={mockAnalytics}
        recommendations={mockRecommendations}
        onSuggestionClick={mockOnSuggestionClick}
      />
    )

    expect(screen.getByText('Advanced EC2 Topics')).toBeInTheDocument()
    expect(screen.getByText('Build on your strong foundation in EC2')).toBeInTheDocument()
  })

  it('generates certification readiness suggestions', () => {
    render(
      <PersonalizedSuggestions
        analytics={mockAnalytics}
        recommendations={mockRecommendations}
        onSuggestionClick={mockOnSuggestionClick}
      />
    )

    expect(screen.getByText('AWS Solutions Architect Certification Final Prep')).toBeInTheDocument()
    expect(screen.getByText("You're 80% ready for AWS Solutions Architect")).toBeInTheDocument()
  })

  it('shows loading state', () => {
    render(
      <PersonalizedSuggestions
        analytics={mockAnalytics}
        recommendations={mockRecommendations}
        onSuggestionClick={mockOnSuggestionClick}
        loading={true}
      />
    )

    expect(screen.getAllByTestId('loading-skeleton')).toHaveLength(3)
  })

  it('shows empty state when no suggestions available', () => {
    const emptyAnalytics: UserAnalytics = {
      performance: { strengths: [], weaknesses: [], improvement_rate: 0 },
      predictions: { certification_readiness: {}, estimated_study_time: {} },
      recommendations: []
    }

    render(
      <PersonalizedSuggestions
        analytics={emptyAnalytics}
        recommendations={[]}
        onSuggestionClick={mockOnSuggestionClick}
      />
    )

    expect(screen.getByText('No Suggestions Available')).toBeInTheDocument()
    expect(screen.getByText('Complete more activities to receive personalized study suggestions.')).toBeInTheDocument()
  })

  it('filters suggestions by type', () => {
    render(
      <PersonalizedSuggestions
        analytics={mockAnalytics}
        recommendations={mockRecommendations}
        onSuggestionClick={mockOnSuggestionClick}
      />
    )

    const filterSelect = screen.getByDisplayValue('All Suggestions')
    fireEvent.change(filterSelect, { target: { value: 'weakness_focus' } })

    expect(screen.getByText('Strengthen Your VPC Skills')).toBeInTheDocument()
    expect(screen.queryByText('Advanced EC2 Topics')).not.toBeInTheDocument()
  })

  it('handles suggestion click', () => {
    render(
      <PersonalizedSuggestions
        analytics={mockAnalytics}
        recommendations={mockRecommendations}
        onSuggestionClick={mockOnSuggestionClick}
      />
    )

    const startButtons = screen.getAllByText('Start')
    fireEvent.click(startButtons[0])

    expect(mockOnSuggestionClick).toHaveBeenCalledWith(
      expect.objectContaining({
        type: 'weakness_focus',
        title: 'Strengthen Your VPC Skills'
      })
    )
  })

  it('displays action items for suggestions', () => {
    render(
      <PersonalizedSuggestions
        analytics={mockAnalytics}
        recommendations={mockRecommendations}
        onSuggestionClick={mockOnSuggestionClick}
      />
    )

    expect(screen.getAllByText('Action Items:')).toHaveLength(3) // Multiple suggestions have action items
    expect(screen.getByText('Review VPC fundamentals')).toBeInTheDocument()
    expect(screen.getByText('Take practice quizzes on VPC')).toBeInTheDocument()
  })

  it('shows priority levels correctly', () => {
    render(
      <PersonalizedSuggestions
        analytics={mockAnalytics}
        recommendations={mockRecommendations}
        onSuggestionClick={mockOnSuggestionClick}
      />
    )

    expect(screen.getByText('Priority: 9/10')).toBeInTheDocument()
    expect(screen.getByText('Priority: 6/10')).toBeInTheDocument()
  })

  it('displays estimated time for suggestions', () => {
    render(
      <PersonalizedSuggestions
        analytics={mockAnalytics}
        recommendations={mockRecommendations}
        onSuggestionClick={mockOnSuggestionClick}
      />
    )

    expect(screen.getByText('45 min')).toBeInTheDocument()
    expect(screen.getByText('30 min')).toBeInTheDocument()
  })

  it('shows related content count when available', () => {
    render(
      <PersonalizedSuggestions
        analytics={mockAnalytics}
        recommendations={mockRecommendations}
        onSuggestionClick={mockOnSuggestionClick}
      />
    )

    expect(screen.getByText('1 related resources')).toBeInTheDocument()
  })

  it('generates time optimization suggestions for low improvement rate', () => {
    const lowImprovementAnalytics = {
      ...mockAnalytics,
      performance: {
        ...mockAnalytics.performance,
        improvement_rate: 0.3
      }
    }

    render(
      <PersonalizedSuggestions
        analytics={lowImprovementAnalytics}
        recommendations={mockRecommendations}
        onSuggestionClick={mockOnSuggestionClick}
      />
    )

    expect(screen.getByText('Optimize Your Study Approach')).toBeInTheDocument()
    expect(screen.getByText('Improve learning efficiency with better study strategies')).toBeInTheDocument()
  })
})