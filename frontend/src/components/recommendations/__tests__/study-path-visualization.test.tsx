import { render, screen, fireEvent } from '@testing-library/react'
import { vi } from 'vitest'
import { StudyPathVisualization } from '../study-path-visualization'
import { StudyPath } from '@/types/api'
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

const mockStudyPath: StudyPath = {
  path: [
    {
      topic: 'EC2 Fundamentals',
      status: 'completed',
      estimated_time: 45,
      content_ids: ['ec2-1', 'ec2-2']
    },
    {
      topic: 'S3 Storage',
      status: 'current',
      estimated_time: 60,
      content_ids: ['s3-1', 's3-2', 's3-3']
    },
    {
      topic: 'VPC Networking',
      status: 'locked',
      estimated_time: 90,
      content_ids: ['vpc-1', 'vpc-2']
    }
  ],
  progress: {
    completed_topics: 1,
    total_topics: 3,
    estimated_completion: '2024-02-15'
  },
  next_steps: [
    'Complete S3 Storage module',
    'Take practice quiz on S3',
    'Review VPC concepts'
  ]
}

describe('StudyPathVisualization', () => {
  const mockOnTopicClick = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders study path correctly', () => {
    render(
      <StudyPathVisualization
        studyPath={mockStudyPath}
        onTopicClick={mockOnTopicClick}
      />
    )

    expect(screen.getByText('Your Study Path')).toBeInTheDocument()
    expect(screen.getByText('1 of 3 topics completed')).toBeInTheDocument()
    expect(screen.getByText('33%')).toBeInTheDocument()
    expect(screen.getByText('Est. completion: 2024-02-15')).toBeInTheDocument()
  })

  it('displays topics with correct status', () => {
    render(
      <StudyPathVisualization
        studyPath={mockStudyPath}
        onTopicClick={mockOnTopicClick}
      />
    )

    expect(screen.getByText('EC2 Fundamentals')).toBeInTheDocument()
    expect(screen.getByText('S3 Storage')).toBeInTheDocument()
    expect(screen.getByText('VPC Networking')).toBeInTheDocument()

    expect(screen.getByText('Status: completed')).toBeInTheDocument()
    expect(screen.getByText('Status: current')).toBeInTheDocument()
    expect(screen.getByText('Status: locked')).toBeInTheDocument()
  })

  it('shows loading state', () => {
    render(
      <StudyPathVisualization
        studyPath={mockStudyPath}
        onTopicClick={mockOnTopicClick}
        loading={true}
      />
    )

    expect(screen.getByTestId('loading-skeleton')).toBeInTheDocument()
  })

  it('handles topic click for accessible topics', () => {
    render(
      <StudyPathVisualization
        studyPath={mockStudyPath}
        onTopicClick={mockOnTopicClick}
      />
    )

    const currentTopic = screen.getByText('S3 Storage').closest('div')
    fireEvent.click(currentTopic!)

    expect(mockOnTopicClick).toHaveBeenCalledWith(1)
  })

  it('does not handle click for locked topics', () => {
    render(
      <StudyPathVisualization
        studyPath={mockStudyPath}
        onTopicClick={mockOnTopicClick}
      />
    )

    const lockedTopic = screen.getByText('VPC Networking').closest('div')
    fireEvent.click(lockedTopic!)

    expect(mockOnTopicClick).not.toHaveBeenCalled()
  })

  it('expands topic details when clicked', () => {
    render(
      <StudyPathVisualization
        studyPath={mockStudyPath}
        onTopicClick={mockOnTopicClick}
      />
    )

    const currentTopic = screen.getByText('S3 Storage').closest('div')
    fireEvent.click(currentTopic!)

    expect(screen.getByText('Available Resources')).toBeInTheDocument()
    expect(screen.getByText('Content ID: s3-1')).toBeInTheDocument()
    expect(screen.getByText('Content ID: s3-2')).toBeInTheDocument()
    expect(screen.getByText('Content ID: s3-3')).toBeInTheDocument()
    expect(screen.getByText('Continue Learning')).toBeInTheDocument()
  })

  it('displays next steps when available', () => {
    render(
      <StudyPathVisualization
        studyPath={mockStudyPath}
        onTopicClick={mockOnTopicClick}
      />
    )

    expect(screen.getByText('Recommended Next Steps')).toBeInTheDocument()
    expect(screen.getByText('Complete S3 Storage module')).toBeInTheDocument()
    expect(screen.getByText('Take practice quiz on S3')).toBeInTheDocument()
    expect(screen.getByText('Review VPC concepts')).toBeInTheDocument()
  })

  it('displays correct progress percentage', () => {
    render(
      <StudyPathVisualization
        studyPath={mockStudyPath}
        onTopicClick={mockOnTopicClick}
      />
    )

    expect(screen.getByText('33%')).toBeInTheDocument()
  })

  it('shows resource counts correctly', () => {
    render(
      <StudyPathVisualization
        studyPath={mockStudyPath}
        onTopicClick={mockOnTopicClick}
      />
    )

    expect(screen.getByText('2 resources')).toBeInTheDocument()
    expect(screen.getByText('3 resources')).toBeInTheDocument()
  })

  it('displays estimated time for each topic', () => {
    render(
      <StudyPathVisualization
        studyPath={mockStudyPath}
        onTopicClick={mockOnTopicClick}
      />
    )

    expect(screen.getByText('45 min')).toBeInTheDocument()
    expect(screen.getByText('60 min')).toBeInTheDocument()
    expect(screen.getByText('90 min')).toBeInTheDocument()
  })
})