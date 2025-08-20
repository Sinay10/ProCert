'use client'

import { useState, useEffect, useRef } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Clock, Target, Play, Pause, RotateCcw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { mockDataStore } from '@/lib/mock-data-store'

interface StudyTimeTrackerProps {
  data?: {
    total_study_time: number
    quizzes_completed: number
    average_score: number
    streak_days: number
  }
  loading: boolean
}

export function StudyTimeTracker({ data, loading }: StudyTimeTrackerProps) {
  const [isTracking, setIsTracking] = useState(false)
  const [sessionTime, setSessionTime] = useState(0)
  const [dailyGoal] = useState(60) // 60 minutes daily goal
  const [todayStudyTime, setTodayStudyTime] = useState(25)
  const intervalRef = useRef<NodeJS.Timeout | null>(null)

  // Update today's study time when data changes
  useEffect(() => {
    if (data) {
      const today = new Date().toISOString().split('T')[0]
      const todayTrend = mockDataStore.progress.trends.find(t => t.date === today)
      setTodayStudyTime(todayTrend?.study_time || 25)
    }
  }, [data])

  // Subscribe to mock data updates
  useEffect(() => {
    const unsubscribe = mockDataStore.subscribe(() => {
      const today = new Date().toISOString().split('T')[0]
      const todayTrend = mockDataStore.progress.trends.find(t => t.date === today)
      setTodayStudyTime(todayTrend?.study_time || 25)
    })

    return unsubscribe
  }, [])

  // Timer functionality
  useEffect(() => {
    if (isTracking) {
      intervalRef.current = setInterval(() => {
        setSessionTime(prev => prev + 1)
      }, 1000)
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [isTracking])

  const handleStartStop = () => {
    if (isTracking) {
      // Stop timer and save session if there's time recorded
      if (sessionTime > 0) {
        const minutes = Math.ceil(sessionTime / 60)
        mockDataStore.addStudyTime(minutes)
      }
    }
    setIsTracking(!isTracking)
  }

  const handleReset = () => {
    setIsTracking(false)
    setSessionTime(0)
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
  }

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5" />
            Study Time Tracker
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse space-y-4">
            <div className="h-16 bg-secondary-200 rounded"></div>
            <div className="h-8 bg-secondary-200 rounded"></div>
            <div className="h-4 bg-secondary-200 rounded w-3/4"></div>
          </div>
        </CardContent>
      </Card>
    )
  }

  const formatTime = (minutes: number) => {
    const hours = Math.floor(minutes / 60)
    const mins = minutes % 60
    if (hours > 0) {
      return `${hours}h ${mins}m`
    }
    return `${mins}m`
  }

  const formatSessionTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  const dailyProgress = Math.min((todayStudyTime / dailyGoal) * 100, 100)
  const weeklyAverage = data ? Math.round(data.total_study_time / 7) : 0

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Clock className="h-5 w-5" />
          Study Time Tracker
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Current Session Timer */}
        <div className="text-center space-y-3">
          <div className="text-3xl font-mono font-bold text-primary-600">
            {formatSessionTime(sessionTime)}
          </div>
          <div className="flex justify-center gap-2">
            <Button
              onClick={handleStartStop}
              variant={isTracking ? "outline" : "primary"}
              size="sm"
              className="flex items-center gap-1"
            >
              {isTracking ? (
                <>
                  <Pause className="h-4 w-4" />
                  Pause
                </>
              ) : (
                <>
                  <Play className="h-4 w-4" />
                  Start
                </>
              )}
            </Button>
            <Button
              onClick={handleReset}
              variant="outline"
              size="sm"
              className="flex items-center gap-1"
            >
              <RotateCcw className="h-4 w-4" />
              Reset
            </Button>
          </div>
        </div>

        {/* Daily Goal Progress */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Target className="h-4 w-4 text-primary-600" />
              <span className="text-sm font-medium">Daily Goal</span>
            </div>
            <span className="text-sm text-secondary-600">
              {formatTime(todayStudyTime)} / {formatTime(dailyGoal)}
            </span>
          </div>
          
          <div className="relative">
            <div className="h-2 bg-secondary-200 rounded-full">
              <div
                className="h-2 bg-primary-600 rounded-full transition-all duration-300"
                style={{ width: `${dailyProgress}%` }}
              />
            </div>
          </div>
          
          <div className="text-center">
            <span className={`text-sm font-medium ${
              dailyProgress >= 100 ? 'text-green-600' : 'text-secondary-600'
            }`}>
              {Math.round(dailyProgress)}% Complete
            </span>
            {dailyProgress >= 100 && (
              <div className="text-xs text-green-600 mt-1">🎉 Goal achieved!</div>
            )}
          </div>
        </div>

        {/* Study Statistics */}
        <div className="space-y-3 pt-3 border-t">
          <h4 className="text-sm font-medium text-secondary-700">Study Statistics</h4>
          
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div className="text-center p-2 bg-secondary-50 rounded">
              <div className="font-semibold text-secondary-900">
                {data ? formatTime(data.total_study_time) : '0m'}
              </div>
              <div className="text-secondary-600">Total Time</div>
            </div>
            
            <div className="text-center p-2 bg-secondary-50 rounded">
              <div className="font-semibold text-secondary-900">
                {formatTime(weeklyAverage)}
              </div>
              <div className="text-secondary-600">Daily Avg</div>
            </div>
          </div>
          
          <div className="text-center p-2 bg-primary-50 rounded">
            <div className="font-semibold text-primary-900">
              {data?.streak_days || 0} days
            </div>
            <div className="text-primary-700 text-xs">Study Streak</div>
          </div>
        </div>

        {/* Study Tips */}
        <div className="bg-blue-50 p-3 rounded-lg">
          <h5 className="text-sm font-medium text-blue-900 mb-1">💡 Study Tip</h5>
          <p className="text-xs text-blue-800">
            {dailyProgress < 50 
              ? "Try studying in 25-minute focused sessions with 5-minute breaks."
              : dailyProgress < 100
              ? "You're doing great! Keep up the momentum to reach your daily goal."
              : "Excellent work! Consider reviewing challenging topics or taking practice quizzes."
            }
          </p>
        </div>
      </CardContent>
    </Card>
  )
}