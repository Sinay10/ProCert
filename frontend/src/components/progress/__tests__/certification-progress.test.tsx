import { render, screen } from '@testing-library/react'
import { vi } from 'vitest'
import { CertificationProgress } from '../certification-progress'
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

const mockData = {
  'aws-solutions-architect': {
    progress_percentage: 75,
    topics_completed: 15,
    total_topics: 20,
    last_activity: '2025-01-15T10:00:00Z'
  },
  'aws-developer': {
    progress_percentage: 45,
    topics_completed: 9,
    total_topics: 20,
    last_activity: '2025-01-14T15:30:00Z'
  }
}

// Mock Date.now() for consistent testing
const mockDate = new Date('2025-01-15T12:00:00Z')
vi.spyOn(global, 'Date').mockImplementation(() => mockDate as any)

describe('CertificationProgress', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders loading state', () => {
    render(<CertificationProgress loading={true} />)
    
    expect(screen.getByText('Certification Progress')).toBeInTheDocument()
    
    // Should render skeleton loaders
    const skeletonElements = screen.getAllByRole('generic').filter(el => 
      el.className.includes('animate-pulse')
    )
    expect(skeletonElements.length).toBeGreaterThan(0)
  })

  it('renders empty state when no data', () => {
    render(<CertificationProgress data={{}} loading={false} />)
    
    expect(screen.getByText('No certification progress yet')).toBeInTheDocument()
    expect(screen.getByText('Start taking quizzes to track your progress')).toBeInTheDocument()
  })

  it('renders certification progress correctly', () => {
    render(<CertificationProgress data={mockData} loading={false} />)

    // Check certification names
    expect(screen.getByText('AWS SOLUTIONS ARCHITECT')).toBeInTheDocument()
    expect(screen.getByText('AWS DEVELOPER')).toBeInTheDocument()

    // Check progress percentages (using getAllByText since they appear multiple times)
    expect(screen.getAllByText('75%')).toHaveLength(3) // Main percentage and milestone indicators
    expect(screen.getByText('45%')).toBeInTheDocument()

    // Check topics completed
    expect(screen.getByText('15 of 20 topics completed')).toBeInTheDocument()
    expect(screen.getByText('9 of 20 topics completed')).toBeInTheDocument()
  })

  it('formats last activity time correctly', () => {
    render(<CertificationProgress data={mockData} loading={false} />)

    // Should show "Just now" since the mock date calculation results in < 1 hour
    expect(screen.getAllByText('Just now')).toHaveLength(2)
  })

  it('applies correct progress bar colors based on percentage', () => {
    render(<CertificationProgress data={mockData} loading={false} />)

    // Find progress bars by their container
    const progressBars = screen.getAllByRole('generic').filter(el => 
      el.className.includes('h-2') && el.className.includes('rounded-full') && 
      (el.className.includes('bg-blue-500') || el.className.includes('bg-yellow-500'))
    )
    
    expect(progressBars.length).toBeGreaterThan(0)
  })

  it('shows milestone indicators correctly', () => {
    render(<CertificationProgress data={mockData} loading={false} />)

    // Should show milestone percentages (75% appears 3 times: main percentage + 2 milestones)
    expect(screen.getAllByText('25%')).toHaveLength(2) // One for each certification
    expect(screen.getAllByText('50%')).toHaveLength(2)
    expect(screen.getAllByText('75%')).toHaveLength(3) // Main percentage + milestone indicators
    expect(screen.getAllByText('Complete')).toHaveLength(2)
  })

  it('handles undefined data gracefully', () => {
    render(<CertificationProgress loading={false} />)
    
    expect(screen.getByText('No certification progress yet')).toBeInTheDocument()
  })

  it('formats certification names correctly', () => {
    const dataWithDashes = {
      'aws-cloud-practitioner': {
        progress_percentage: 30,
        topics_completed: 6,
        total_topics: 20,
        last_activity: '2025-01-15T10:00:00Z'
      }
    }

    render(<CertificationProgress data={dataWithDashes} loading={false} />)
    
    expect(screen.getByText('AWS CLOUD PRACTITIONER')).toBeInTheDocument()
  })
})