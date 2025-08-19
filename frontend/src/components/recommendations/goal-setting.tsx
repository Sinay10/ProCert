'use client'

import { useState, useEffect } from 'react'
import { Target, Calendar, Clock, Award, TrendingUp, Plus, Edit2, Trash2, CheckCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'

interface StudyGoal {
  id: string
  title: string
  description?: string
  type: 'certification' | 'skill' | 'time' | 'score' | 'streak'
  targetValue: number
  currentValue: number
  unit: string
  deadline?: string
  priority: 'low' | 'medium' | 'high'
  status: 'active' | 'completed' | 'paused'
  createdAt: string
  milestones: Array<{
    value: number
    label: string
    completed: boolean
    completedAt?: string
  }>
}

interface GoalSettingProps {
  onCreateGoal: (goal: Omit<StudyGoal, 'id' | 'currentValue' | 'status' | 'createdAt'>) => void
  onUpdateGoal: (goalId: string, updates: Partial<StudyGoal>) => void
  onDeleteGoal: (goalId: string) => void
  existingGoals?: StudyGoal[]
  userProgress?: {
    totalStudyTime: number
    quizzesCompleted: number
    averageScore: number
    streakDays: number
  }
}

const goalTypes = [
  { value: 'certification', label: 'Certification Goal', icon: '🏆', description: 'Pass a specific certification' },
  { value: 'skill', label: 'Skill Mastery', icon: '🎯', description: 'Master a particular skill area' },
  { value: 'time', label: 'Study Time', icon: '⏰', description: 'Achieve study time targets' },
  { value: 'score', label: 'Quiz Performance', icon: '📊', description: 'Improve quiz scores' },
  { value: 'streak', label: 'Study Streak', icon: '🔥', description: 'Maintain consistent study habits' }
]

const priorityColors = {
  low: 'bg-green-100 text-green-800 border-green-200',
  medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  high: 'bg-red-100 text-red-800 border-red-200'
}

export function GoalSetting({
  onCreateGoal,
  onUpdateGoal,
  onDeleteGoal,
  existingGoals = [],
  userProgress
}: GoalSettingProps) {
  const [goals, setGoals] = useState<StudyGoal[]>(existingGoals)
  const [showNewGoalForm, setShowNewGoalForm] = useState(false)
  const [editingGoal, setEditingGoal] = useState<string | null>(null)

  // Form state
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    type: 'certification' as StudyGoal['type'],
    targetValue: 100,
    unit: 'percent',
    deadline: '',
    priority: 'medium' as StudyGoal['priority'],
    milestones: [] as Array<{ value: number; label: string }>
  })

  useEffect(() => {
    setGoals(existingGoals)
  }, [existingGoals])

  const resetForm = () => {
    setFormData({
      title: '',
      description: '',
      type: 'certification',
      targetValue: 100,
      unit: 'percent',
      deadline: '',
      priority: 'medium',
      milestones: []
    })
  }

  const getUnitOptions = (type: StudyGoal['type']) => {
    switch (type) {
      case 'certification':
        return [{ value: 'percent', label: '% Ready' }]
      case 'skill':
        return [{ value: 'percent', label: '% Mastery' }]
      case 'time':
        return [
          { value: 'hours', label: 'Hours' },
          { value: 'minutes', label: 'Minutes' }
        ]
      case 'score':
        return [{ value: 'percent', label: '% Score' }]
      case 'streak':
        return [{ value: 'days', label: 'Days' }]
      default:
        return [{ value: 'percent', label: '%' }]
    }
  }

  const generateDefaultMilestones = (type: StudyGoal['type'], targetValue: number) => {
    switch (type) {
      case 'certification':
      case 'skill':
        return [
          { value: targetValue * 0.25, label: '25% Progress' },
          { value: targetValue * 0.5, label: '50% Progress' },
          { value: targetValue * 0.75, label: '75% Progress' }
        ]
      case 'time':
        return [
          { value: targetValue * 0.3, label: '30% Complete' },
          { value: targetValue * 0.6, label: '60% Complete' },
          { value: targetValue * 0.9, label: '90% Complete' }
        ]
      case 'score':
        return [
          { value: Math.min(70, targetValue * 0.7), label: 'Passing Score' },
          { value: Math.min(85, targetValue * 0.85), label: 'Good Score' }
        ]
      case 'streak':
        return [
          { value: Math.max(7, targetValue * 0.25), label: 'First Week' },
          { value: Math.max(30, targetValue * 0.5), label: 'One Month' }
        ]
      default:
        return []
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    const milestones = formData.milestones.length > 0 
      ? formData.milestones 
      : generateDefaultMilestones(formData.type, formData.targetValue)

    const goalData = {
      ...formData,
      milestones: milestones.map(m => ({ ...m, completed: false }))
    }
    
    if (editingGoal) {
      onUpdateGoal(editingGoal, goalData)
      setEditingGoal(null)
    } else {
      onCreateGoal(goalData)
    }
    
    resetForm()
    setShowNewGoalForm(false)
  }

  const handleEdit = (goal: StudyGoal) => {
    setFormData({
      title: goal.title,
      description: goal.description || '',
      type: goal.type,
      targetValue: goal.targetValue,
      unit: goal.unit,
      deadline: goal.deadline || '',
      priority: goal.priority,
      milestones: goal.milestones.map(m => ({ value: m.value, label: m.label }))
    })
    setEditingGoal(goal.id)
    setShowNewGoalForm(true)
  }

  const calculateProgress = (goal: StudyGoal) => {
    return Math.min(100, (goal.currentValue / goal.targetValue) * 100)
  }

  const getGoalIcon = (type: StudyGoal['type']) => {
    const goalType = goalTypes.find(gt => gt.value === type)
    return goalType?.icon || '🎯'
  }

  const isGoalOverdue = (goal: StudyGoal) => {
    if (!goal.deadline) return false
    return new Date(goal.deadline) < new Date() && goal.status !== 'completed'
  }

  const activeGoals = goals.filter(g => g.status === 'active')
  const completedGoals = goals.filter(g => g.status === 'completed')

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-900">Study Goals</h2>
        <Button
          onClick={() => setShowNewGoalForm(true)}
          className="flex items-center space-x-2"
        >
          <Plus className="w-4 h-4" />
          <span>Set New Goal</span>
        </Button>
      </div>

      {/* Goal Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="p-4">
          <div className="flex items-center space-x-3">
            <Target className="w-8 h-8 text-blue-600" />
            <div>
              <div className="text-2xl font-bold text-gray-900">{activeGoals.length}</div>
              <div className="text-sm text-gray-600">Active Goals</div>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center space-x-3">
            <CheckCircle className="w-8 h-8 text-green-600" />
            <div>
              <div className="text-2xl font-bold text-gray-900">{completedGoals.length}</div>
              <div className="text-sm text-gray-600">Completed Goals</div>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center space-x-3">
            <TrendingUp className="w-8 h-8 text-purple-600" />
            <div>
              <div className="text-2xl font-bold text-gray-900">
                {activeGoals.length > 0 
                  ? Math.round(activeGoals.reduce((acc, goal) => acc + calculateProgress(goal), 0) / activeGoals.length)
                  : 0}%
              </div>
              <div className="text-sm text-gray-600">Avg Progress</div>
            </div>
          </div>
        </Card>
      </div>

      {/* Active Goals */}
      {activeGoals.length > 0 && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Active Goals</h3>
          <div className="space-y-4">
            {activeGoals.map((goal) => {
              const progress = calculateProgress(goal)
              const overdue = isGoalOverdue(goal)
              
              return (
                <div key={goal.id} className={`p-4 border rounded-lg ${overdue ? 'border-red-200 bg-red-50' : 'border-gray-200'}`}>
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center space-x-3">
                      <span className="text-2xl">{getGoalIcon(goal.type)}</span>
                      <div>
                        <h4 className="font-medium text-gray-900">{goal.title}</h4>
                        {goal.description && (
                          <p className="text-sm text-gray-600">{goal.description}</p>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className={`px-2 py-1 text-xs rounded-full ${priorityColors[goal.priority]}`}>
                        {goal.priority}
                      </span>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleEdit(goal)}
                      >
                        <Edit2 className="w-3 h-3" />
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => onDeleteGoal(goal.id)}
                      >
                        <Trash2 className="w-3 h-3" />
                      </Button>
                    </div>
                  </div>

                  {/* Progress Bar */}
                  <div className="mb-3">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-gray-700">Progress</span>
                      <span className="text-sm text-gray-600">
                        {goal.currentValue} / {goal.targetValue} {goal.unit}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full transition-all duration-300 ${
                          progress >= 100 ? 'bg-green-600' : 'bg-blue-600'
                        }`}
                        style={{ width: `${Math.min(100, progress)}%` }}
                      ></div>
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      {Math.round(progress)}% complete
                    </div>
                  </div>

                  {/* Milestones */}
                  {goal.milestones.length > 0 && (
                    <div className="mb-3">
                      <h5 className="text-sm font-medium text-gray-700 mb-2">Milestones</h5>
                      <div className="flex flex-wrap gap-2">
                        {goal.milestones.map((milestone, index) => (
                          <div
                            key={index}
                            className={`px-2 py-1 text-xs rounded-full border ${
                              milestone.completed
                                ? 'bg-green-100 text-green-800 border-green-200'
                                : goal.currentValue >= milestone.value
                                ? 'bg-blue-100 text-blue-800 border-blue-200'
                                : 'bg-gray-100 text-gray-600 border-gray-200'
                            }`}
                          >
                            {milestone.completed ? '✓' : ''} {milestone.label}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Goal Details */}
                  <div className="flex items-center space-x-4 text-sm text-gray-600">
                    {goal.deadline && (
                      <div className={`flex items-center space-x-1 ${overdue ? 'text-red-600' : ''}`}>
                        <Calendar className="w-4 h-4" />
                        <span>Due: {new Date(goal.deadline).toLocaleDateString()}</span>
                        {overdue && <span className="text-red-600 font-medium">(Overdue)</span>}
                      </div>
                    )}
                    <div className="flex items-center space-x-1">
                      <Clock className="w-4 h-4" />
                      <span>Created: {new Date(goal.createdAt).toLocaleDateString()}</span>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </Card>
      )}

      {/* Completed Goals */}
      {completedGoals.length > 0 && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Completed Goals</h3>
          <div className="space-y-3">
            {completedGoals.slice(0, 3).map((goal) => (
              <div key={goal.id} className="flex items-center space-x-3 p-3 bg-green-50 rounded-lg">
                <CheckCircle className="w-5 h-5 text-green-600" />
                <div className="flex-1">
                  <h4 className="font-medium text-gray-900">{goal.title}</h4>
                  <div className="text-sm text-gray-600">
                    Completed on {new Date(goal.createdAt).toLocaleDateString()}
                  </div>
                </div>
                <span className="text-2xl">{getGoalIcon(goal.type)}</span>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* New/Edit Goal Form */}
      {showNewGoalForm && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            {editingGoal ? 'Edit Goal' : 'Set New Goal'}
          </h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Goal Type
              </label>
              <select
                value={formData.type}
                onChange={(e) => {
                  const newType = e.target.value as StudyGoal['type']
                  const unitOptions = getUnitOptions(newType)
                  setFormData({ 
                    ...formData, 
                    type: newType,
                    unit: unitOptions[0]?.value || 'percent'
                  })
                }}
                className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                {goalTypes.map((type) => (
                  <option key={type.value} value={type.value}>
                    {type.icon} {type.label} - {type.description}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Goal Title
              </label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                placeholder="e.g., Pass AWS Solutions Architect Associate"
                className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description (Optional)
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Additional details about your goal..."
                className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                rows={2}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Target Value
                </label>
                <input
                  type="number"
                  value={formData.targetValue}
                  onChange={(e) => setFormData({ ...formData, targetValue: parseInt(e.target.value) })}
                  className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  min="1"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Unit
                </label>
                <select
                  value={formData.unit}
                  onChange={(e) => setFormData({ ...formData, unit: e.target.value })}
                  className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  {getUnitOptions(formData.type).map((unit) => (
                    <option key={unit.value} value={unit.value}>
                      {unit.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Deadline (Optional)
                </label>
                <input
                  type="date"
                  value={formData.deadline}
                  onChange={(e) => setFormData({ ...formData, deadline: e.target.value })}
                  className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Priority
                </label>
                <select
                  value={formData.priority}
                  onChange={(e) => setFormData({ ...formData, priority: e.target.value as StudyGoal['priority'] })}
                  className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="low">Low Priority</option>
                  <option value="medium">Medium Priority</option>
                  <option value="high">High Priority</option>
                </select>
              </div>
            </div>

            <div className="flex space-x-3 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setShowNewGoalForm(false)
                  setEditingGoal(null)
                  resetForm()
                }}
              >
                Cancel
              </Button>
              <Button type="submit">
                {editingGoal ? 'Update Goal' : 'Create Goal'}
              </Button>
            </div>
          </form>
        </Card>
      )}

      {/* Empty State */}
      {goals.length === 0 && !showNewGoalForm && (
        <Card className="p-8 text-center">
          <Target className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Goals Set</h3>
          <p className="text-gray-600 mb-4">
            Set study goals to track your progress and stay motivated on your certification journey.
          </p>
          <Button onClick={() => setShowNewGoalForm(true)}>
            <Plus className="w-4 h-4 mr-2" />
            Set Your First Goal
          </Button>
        </Card>
      )}
    </div>
  )
}