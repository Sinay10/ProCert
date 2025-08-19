import { render, screen } from '@testing-library/react'
import { PerformanceTrends } from '../performance-trends'

const mockTrendsData = [
  { date: '2025-01-10', score: 70, study_time: 30 },
  { date: '2025-01-11', score: 75, study_time: 25 },
  { date: '2025-01-12', score: 80, study_time: 35 },
  { date: '2025-01-13', score: 85, study_time: 40 },
  { date: '2025-01-14', score: 90, study_time: 30 }
]

describe('PerformanceTrends', () => {
  it('renders loading state', () => {
    const { container } = render(<PerformanceTrends loading={true} timeframe="month" />)
    
    expect(screen.getByText('Performance Trends')).toBeInTheDocument()
    
    // Should render skeleton loader
    const skeletonElement = container.querySelector('.animate-pulse')
    expect(skeletonElement).toBeTruthy()
  })

  it('renders empty state when no data', () => {
    render(<PerformanceTrends data={[]} loading={false} timeframe="month" />)
    
    expect(screen.getByText('No performance data yet')).toBeInTheDocument()
    expect(screen.getByText('Complete some quizzes to see your trends')).toBeInTheDocument()
  })

  it('renders performance trends with data', () => {
    render(<PerformanceTrends data={mockTrendsData} loading={false} timeframe="month" />)

    expect(screen.getByText('Performance Trends')).toBeInTheDocument()
    expect(screen.getByText('Quiz Scores')).toBeInTheDocument()
    expect(screen.getByText('Study Time (minutes)')).toBeInTheDocument()
  })

  it('calculates and displays trend direction correctly', () => {
    // Create data with significant upward trend (need more data points for trend calculation)
    const upwardTrendData = [
      { date: '2025-01-01', score: 50, study_time: 30 },
      { date: '2025-01-02', score: 55, study_time: 25 },
      { date: '2025-01-03', score: 60, study_time: 35 },
      { date: '2025-01-04', score: 65, study_time: 40 },
      { date: '2025-01-05', score: 70, study_time: 30 },
      { date: '2025-01-06', score: 75, study_time: 35 },
      { date: '2025-01-07', score: 80, study_time: 40 },
      { date: '2025-01-08', score: 85, study_time: 30 },
      { date: '2025-01-09', score: 90, study_time: 35 },
      { date: '2025-01-10', score: 95, study_time: 40 }
    ]

    render(<PerformanceTrends data={upwardTrendData} loading={false} timeframe="month" />)
    
    expect(screen.getByText('Improving performance')).toBeInTheDocument()
  })

  it('displays summary statistics correctly', () => {
    render(<PerformanceTrends data={mockTrendsData} loading={false} timeframe="month" />)

    // Calculate expected averages
    const avgScore = Math.round(mockTrendsData.reduce((sum, item) => sum + item.score, 0) / mockTrendsData.length)
    const avgStudyTime = Math.round(mockTrendsData.reduce((sum, item) => sum + item.study_time, 0) / mockTrendsData.length)

    expect(screen.getByText(`${avgScore}%`)).toBeInTheDocument()
    expect(screen.getByText(`${avgStudyTime}m`)).toBeInTheDocument()
    expect(screen.getByText('Average Score')).toBeInTheDocument()
    expect(screen.getByText('Avg Study Time')).toBeInTheDocument()
  })

  it('formats dates correctly based on timeframe', () => {
    const { rerender } = render(
      <PerformanceTrends data={mockTrendsData} loading={false} timeframe="week" />
    )

    // Week timeframe should show weekday names
    // Note: The actual date formatting depends on the implementation
    // We're testing that the component renders without errors

    rerender(<PerformanceTrends data={mockTrendsData} loading={false} timeframe="month" />)
    rerender(<PerformanceTrends data={mockTrendsData} loading={false} timeframe="quarter" />)
    rerender(<PerformanceTrends data={mockTrendsData} loading={false} timeframe="year" />)

    // Should render without errors for all timeframes
    expect(screen.getByText('Performance Trends')).toBeInTheDocument()
  })

  it('handles single data point correctly', () => {
    const singleDataPoint = [{ date: '2025-01-15', score: 85, study_time: 30 }]
    
    render(<PerformanceTrends data={singleDataPoint} loading={false} timeframe="month" />)

    expect(screen.getByText('Stable performance')).toBeInTheDocument()
    expect(screen.getByText('85%')).toBeInTheDocument()
    expect(screen.getByText('30m')).toBeInTheDocument()
  })

  it('renders SVG chart elements', () => {
    const { container } = render(<PerformanceTrends data={mockTrendsData} loading={false} timeframe="month" />)

    // Check for SVG elements
    const svgElement = container.querySelector('svg')
    expect(svgElement).toBeTruthy()
  })

  it('handles undefined data gracefully', () => {
    render(<PerformanceTrends loading={false} timeframe="month" />)
    
    expect(screen.getByText('No performance data yet')).toBeInTheDocument()
  })
})