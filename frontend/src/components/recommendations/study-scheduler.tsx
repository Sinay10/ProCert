'use client'

import { useState, useEffect } from 'react'
import { Calendar, Clock, Target, Plus, Edit2, Trash2, Bell } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'

interface StudySession {
  id: string
  title: string
  description?: string
  date: string
  startTime: string
  duration: number // in minutes
  type: 'quiz' | 'content' | 'review' | 'practice'
  certification?: string
  priority: 'low' | 'medium' | 'high'
  completed: boolean
  reminders: boolean
}

interface StudySchedulerProps {
  onScheduleSession: (session: Omit<StudySession, 'id' | 'completed'>) => void
  onUpdateSession: (sessionId: string, updates: Partial<StudySession>) => void
  onDeleteSession: (sessionId: string) => void
  existingSessions?: StudySession[]
}

const sessionTypes = [
  { value: 'quiz', label: 'Practice Quiz', icon: '🎯' },
  { value: 'content', label: 'Content Study', icon: '📚' },
  { value: 'review', label: 'Review Session', icon: '🔄' },
  { value: 'practice', label: 'Hands-on Practice', icon: '⚡' }
]

const priorityColors = {
  low: 'bg-green-100 text-green-800 border-green-200',
  medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  high: 'bg-red-100 text-red-800 border-red-200'
}

