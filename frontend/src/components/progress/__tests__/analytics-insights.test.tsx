import { render, screen } from '@testing-library/react'
import { AnalyticsInsights } from '../analytics-insights'

const mockAnalyticsData = {
  performance: {
    strengths: ['EC2', 'S3', 'IAM'],
    weaknesses: ['Lambda', 'API Gateway'],
    improvement_rate: 0.15
  },
  predictions: {
    certification_readiness: {
      'aws-solutions-architect': 0.85,
      'aws-developer': 0.65
    },
    estimated_study_time: {
      'aws-solutions-architect': 25,
      'aws-developer': 45
    }
  },
  recommendations: [
    'Focus on Lambda functions and serverless architecture',
    'Practice more API Gateway configurations',
    'Review security best practices'
  ]
}

describe('AnalyticsInsights', () => {
  it('renders loading state', () => {
    render(<AnalyticsInsights loading={true} />)
    
    expect(screen.getByText('Analytics Insights')).toBeInTheDocument()
    
    // Should render skeleton loaders
    const skeletonElements = screen.getAllByRole('generic').filter(el => 
      el.className.includes('animate-pulse')
    )
    expect(skeletonElements.length).toBeGreaterThan(0)
  })

  it('renders empty state when no data', () => {
    render(<AnalyticsInsights loading={false} />)

    expect(screen.getByText('No analytics data yet')).toBeInTheDocument()
    expect(screen.getByText('Complete more activities to see insights')).toBeInTheDocument()
  })

  it('displays performance analysis correctly', () => {
    render(<AnalyticsInsights data={mockAnalyticsData} loading={false} />)

    expect(screen.getByText('Performance Analysis')).toBeInTheDocument()
    
    // Check strengths
    expect(screen.getByText('Strengths')).toBeInTheDocument()
    expect(screen.getByText('EC2')).toBeInTheDocument()
    expect(screen.getByText('S3')).toBeInTheDocument()
    expect(screen.getByText('IAM')).toBeInTheDocument()
    
    // Check weaknesses
    expect(screen.getByText('Areas to Improve')).toBeInTheDocument()
    expect(screen.getByText('Lambda')).toBeInTheDocument()
    expect(screen.getByText('API Gateway')).toBeInTheDocument()
    
    // Check improvement rate
    expect(screen.getByText('Improvement Rate')).toBeInTheDocument()
    expect(screen.getByText('15%')).toBeInTheDocument()
  })

  it('displays certification readiness with correct colors', () => {
    render(<AnalyticsInsights data={mockAnalyticsData} loading={false} />)

    expect(screen.getByText('Certification Readiness')).toBeInTheDocument()
    
    // Check certification names and readiness percentages
    expect(screen.getAllByText('AWS SOLUTIONS ARCHITECT')).toHaveLength(2) // Appears in both readiness and study time sections
    expect(screen.getByText('85%')).toBeInTheDocument()
    expect(screen.getAllByText('AWS DEVELOPER')).toHaveLength(2) // Appears in both sections
    expect(screen.getByText('65%')).toBeInTheDocument()
  })

  it('applies correct readiness colors based on percentage', () => {
    render(<AnalyticsInsights data={mockAnalyticsData} loading={false} />)

    // High readiness (85%) should have green color
    const highReadiness = screen.getByText('85%')
    expect(highReadiness).toHaveClass('text-green-600')
    
    // Medium readiness (65%) should have yellow color
    const mediumReadiness = screen.getByText('65%')
    expect(mediumReadiness).toHaveClass('text-yellow-600')
  })

  it('displays estimated study time correctly', () => {
    render(<AnalyticsInsights data={mockAnalyticsData} loading={false} />)

    expect(screen.getByText('Estimated Study Time')).toBeInTheDocument()
    // Check that study time section is rendered (using getAllByText since names appear in multiple sections)
    expect(screen.getAllByText('AWS SOLUTIONS ARCHITECT')).toHaveLength(2)
    expect(screen.getAllByText('AWS DEVELOPER')).toHaveLength(2)
  })

  it('formats study time estimates correctly', () => {
    const dataWithDifferentTimes = {
      ...mockAnalyticsData,
      predictions: {
        ...mockAnalyticsData.predictions,
        estimated_study_time: {
          'aws-solutions-architect': 0.5, // 30 minutes
          'aws-developer': 30, // 30 hours
          'aws-sysops': 72 // 3 days
        }
      }
    }

    render(<AnalyticsInsights data={dataWithDifferentTimes} loading={false} />)

    // Check that different time formats are rendered
    const timeElements = screen.getAllByText(/\d+[mhd]/)
    expect(timeElements.length).toBeGreaterThan(0)
  })

  it('displays AI recommendations', () => {
    render(<AnalyticsInsights data={mockAnalyticsData} loading={false} />)

    expect(screen.getByText('AI Recommendations')).toBeInTheDocument()
    expect(screen.getByText('Focus on Lambda functions and serverless architecture')).toBeInTheDocument()
    expect(screen.getByText('Practice more API Gateway configurations')).toBeInTheDocument()
    expect(screen.getByText('Review security best practices')).toBeInTheDocument()
  })

  it('displays quick stats correctly', () => {
    render(<AnalyticsInsights data={mockAnalyticsData} loading={false} />)

    expect(screen.getByText('Strong Areas')).toBeInTheDocument()
    expect(screen.getByText('Certifications')).toBeInTheDocument()
    
    // Should show count of strengths (3) and certifications (2)
    expect(screen.getByText('3')).toBeInTheDocument() // Strengths count
    expect(screen.getByText('2')).toBeInTheDocument() // Certifications count
  })

  it('displays motivational message based on improvement rate', () => {
    render(<AnalyticsInsights data={mockAnalyticsData} loading={false} />)

    // With improvement rate of 0.15 (15%), should show excellent progress message
    expect(screen.getByText(/You're making excellent progress/)).toBeInTheDocument()
  })

  it('displays different motivational messages for different improvement rates', () => {
    // Test medium improvement rate
    const mediumImprovementData = {
      ...mockAnalyticsData,
      performance: {
        ...mockAnalyticsData.performance,
        improvement_rate: 0.07
      }
    }

    const { rerender } = render(<AnalyticsInsights data={mediumImprovementData} loading={false} />)
    expect(screen.getByText(/Steady progress/)).toBeInTheDocument()

    // Test low improvement rate
    const lowImprovementData = {
      ...mockAnalyticsData,
      performance: {
        ...mockAnalyticsData.performance,
        improvement_rate: 0.02
      }
    }

    rerender(<AnalyticsInsights data={lowImprovementData} loading={false} />)
    expect(screen.getByText(/Every expert was once a beginner/)).toBeInTheDocument()
  })

  it('handles empty arrays gracefully', () => {
    const emptyData = {
      performance: {
        strengths: [],
        weaknesses: [],
        improvement_rate: 0
      },
      predictions: {
        certification_readiness: {},
        estimated_study_time: {}
      },
      recommendations: []
    }

    render(<AnalyticsInsights data={emptyData} loading={false} />)

    expect(screen.getByText('Analytics Insights')).toBeInTheDocument()
    // Should still render sections even with empty data
    expect(screen.getByText('Performance Analysis')).toBeInTheDocument()
  })
})