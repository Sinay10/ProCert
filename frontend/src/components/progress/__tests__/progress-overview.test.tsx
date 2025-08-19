import { render, screen } from '@testing-library/react'
import { ProgressOverview } from '../progress-overview'

const mockData = {
  total_study_time: 125,
  quizzes_completed: 8,
  average_score: 87.5,
  streak_days: 5
}

describe('ProgressOverview', () => {
  it('renders loading state', () => {
    render(<ProgressOverview loading={true} />)
    
    // Should render 4 skeleton cards
    const skeletonCards = screen.getAllByRole('generic').filter(el => 
      el.className.includes('animate-pulse')
    )
    expect(skeletonCards.length).toBeGreaterThan(0)
  })

  it('renders progress stats correctly', () => {
    render(<ProgressOverview data={mockData} loading={false} />)

    // Check study time formatting
    expect(screen.getByText('2h 5m')).toBeInTheDocument()
    expect(screen.getByText('Study Time')).toBeInTheDocument()

    // Check quizzes completed
    expect(screen.getByText('8')).toBeInTheDocument()
    expect(screen.getByText('Quizzes Completed')).toBeInTheDocument()

    // Check average score
    expect(screen.getByText('88%')).toBeInTheDocument()
    expect(screen.getByText('Average Score')).toBeInTheDocument()

    // Check streak
    expect(screen.getByText('5 days')).toBeInTheDocument()
    expect(screen.getByText('Study Streak')).toBeInTheDocument()
  })

  it('renders zero values when no data provided', () => {
    render(<ProgressOverview loading={false} />)

    expect(screen.getByText('0m')).toBeInTheDocument()
    expect(screen.getByText('0')).toBeInTheDocument()
    expect(screen.getByText('0%')).toBeInTheDocument()
    expect(screen.getByText('0 days')).toBeInTheDocument()
  })

  it('formats study time correctly for different durations', () => {
    // Test minutes only
    render(<ProgressOverview data={{ ...mockData, total_study_time: 45 }} loading={false} />)
    expect(screen.getByText('45m')).toBeInTheDocument()
  })

  it('applies correct color classes based on score', () => {
    // High score (green)
    const { rerender } = render(
      <ProgressOverview data={{ ...mockData, average_score: 85 }} loading={false} />
    )
    expect(screen.getByText('85%')).toHaveClass('text-green-600')

    // Medium score (yellow)
    rerender(<ProgressOverview data={{ ...mockData, average_score: 65 }} loading={false} />)
    expect(screen.getByText('65%')).toHaveClass('text-yellow-600')

    // Low score (red)
    rerender(<ProgressOverview data={{ ...mockData, average_score: 45 }} loading={false} />)
    expect(screen.getByText('45%')).toHaveClass('text-red-600')
  })

  it('applies correct color classes based on streak', () => {
    // Long streak (purple)
    const { rerender } = render(
      <ProgressOverview data={{ ...mockData, streak_days: 10 }} loading={false} />
    )
    expect(screen.getByText('10 days')).toHaveClass('text-purple-600')

    // Medium streak (blue)
    rerender(<ProgressOverview data={{ ...mockData, streak_days: 5 }} loading={false} />)
    expect(screen.getByText('5 days')).toHaveClass('text-blue-600')

    // Short streak (gray)
    rerender(<ProgressOverview data={{ ...mockData, streak_days: 1 }} loading={false} />)
    expect(screen.getByText('1 days')).toHaveClass('text-secondary-600')
  })
})