import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { vi } from 'vitest'
import { StudyScheduler } from '../study-scheduler'
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
import { it } from 'node:test'
import { it } from 'node:test'
import { beforeEach } from 'node:test'
import { describe } from 'node:test'

const mockExistingSessions = [
  {
    id: '1',
    title: 'EC2 Study Session',
    description: 'Review EC2 fundamentals',
    date: '2024-01-15',
    startTime: '09:00',
    duration: 60,
    type: 'content' as const,
    certification: 'AWS Solutions Architect',
    priority: 'high' as const,
    completed: false,
    reminders: true
  },
  {
    id: '2',
    title: 'S3 Practice Quiz',
    date: '2024-01-16',
    startTime: '14:00',
    duration: 30,
    type: 'quiz' as const,
    priority: 'medium' as const,
    completed: true,
    reminders: false
  }
]

describe('StudyScheduler', () => {
  const mockOnScheduleSession = vi.fn()
  const mockOnUpdateSession = vi.fn()
  const mockOnDeleteSession = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders study scheduler correctly', () => {
    render(
      <StudyScheduler
        onScheduleSession={mockOnScheduleSession}
        onUpdateSession={mockOnUpdateSession}
        onDeleteSession={mockOnDeleteSession}
        existingSessions={mockExistingSessions}
      />
    )

    expect(screen.getByText('Study Schedule')).toBeInTheDocument()
    expect(screen.getByText('Schedule Session')).toBeInTheDocument()
    expect(screen.getByText('Upcoming Sessions')).toBeInTheDocument()
  })

  it('displays existing sessions in calendar', () => {
    render(
      <StudyScheduler
        onScheduleSession={mockOnScheduleSession}
        onUpdateSession={mockOnUpdateSession}
        onDeleteSession={mockOnDeleteSession}
        existingSessions={mockExistingSessions}
      />
    )

    expect(screen.getByText('EC2 Study Session')).toBeInTheDocument()
    expect(screen.getByText('S3 Practice Quiz')).toBeInTheDocument()
  })

  it('shows new session form when schedule button clicked', () => {
    render(
      <StudyScheduler
        onScheduleSession={mockOnScheduleSession}
        onUpdateSession={mockOnUpdateSession}
        onDeleteSession={mockOnDeleteSession}
      />
    )

    const scheduleButton = screen.getByText('Schedule Session')
    fireEvent.click(scheduleButton)

    expect(screen.getByText('Schedule New Session')).toBeInTheDocument()
    expect(screen.getByLabelText('Session Title')).toBeInTheDocument()
    expect(screen.getByLabelText('Session Type')).toBeInTheDocument()
  })

  it('handles form submission for new session', async () => {
    render(
      <StudyScheduler
        onScheduleSession={mockOnScheduleSession}
        onUpdateSession={mockOnUpdateSession}
        onDeleteSession={mockOnDeleteSession}
      />
    )

    const scheduleButton = screen.getByText('Schedule Session')
    fireEvent.click(scheduleButton)

    // Fill out form
    fireEvent.change(screen.getByLabelText('Session Title'), {
      target: { value: 'Lambda Study Session' }
    })
    fireEvent.change(screen.getByLabelText('Date'), {
      target: { value: '2024-01-20' }
    })
    fireEvent.change(screen.getByLabelText('Start Time'), {
      target: { value: '10:00' }
    })

    const submitButton = screen.getByText('Schedule Session')
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(mockOnScheduleSession).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Lambda Study Session',
          date: '2024-01-20',
          startTime: '10:00'
        })
      )
    })
  })

  it('handles session editing', () => {
    render(
      <StudyScheduler
        onScheduleSession={mockOnScheduleSession}
        onUpdateSession={mockOnUpdateSession}
        onDeleteSession={mockOnDeleteSession}
        existingSessions={mockExistingSessions}
      />
    )

    const editButtons = screen.getAllByRole('button', { name: /edit/i })
    fireEvent.click(editButtons[0])

    expect(screen.getByText('Edit Session')).toBeInTheDocument()
    expect(screen.getByDisplayValue('EC2 Study Session')).toBeInTheDocument()
  })

  it('handles session completion', () => {
    render(
      <StudyScheduler
        onScheduleSession={mockOnScheduleSession}
        onUpdateSession={mockOnUpdateSession}
        onDeleteSession={mockOnDeleteSession}
        existingSessions={mockExistingSessions}
      />
    )

    const completeButtons = screen.getAllByText('✓')
    fireEvent.click(completeButtons[0])

    expect(mockOnUpdateSession).toHaveBeenCalledWith('1', { completed: true })
  })

  it('handles session deletion', () => {
    render(
      <StudyScheduler
        onScheduleSession={mockOnScheduleSession}
        onUpdateSession={mockOnUpdateSession}
        onDeleteSession={mockOnDeleteSession}
        existingSessions={mockExistingSessions}
      />
    )

    const deleteButtons = screen.getAllByRole('button', { name: /delete/i })
    fireEvent.click(deleteButtons[0])

    expect(mockOnDeleteSession).toHaveBeenCalledWith('1')
  })

  it('navigates between weeks', () => {
    render(
      <StudyScheduler
        onScheduleSession={mockOnScheduleSession}
        onUpdateSession={mockOnUpdateSession}
        onDeleteSession={mockOnDeleteSession}
      />
    )

    const nextWeekButton = screen.getByText('Next Week →')
    fireEvent.click(nextWeekButton)

    const prevWeekButton = screen.getByText('← Previous Week')
    fireEvent.click(prevWeekButton)

    // Should return to original week
    expect(screen.getByText('Next Week →')).toBeInTheDocument()
  })

  it('displays session types with correct icons', () => {
    render(
      <StudyScheduler
        onScheduleSession={mockOnScheduleSession}
        onUpdateSession={mockOnUpdateSession}
        onDeleteSession={mockOnDeleteSession}
      />
    )

    const scheduleButton = screen.getByText('Schedule Session')
    fireEvent.click(scheduleButton)

    const sessionTypeSelect = screen.getByLabelText('Session Type')
    expect(sessionTypeSelect).toBeInTheDocument()

    // Check that options contain emojis
    expect(screen.getByText('📚 Content Study')).toBeInTheDocument()
    expect(screen.getByText('🎯 Practice Quiz')).toBeInTheDocument()
  })

  it('validates required fields', () => {
    render(
      <StudyScheduler
        onScheduleSession={mockOnScheduleSession}
        onUpdateSession={mockOnUpdateSession}
        onDeleteSession={mockOnDeleteSession}
      />
    )

    const scheduleButton = screen.getByText('Schedule Session')
    fireEvent.click(scheduleButton)

    const submitButton = screen.getByText('Schedule Session')
    fireEvent.click(submitButton)

    // Form should not submit without required fields
    expect(mockOnScheduleSession).not.toHaveBeenCalled()
  })

  it('shows priority colors correctly', () => {
    render(
      <StudyScheduler
        onScheduleSession={mockOnScheduleSession}
        onUpdateSession={mockOnUpdateSession}
        onDeleteSession={mockOnDeleteSession}
        existingSessions={mockExistingSessions}
      />
    )

    // High priority session should have red styling
    const highPrioritySession = screen.getByText('EC2 Study Session').closest('div')
    expect(highPrioritySession).toHaveClass('bg-red-100')

    // Medium priority session should have yellow styling
    const mediumPrioritySession = screen.getByText('S3 Practice Quiz').closest('div')
    expect(mediumPrioritySession).toHaveClass('bg-yellow-100')
  })

  it('handles reminder toggle', () => {
    render(
      <StudyScheduler
        onScheduleSession={mockOnScheduleSession}
        onUpdateSession={mockOnUpdateSession}
        onDeleteSession={mockOnDeleteSession}
      />
    )

    const scheduleButton = screen.getByText('Schedule Session')
    fireEvent.click(scheduleButton)

    const reminderCheckbox = screen.getByLabelText('Enable reminders')
    expect(reminderCheckbox).toBeChecked() // Should be checked by default

    fireEvent.click(reminderCheckbox)
    expect(reminderCheckbox).not.toBeChecked()
  })

  it('displays completed sessions with strikethrough', () => {
    render(
      <StudyScheduler
        onScheduleSession={mockOnScheduleSession}
        onUpdateSession={mockOnUpdateSession}
        onDeleteSession={mockOnDeleteSession}
        existingSessions={mockExistingSessions}
      />
    )

    const completedSession = screen.getByText('S3 Practice Quiz').closest('div')
    expect(completedSession).toHaveClass('line-through')
  })
})