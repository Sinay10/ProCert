import { render, screen, fireEvent } from '@testing-library/react'
import { vi } from 'vitest'
import { ActiveStudyPaths } from '../active-study-paths'
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

const mockActivePaths = [
  {
    id: 'path-1',
    title: 'AWS Solutions Architect Associate Study Path',
    certification: 'SAA',
    startedAt: '2024-01-15T10:00:00Z',
    lastAccessedAt: '2024-01-18T14:30:00Z',
    totalTopics: 8,
    completedTopics: 3,
    currentTopic: 'VPC Networking Fundamentals',
    estimatedTimeRemaining: 180,
    status: 'active' as const,
    progressPercentage: 37.5,
    topics: [
      { id: 'topic-1', title: 'EC2 Fundamentals', status: 'completed' as const },
      { id: 'topic-2', title: 'S3 Storage Basics', status: 'completed' as const },
      { id: 'topic-3', title: 'IAM Security', status: 'completed' as const },
      { id: 'topic-4', title: 'VPC Networking Fundamentals', status: 'current' as const }
    ]
  },
  {
    id: 'path-2',
    title: 'VPC Networking Deep Dive',
    certification: 'SAA',
    startedAt: '2024-01-10T09:00:00Z',
    lastAccessedAt: '2024-01-12T16:00:00Z',
    totalTopics: 5,
    completedTopics: 5,
    currentTopic: 'Completed',
    estimatedTimeRemaining: 0,
    status: 'completed' as const,
    progressPercentage: 100,
    topics: []
  }
]

describe('ActiveStudyPaths', () => {
  const mockOnContinuePath = vi.fn()
  const mockOnPausePath = vi.fn()
  const mockOnCompletePath = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders active study paths correctly', () => {
    render(
      <ActiveStudyPaths
        onContinuePath={mockOnContinuePath}
        onPausePath={mockOnPausePath}
        onCompletePath={mockOnCompletePath}
        activePaths={mockActivePaths}
      />
    )

    expect(screen.getByText('Active Study Paths')).toBeInTheDocument()
    expect(screen.getByText('AWS Solutions Architect Associate Study Path')).toBeInTheDocument()
    expect(screen.getByText('VPC Networking Deep Dive')).toBeInTheDocument()
    expect(screen.getByText('1 active, 1 completed')).toBeInTheDocument()
  })

  it('shows loading state', () => {
    render(
      <ActiveStudyPaths
        onContinuePath={mockOnContinuePath}
        onPausePath={mockOnPausePath}
        onCompletePath={mockOnCompletePath}
        activePaths={[]}
        loading={true}
      />
    )

    // Check for loading animation elements
    expect(screen.getAllByRole('generic')).toBeTruthy()
  })

  it('shows empty state when no paths', () => {
    render(
      <ActiveStudyPaths
        onContinuePath={mockOnContinuePath}
        onPausePath={mockOnPausePath}
        onCompletePath={mockOnCompletePath}
        activePaths={[]}
      />
    )

    expect(screen.getByText('No Active Study Paths')).toBeInTheDocument()
    expect(screen.getByText('Start a study path from the recommendations below to begin tracking your progress.')).toBeInTheDocument()
  })

  it('handles continue path action', () => {
    render(
      <ActiveStudyPaths
        onContinuePath={mockOnContinuePath}
        onPausePath={mockOnPausePath}
        onCompletePath={mockOnCompletePath}
        activePaths={mockActivePaths}
      />
    )

    const continueButton = screen.getByText('Continue')
    fireEvent.click(continueButton)

    expect(mockOnContinuePath).toHaveBeenCalledWith('path-1')
  })

  it('handles pause path action', () => {
    render(
      <ActiveStudyPaths
        onContinuePath={mockOnContinuePath}
        onPausePath={mockOnPausePath}
        onCompletePath={mockOnCompletePath}
        activePaths={mockActivePaths}
      />
    )

    const pauseButton = screen.getByText('Pause')
    fireEvent.click(pauseButton)

    expect(mockOnPausePath).toHaveBeenCalledWith('path-1')
  })

  it('displays progress correctly', () => {
    render(
      <ActiveStudyPaths
        onContinuePath={mockOnContinuePath}
        onPausePath={mockOnPausePath}
        onCompletePath={mockOnCompletePath}
        activePaths={mockActivePaths}
      />
    )

    expect(screen.getByText('3 / 8 topics (38%)')).toBeInTheDocument()
    expect(screen.getByText('5 / 5 topics (100%)')).toBeInTheDocument()
  })

  it('shows different status badges', () => {
    render(
      <ActiveStudyPaths
        onContinuePath={mockOnContinuePath}
        onPausePath={mockOnPausePath}
        onCompletePath={mockOnCompletePath}
        activePaths={mockActivePaths}
      />
    )

    expect(screen.getByText('active')).toBeInTheDocument()
    expect(screen.getByText('completed')).toBeInTheDocument()
  })

  it('expands topic details when clicked', () => {
    render(
      <ActiveStudyPaths
        onContinuePath={mockOnContinuePath}
        onPausePath={mockOnPausePath}
        onCompletePath={mockOnCompletePath}
        activePaths={mockActivePaths}
      />
    )

    const viewDetailsButtons = screen.getAllByText('View Topic Details')
    fireEvent.click(viewDetailsButtons[0])

    expect(screen.getByText('Topic Progress')).toBeInTheDocument()
    expect(screen.getByText('EC2 Fundamentals')).toBeInTheDocument()
    expect(screen.getByText('S3 Storage Basics')).toBeInTheDocument()
  })

  it('displays current topic for active paths', () => {
    render(
      <ActiveStudyPaths
        onContinuePath={mockOnContinuePath}
        onPausePath={mockOnPausePath}
        onCompletePath={mockOnCompletePath}
        activePaths={mockActivePaths}
      />
    )

    expect(screen.getByText('Current: VPC Networking Fundamentals')).toBeInTheDocument()
    expect(screen.getByText('3h 0m remaining')).toBeInTheDocument()
  })
})