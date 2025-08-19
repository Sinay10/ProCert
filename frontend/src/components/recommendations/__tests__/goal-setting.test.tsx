import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { vi } from 'vitest'
import { GoalSetting } from '../goal-setting'
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
import { it } from 'node:test'
import { it } from 'node:test'
import { beforeEach } from 'node:test'
import { describe } from 'node:test'

const mockExistingGoals = [
  {
    id: '1',
    title: 'Pass AWS Solutions Architect',
    description: 'Achieve certification within 3 months',
    type: 'certification' as const,
    targetValue: 100,
    currentValue: 75,
    unit: 'percent',
    deadline: '2024-03-01',
    priority: 'high' as const,
    status: 'active' as const,
    createdAt: '2024-01-01T00:00:00Z',
    milestones: [
      { value: 25, label: '25% Progress', completed: true, completedAt: '2024-01-15T00:00:00Z' },
      { value: 50, label: '50% Progress', completed: true, completedAt: '2024-01-30T00:00:00Z' },
      { value: 75, label: '75% Progress', completed: false }
    ]
  },
  {
    id: '2',
    title: 'Study 100 Hours',
    type: 'time' as const,
    targetValue: 100,
    currentValue: 100,
    unit: 'hours',
    priority: 'medium' as const,
    status: 'completed' as const,
    createdAt: '2023-12-01T00:00:00Z',
    milestones: []
  }
]

const mockUserProgress = {
  totalStudyTime: 120,
  quizzesCompleted: 15,
  averageScore: 78,
  streakDays: 5
}

