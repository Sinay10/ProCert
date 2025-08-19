import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { vi } from 'vitest'
import { RecommendationDisplay } from '../recommendation-display'
import { StudyRecommendation } from '@/types/api'
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

const mockRecommendations: StudyRecommendation[] = [
  {
    recommendation_id: '1',
    type: 'content',
    priority: 8,
    content_id: 'content-123',
    reasoning: 'Based on your recent quiz performance, you should focus on EC2 fundamentals.',
    estimated_time: 30,
    created_at: '2024-01-01T00:00:00Z'
  },
  {
    recommendation_id: '2',
    type: 'quiz',
    priority: 6,
    reasoning: 'Practice more S3 questions to improve your storage knowledge.',
    estimated_time: 15,
    created_at: '2024-01-02T00:00:00Z'
  }
]

describe('RecommendationDisplay', () => {
  const mockOnRecommendationClick = vi.fn()
  const mockOnFeedback = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders recommendations correctly', () => {
    render(
      <RecommendationDisplay
        recommendations={mockRecommendations}
        onRecommendationClick={mockOnRecommendationClick}
        onFeedback={mockOnFeedback}
      />
    )

    expect(screen.getByText('Study Recommendations')).toBeInTheDocument()
    expect(screen.getByText('2 recommendations available')).toBeInTheDocument()
    expect(screen.getByText('Based on your recent quiz performance, you should focus on EC2 fundamentals.')).toBeInTheDocument()
    expect(screen.getByText('Practice more S3 questions to improve your storage knowledge.')).toBeInTheDocument()
  })

  it('shows loading state', () => {
    render(
      <RecommendationDisplay
        recommendations={[]}
        onRecommendationClick={mockOnRecommendationClick}
        onFeedback={mockOnFeedback}
        loading={true}
      />
    )

    expect(screen.getAllByTestId('loading-skeleton')).toHaveLength(3)
  })

  it('shows empty state when no recommendations', () => {
    render(
      <RecommendationDisplay
        recommendations={[]}
        onRecommendationClick={mockOnRecommendationClick}
        onFeedback={mockOnFeedback}
      />
    )

    expect(screen.getByText('No Recommendations Available')).toBeInTheDocument()
    expect(screen.getByText('Complete some quizzes or interact with the chatbot to get personalized study recommendations.')).toBeInTheDocument()
  })

  it('handles recommendation click', () => {
    render(
      <RecommendationDisplay
        recommendations={mockRecommendations}
        onRecommendationClick={mockOnRecommendationClick}
        onFeedback={mockOnFeedback}
      />
    )

    const startButtons = screen.getAllByText('Start')
    fireEvent.click(startButtons[0])

    expect(mockOnRecommendationClick).toHaveBeenCalledWith(mockRecommendations[0])
  })

  it('handles feedback submission', () => {
    render(
      <RecommendationDisplay
        recommendations={mockRecommendations}
        onRecommendationClick={mockOnRecommendationClick}
        onFeedback={mockOnFeedback}
      />
    )

    const helpfulButtons = screen.getAllByText('👍 Helpful')
    fireEvent.click(helpfulButtons[0])

    expect(mockOnFeedback).toHaveBeenCalledWith('1', 'helpful')
  })

  it('expands and collapses recommendation details', () => {
    render(
      <RecommendationDisplay
        recommendations={mockRecommendations}
        onRecommendationClick={mockOnRecommendationClick}
        onFeedback={mockOnFeedback}
      />
    )

    const moreInfoButtons = screen.getAllByText('More Info')
    fireEvent.click(moreInfoButtons[0])

    expect(screen.getByText('Why this recommendation?')).toBeInTheDocument()
    expect(screen.getByText('content-123')).toBeInTheDocument()

    const lessInfoButton = screen.getByText('Less Info')
    fireEvent.click(lessInfoButton)

    expect(screen.queryByText('Why this recommendation?')).not.toBeInTheDocument()
  })

  it('displays correct priority colors and labels', () => {
    render(
      <RecommendationDisplay
        recommendations={mockRecommendations}
        onRecommendationClick={mockOnRecommendationClick}
        onFeedback={mockOnFeedback}
      />
    )

    expect(screen.getByText('High Priority')).toBeInTheDocument()
    expect(screen.getByText('Medium Priority')).toBeInTheDocument()
  })

  it('displays correct icons for different recommendation types', () => {
    render(
      <RecommendationDisplay
        recommendations={mockRecommendations}
        onRecommendationClick={mockOnRecommendationClick}
        onFeedback={mockOnFeedback}
      />
    )

    expect(screen.getByText('content Recommendation')).toBeInTheDocument()
    expect(screen.getByText('quiz Recommendation')).toBeInTheDocument()
  })

  it('formats dates correctly', () => {
    render(
      <RecommendationDisplay
        recommendations={mockRecommendations}
        onRecommendationClick={mockOnRecommendationClick}
        onFeedback={mockOnFeedback}
      />
    )

    expect(screen.getByText('Created 1/1/2024')).toBeInTheDocument()
    expect(screen.getByText('Created 1/2/2024')).toBeInTheDocument()
  })
})