export function StudyScheduler({
  onScheduleSession,
  onUpdateSession,
  onDeleteSession,
  existingSessions = []
}: StudySchedulerProps) {
  const [sessions, setSessions] = useState<StudySession[]>(existingSessions)
  const [showNewSessionForm, setShowNewSessionForm] = useState(false)
  const [editingSession, setEditingSession] = useState<string | null>(null)
  const [selectedWeek, setSelectedWeek] = useState(new Date())

  // Form state
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    date: '',
    startTime: '',
    duration: 60,
    type: 'content' as StudySession['type'],
    certification: '',
    priority: 'medium' as StudySession['priority'],
    reminders: true
  })

  useEffect(() => {
    setSessions(existingSessions)
  }, [existingSessions])

  const resetForm = () => {
    setFormData({
      title: '',
      description: '',
      date: '',
      startTime: '',
      duration: 60,
      type: 'content',
      certification: '',
      priority: 'medium',
      reminders: true
    })
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    if (editingSession) {
      onUpdateSession(editingSession, formData)
      setEditingSession(null)
    } else {
      onScheduleSession(formData)
    }
    
    resetForm()
    setShowNewSessionForm(false)
  }

  const handleEdit = (session: StudySession) => {
    setFormData({
      title: session.title,
      description: session.description || '',
      date: session.date,
      startTime: session.startTime,
      duration: session.duration,
      type: session.type,
      certification: session.certification || '',
      priority: session.priority,
      reminders: session.reminders
    })
    setEditingSession(session.id)
    setShowNewSessionForm(true)
  }

  const handleComplete = (sessionId: string) => {
    onUpdateSession(sessionId, { completed: true })
  }

  const getWeekDates = (date: Date) => {
    const week = []
    const startOfWeek = new Date(date)
    startOfWeek.setDate(date.getDate() - date.getDay())
    
    for (let i = 0; i < 7; i++) {
      const day = new Date(startOfWeek)
      day.setDate(startOfWeek.getDate() + i)
      week.push(day)
    }
    return week
  }

  const getSessionsForDate = (date: Date) => {
    const dateStr = date.toISOString().split('T')[0]
    return sessions.filter(session => session.date === dateStr)
  }

  const weekDates = getWeekDates(selectedWeek)
  const today = new Date().toISOString().split('T')[0]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-900">Study Schedule</h2>
        <Button
          onClick={() => setShowNewSessionForm(true)}
          className="flex items-center space-x-2"
        >
          <Plus className="w-4 h-4" />
          <span>Schedule Session</span>
        </Button>
      </div>

      {/* Week Navigation */}
      <Card className="p-4">
        <div className="flex items-center justify-between mb-4">
          <Button
            variant="outline"
            onClick={() => {
              const prevWeek = new Date(selectedWeek)
              prevWeek.setDate(selectedWeek.getDate() - 7)
              setSelectedWeek(prevWeek)
            }}
          >
            ← Previous Week
          </Button>
          <h3 className="font-medium text-gray-900">
            {weekDates[0].toLocaleDateString()} - {weekDates[6].toLocaleDateString()}
          </h3>
          <Button
            variant="outline"
            onClick={() => {
              const nextWeek = new Date(selectedWeek)
              nextWeek.setDate(selectedWeek.getDate() + 7)
              setSelectedWeek(nextWeek)
            }}
          >
            Next Week →
          </Button>
        </div>

        {/* Calendar Grid */}
        <div className="grid grid-cols-7 gap-2">
          {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((day) => (
            <div key={day} className="text-center text-sm font-medium text-gray-600 p-2">
              {day}
            </div>
          ))}
          
          {weekDates.map((date) => {
            const dateStr = date.toISOString().split('T')[0]
            const daySessions = getSessionsForDate(date)
            const isToday = dateStr === today
            
            return (
              <div
                key={dateStr}
                className={`min-h-24 p-2 border rounded-lg ${
                  isToday ? 'bg-blue-50 border-blue-200' : 'bg-gray-50 border-gray-200'
                }`}
              >
                <div className={`text-sm font-medium mb-1 ${
                  isToday ? 'text-blue-900' : 'text-gray-900'
                }`}>
                  {date.getDate()}
                </div>
                <div className="space-y-1">
                  {daySessions.map((session) => (
                    <div
                      key={session.id}
                      className={`text-xs p-1 rounded cursor-pointer hover:opacity-80 ${
                        session.completed 
                          ? 'bg-green-100 text-green-800 line-through' 
                          : priorityColors[session.priority]
                      }`}
                      onClick={() => handleEdit(session)}
                    >
                      <div className="font-medium truncate">{session.title}</div>
                      <div className="flex items-center space-x-1">
                        <Clock className="w-3 h-3" />
                        <span>{session.startTime}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      </Card>

      {/* Upcoming Sessions */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Upcoming Sessions</h3>
        <div className="space-y-3">
          {sessions
            .filter(session => !session.completed && session.date >= today)
            .sort((a, b) => new Date(a.date + ' ' + a.startTime).getTime() - new Date(b.date + ' ' + b.startTime).getTime())
            .slice(0, 5)
            .map((session) => (
              <div key={session.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex-1">
                  <div className="flex items-center space-x-3">
                    <span className="text-lg">
                      {sessionTypes.find(t => t.value === session.type)?.icon}
                    </span>
                    <div>
                      <h4 className="font-medium text-gray-900">{session.title}</h4>
                      <div className="flex items-center space-x-4 text-sm text-gray-600">
                        <div className="flex items-center space-x-1">
                          <Calendar className="w-4 h-4" />
                          <span>{new Date(session.date).toLocaleDateString()}</span>
                        </div>
                        <div className="flex items-center space-x-1">
                          <Clock className="w-4 h-4" />
                          <span>{session.startTime} ({session.duration}min)</span>
                        </div>
                        <span className={`px-2 py-1 text-xs rounded-full ${priorityColors[session.priority]}`}>
                          {session.priority}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleEdit(session)}
                  >
                    <Edit2 className="w-3 h-3" />
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleComplete(session.id)}
                  >
                    ✓
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => onDeleteSession(session.id)}
                  >
                    <Trash2 className="w-3 h-3" />
                  </Button>
                </div>
              </div>
            ))}
        </div>
      </Card>

      {/* New/Edit Session Form */}
      {showNewSessionForm && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            {editingSession ? 'Edit Session' : 'Schedule New Session'}
          </h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Session Title
                </label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Session Type
                </label>
                <select
                  value={formData.type}
                  onChange={(e) => setFormData({ ...formData, type: e.target.value as StudySession['type'] })}
                  className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  {sessionTypes.map((type) => (
                    <option key={type.value} value={type.value}>
                      {type.icon} {type.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description (Optional)
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                rows={2}
              />
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Date
                </label>
                <input
                  type="date"
                  value={formData.date}
                  onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                  className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Start Time
                </label>
                <input
                  type="time"
                  value={formData.startTime}
                  onChange={(e) => setFormData({ ...formData, startTime: e.target.value })}
                  className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Duration (minutes)
                </label>
                <input
                  type="number"
                  value={formData.duration}
                  onChange={(e) => setFormData({ ...formData, duration: parseInt(e.target.value) })}
                  className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  min="15"
                  step="15"
                  required
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Priority
                </label>
                <select
                  value={formData.priority}
                  onChange={(e) => setFormData({ ...formData, priority: e.target.value as StudySession['priority'] })}
                  className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="low">Low Priority</option>
                  <option value="medium">Medium Priority</option>
                  <option value="high">High Priority</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Certification (Optional)
                </label>
                <input
                  type="text"
                  value={formData.certification}
                  onChange={(e) => setFormData({ ...formData, certification: e.target.value })}
                  placeholder="e.g., AWS Solutions Architect"
                  className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="reminders"
                checked={formData.reminders}
                onChange={(e) => setFormData({ ...formData, reminders: e.target.checked })}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <label htmlFor="reminders" className="text-sm text-gray-700 flex items-center space-x-1">
                <Bell className="w-4 h-4" />
                <span>Enable reminders</span>
              </label>
            </div>

            <div className="flex space-x-3 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setShowNewSessionForm(false)
                  setEditingSession(null)
                  resetForm()
                }}
              >
                Cancel
              </Button>
              <Button type="submit">
                {editingSession ? 'Update Session' : 'Schedule Session'}
              </Button>
            </div>
          </form>
        </Card>
      )}
    </div>
  )
}