describe('GoalSetting', () => {
  const mockOnCreateGoal = vi.fn()
  const mockOnUpdateGoal = vi.fn()
  const mockOnDeleteGoal = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders goal setting interface correctly', () => {
    render(
      <GoalSetting
        onCreateGoal={mockOnCreateGoal}
        onUpdateGoal={mockOnUpdateGoal}
        onDeleteGoal={mockOnDeleteGoal}
        existingGoals={mockExistingGoals}
        userProgress={mockUserProgress}
      />
    )

    expect(screen.getByText('Study Goals')).toBeInTheDocument()
    expect(screen.getByText('Set New Goal')).toBeInTheDocument()
    expect(screen.getByText('Active Goals')).toBeInTheDocument()
    expect(screen.getByText('Completed Goals')).toBeInTheDocument()
  })

  it('displays goal overview statistics', () => {
    render(
      <GoalSetting
        onCreateGoal={mockOnCreateGoal}
        onUpdateGoal={mockOnUpdateGoal}
        onDeleteGoal={mockOnDeleteGoal}
        existingGoals={mockExistingGoals}
        userProgress={mockUserProgress}
      />
    )

    expect(screen.getByText('1')).toBeInTheDocument() // Active goals count
    expect(screen.getByText('Active Goals')).toBeInTheDocument()
    expect(screen.getByText('Completed Goals')).toBeInTheDocument()
    expect(screen.getByText('75%')).toBeInTheDocument() // Average progress
  })

  it('displays active goals with progress bars', () => {
    render(
      <GoalSetting
        onCreateGoal={mockOnCreateGoal}
        onUpdateGoal={mockOnUpdateGoal}
        onDeleteGoal={mockOnDeleteGoal}
        existingGoals={mockExistingGoals}
        userProgress={mockUserProgress}
      />
    )

    expect(screen.getByText('Pass AWS Solutions Architect')).toBeInTheDocument()
    expect(screen.getByText('Achieve certification within 3 months')).toBeInTheDocument()
    expect(screen.getByText('75 / 100 percent')).toBeInTheDocument()
    expect(screen.getByText('75% complete')).toBeInTheDocument()
  })

  it('shows milestone progress', () => {
    render(
      <GoalSetting
        onCreateGoal={mockOnCreateGoal}
        onUpdateGoal={mockOnUpdateGoal}
        onDeleteGoal={mockOnDeleteGoal}
        existingGoals={mockExistingGoals}
        userProgress={mockUserProgress}
      />
    )

    expect(screen.getByText('Milestones')).toBeInTheDocument()
    expect(screen.getByText('✓ 25% Progress')).toBeInTheDocument()
    expect(screen.getByText('✓ 50% Progress')).toBeInTheDocument()
    expect(screen.getByText('75% Progress')).toBeInTheDocument()
  })

  it('shows new goal form when button clicked', () => {
    render(
      <GoalSetting
        onCreateGoal={mockOnCreateGoal}
        onUpdateGoal={mockOnUpdateGoal}
        onDeleteGoal={mockOnDeleteGoal}
        existingGoals={[]}
        userProgress={mockUserProgress}
      />
    )

    const setGoalButton = screen.getByText('Set New Goal')
    fireEvent.click(setGoalButton)

    expect(screen.getByText('Set New Goal')).toBeInTheDocument()
    expect(screen.getByLabelText('Goal Type')).toBeInTheDocument()
    expect(screen.getByLabelText('Goal Title')).toBeInTheDocument()
  })

  it('handles goal creation', async () => {
    render(
      <GoalSetting
        onCreateGoal={mockOnCreateGoal}
        onUpdateGoal={mockOnUpdateGoal}
        onDeleteGoal={mockOnDeleteGoal}
        existingGoals={[]}
        userProgress={mockUserProgress}
      />
    )

    const setGoalButton = screen.getByText('Set New Goal')
    fireEvent.click(setGoalButton)

    // Fill out form
    fireEvent.change(screen.getByLabelText('Goal Title'), {
      target: { value: 'Master Lambda Functions' }
    })
    fireEvent.change(screen.getByLabelText('Target Value'), {
      target: { value: '90' }
    })
    fireEvent.change(screen.getByLabelText('Deadline (Optional)'), {
      target: { value: '2024-06-01' }
    })

    const createButton = screen.getByText('Create Goal')
    fireEvent.click(createButton)

    await waitFor(() => {
      expect(mockOnCreateGoal).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Master Lambda Functions',
          targetValue: 90,
          deadline: '2024-06-01'
        })
      )
    })
  })

  it('handles goal editing', () => {
    render(
      <GoalSetting
        onCreateGoal={mockOnCreateGoal}
        onUpdateGoal={mockOnUpdateGoal}
        onDeleteGoal={mockOnDeleteGoal}
        existingGoals={mockExistingGoals}
        userProgress={mockUserProgress}
      />
    )

    const editButtons = screen.getAllByRole('button', { name: /edit/i })
    fireEvent.click(editButtons[0])

    expect(screen.getByText('Edit Goal')).toBeInTheDocument()
    expect(screen.getByDisplayValue('Pass AWS Solutions Architect')).toBeInTheDocument()
  })

  it('handles goal deletion', () => {
    render(
      <GoalSetting
        onCreateGoal={mockOnCreateGoal}
        onUpdateGoal={mockOnUpdateGoal}
        onDeleteGoal={mockOnDeleteGoal}
        existingGoals={mockExistingGoals}
        userProgress={mockUserProgress}
      />
    )

    const deleteButtons = screen.getAllByRole('button', { name: /delete/i })
    fireEvent.click(deleteButtons[0])

    expect(mockOnDeleteGoal).toHaveBeenCalledWith('1')
  })

  it('shows different goal types with correct icons', () => {
    render(
      <GoalSetting
        onCreateGoal={mockOnCreateGoal}
        onUpdateGoal={mockOnUpdateGoal}
        onDeleteGoal={mockOnDeleteGoal}
        existingGoals={[]}
        userProgress={mockUserProgress}
      />
    )

    const setGoalButton = screen.getByText('Set New Goal')
    fireEvent.click(setGoalButton)

    const goalTypeSelect = screen.getByLabelText('Goal Type')
    expect(goalTypeSelect).toBeInTheDocument()

    expect(screen.getByText('🏆 Certification Goal - Pass a specific certification')).toBeInTheDocument()
    expect(screen.getByText('🎯 Skill Mastery - Master a particular skill area')).toBeInTheDocument()
    expect(screen.getByText('⏰ Study Time - Achieve study time targets')).toBeInTheDocument()
  })

  it('updates unit options based on goal type', () => {
    render(
      <GoalSetting
        onCreateGoal={mockOnCreateGoal}
        onUpdateGoal={mockOnUpdateGoal}
        onDeleteGoal={mockOnDeleteGoal}
        existingGoals={[]}
        userProgress={mockUserProgress}
      />
    )

    const setGoalButton = screen.getByText('Set New Goal')
    fireEvent.click(setGoalButton)

    const goalTypeSelect = screen.getByLabelText('Goal Type')
    fireEvent.change(goalTypeSelect, { target: { value: 'time' } })

    const unitSelect = screen.getByLabelText('Unit')
    expect(screen.getByText('Hours')).toBeInTheDocument()
    expect(screen.getByText('Minutes')).toBeInTheDocument()
  })

  it('shows overdue goals with warning styling', () => {
    const overdueGoal = {
      ...mockExistingGoals[0],
      deadline: '2023-12-01' // Past date
    }

    render(
      <GoalSetting
        onCreateGoal={mockOnCreateGoal}
        onUpdateGoal={mockOnUpdateGoal}
        onDeleteGoal={mockOnDeleteGoal}
        existingGoals={[overdueGoal]}
        userProgress={mockUserProgress}
      />
    )

    expect(screen.getByText('(Overdue)')).toBeInTheDocument()
  })

  it('displays completed goals section', () => {
    render(
      <GoalSetting
        onCreateGoal={mockOnCreateGoal}
        onUpdateGoal={mockOnUpdateGoal}
        onDeleteGoal={mockOnDeleteGoal}
        existingGoals={mockExistingGoals}
        userProgress={mockUserProgress}
      />
    )

    expect(screen.getByText('Study 100 Hours')).toBeInTheDocument()
    expect(screen.getByText('Completed on 12/1/2023')).toBeInTheDocument()
  })

  it('shows empty state when no goals exist', () => {
    render(
      <GoalSetting
        onCreateGoal={mockOnCreateGoal}
        onUpdateGoal={mockOnUpdateGoal}
        onDeleteGoal={mockOnDeleteGoal}
        existingGoals={[]}
        userProgress={mockUserProgress}
      />
    )

    expect(screen.getByText('No Goals Set')).toBeInTheDocument()
    expect(screen.getByText('Set study goals to track your progress and stay motivated on your certification journey.')).toBeInTheDocument()
    expect(screen.getByText('Set Your First Goal')).toBeInTheDocument()
  })

  it('validates required fields in goal form', () => {
    render(
      <GoalSetting
        onCreateGoal={mockOnCreateGoal}
        onUpdateGoal={mockOnUpdateGoal}
        onDeleteGoal={mockOnDeleteGoal}
        existingGoals={[]}
        userProgress={mockUserProgress}
      />
    )

    const setGoalButton = screen.getByText('Set New Goal')
    fireEvent.click(setGoalButton)

    const createButton = screen.getByText('Create Goal')
    fireEvent.click(createButton)

    // Should not call create function without required fields
    expect(mockOnCreateGoal).not.toHaveBeenCalled()
  })

  it('displays priority colors correctly', () => {
    render(
      <GoalSetting
        onCreateGoal={mockOnCreateGoal}
        onUpdateGoal={mockOnUpdateGoal}
        onDeleteGoal={mockOnDeleteGoal}
        existingGoals={mockExistingGoals}
        userProgress={mockUserProgress}
      />
    )

    const highPriorityBadge = screen.getByText('high')
    expect(highPriorityBadge).toHaveClass('bg-red-100')
  })
})