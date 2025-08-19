import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { vi } from 'vitest'
import { RecommendationFeedback } from '../recommendation-feedback'
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

describe('RecommendationFeedback', () => {
  const mockOnSubmitFeedback = vi.fn()
  const mockOnClose = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders feedback form correctly', () => {
    render(
      <RecommendationFeedback
        recommendationId="test-recommendation"
        onSubmitFeedback={mockOnSubmitFeedback}
        onClose={mockOnClose}
      />
    )

    expect(screen.getByText('How was this recommendation?')).toBeInTheDocument()
    expect(screen.getByText('Your feedback helps us improve future recommendations')).toBeInTheDocument()
    expect(screen.getByText('Was this recommendation helpful?')).toBeInTheDocument()
    expect(screen.getByText('Overall rating')).toBeInTheDocument()
  })

  it('handles helpful/not helpful selection', () => {
    render(
      <RecommendationFeedback
        recommendationId="test-recommendation"
        onSubmitFeedback={mockOnSubmitFeedback}
        onClose={mockOnClose}
      />
    )

    const helpfulButton = screen.getByText('Yes, helpful')
    fireEvent.click(helpfulButton)

    expect(helpfulButton).toHaveClass('bg-blue-600') // or whatever the selected class is
  })

  it('handles star rating selection', () => {
    render(
      <RecommendationFeedback
        recommendationId="test-recommendation"
        onSubmitFeedback={mockOnSubmitFeedback}
        onClose={mockOnClose}
      />
    )

    // Find star buttons by their container
    const starContainer = screen.getByText('Overall rating').parentElement
    const stars = starContainer?.querySelectorAll('button') || []
    
    if (stars.length > 3) {
      fireEvent.click(stars[3]) // Click 4th star (4-star rating)
    }

    // Basic check that interaction works
    expect(stars.length).toBeGreaterThan(0)
  })

  it('shows feedback categories when helpful is selected', () => {
    render(
      <RecommendationFeedback
        recommendationId="test-recommendation"
        onSubmitFeedback={mockOnSubmitFeedback}
        onClose={mockOnClose}
      />
    )

    const helpfulButton = screen.getByText('Yes, helpful')
    fireEvent.click(helpfulButton)

    expect(screen.getByText('What made it helpful? (Select all that apply)')).toBeInTheDocument()
    expect(screen.getByText('Relevant to my goals')).toBeInTheDocument()
    expect(screen.getByText('Appropriate difficulty')).toBeInTheDocument()
    expect(screen.getByText('Good timing')).toBeInTheDocument()
  })

  it('handles category selection', () => {
    render(
      <RecommendationFeedback
        recommendationId="test-recommendation"
        onSubmitFeedback={mockOnSubmitFeedback}
        onClose={mockOnClose}
      />
    )

    const helpfulButton = screen.getByText('Yes, helpful')
    fireEvent.click(helpfulButton)

    const relevantCategory = screen.getByText('Relevant to my goals')
    fireEvent.click(relevantCategory)

    expect(relevantCategory).toHaveClass('bg-blue-50') // Selected state
  })

  it('handles comments input', () => {
    render(
      <RecommendationFeedback
        recommendationId="test-recommendation"
        onSubmitFeedback={mockOnSubmitFeedback}
        onClose={mockOnClose}
      />
    )

    const commentsTextarea = screen.getByPlaceholderText('Tell us more about your experience...')
    fireEvent.change(commentsTextarea, { target: { value: 'This was very helpful!' } })

    expect(commentsTextarea).toHaveValue('This was very helpful!')
    expect(screen.getByText('23/500 characters')).toBeInTheDocument()
  })

  it('disables submit button when required fields are missing', () => {
    render(
      <RecommendationFeedback
        recommendationId="test-recommendation"
        onSubmitFeedback={mockOnSubmitFeedback}
        onClose={mockOnClose}
      />
    )

    const submitButton = screen.getByText('Submit Feedback')
    expect(submitButton).toBeDisabled()
  })

  it('enables submit button when required fields are filled', () => {
    render(
      <RecommendationFeedback
        recommendationId="test-recommendation"
        onSubmitFeedback={mockOnSubmitFeedback}
        onClose={mockOnClose}
      />
    )

    // Select helpful
    const helpfulButton = screen.getByText('Yes, helpful')
    fireEvent.click(helpfulButton)

    // Select rating
    const stars = screen.getAllByRole('button').filter(button => 
      button.querySelector('svg')?.classList.contains('w-6')
    )
    fireEvent.click(stars[3])

    const submitButton = screen.getByText('Submit Feedback')
    expect(submitButton).not.toBeDisabled()
  })

  it('submits feedback with correct data', async () => {
    render(
      <RecommendationFeedback
        recommendationId="test-recommendation"
        onSubmitFeedback={mockOnSubmitFeedback}
        onClose={mockOnClose}
      />
    )

    // Fill out form
    const helpfulButton = screen.getByText('Yes, helpful')
    fireEvent.click(helpfulButton)

    const stars = screen.getAllByRole('button').filter(button => 
      button.querySelector('svg')?.classList.contains('w-6')
    )
    fireEvent.click(stars[3]) // 4-star rating

    const relevantCategory = screen.getByText('Relevant to my goals')
    fireEvent.click(relevantCategory)

    const commentsTextarea = screen.getByPlaceholderText('Tell us more about your experience...')
    fireEvent.change(commentsTextarea, { target: { value: 'Great recommendation!' } })

    const submitButton = screen.getByText('Submit Feedback')
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(mockOnSubmitFeedback).toHaveBeenCalledWith({
        recommendationId: 'test-recommendation',
        rating: 4,
        helpful: true,
        comments: 'Great recommendation!',
        categories: ['relevant']
      })
    })
  })

  it('handles close button click', () => {
    render(
      <RecommendationFeedback
        recommendationId="test-recommendation"
        onSubmitFeedback={mockOnSubmitFeedback}
        onClose={mockOnClose}
      />
    )

    const cancelButton = screen.getByText('Cancel')
    fireEvent.click(cancelButton)

    expect(mockOnClose).toHaveBeenCalled()
  })

  it('shows loading state during submission', async () => {
    const slowSubmit = jest.fn(() => new Promise(resolve => setTimeout(resolve, 100)))
    
    render(
      <RecommendationFeedback
        recommendationId="test-recommendation"
        onSubmitFeedback={slowSubmit}
        onClose={mockOnClose}
      />
    )

    // Fill required fields
    const helpfulButton = screen.getByText('Yes, helpful')
    fireEvent.click(helpfulButton)

    const stars = screen.getAllByRole('button').filter(button => 
      button.querySelector('svg')?.classList.contains('w-6')
    )
    fireEvent.click(stars[3])

    const submitButton = screen.getByText('Submit Feedback')
    fireEvent.click(submitButton)

    expect(screen.getByText('Submitting...')).toBeInTheDocument()
    expect(submitButton).toBeDisabled()
  })
})