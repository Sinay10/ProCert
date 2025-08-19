'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Clock, Target, TrendingUp, Zap } from 'lucide-react'

interface ProgressOverviewProps {
  data?: {
    total_study_time: number
    quizzes_completed: number
    average_score: number
    streak_days: number
  }
  loading: boolean
}

export function ProgressOverview({ data, loading }: ProgressOverviewProps) {
  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Card key={i}>
            <CardContent className="p-6">
              <div className="animate-pulse">
                <div className="h-4 bg-secondary-200 rounded w-3/4 mb-2"></div>
                <div className="h-8 bg-secondary-200 rounded w-1/2"></div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  const formatStudyTime = (minutes: number) => {
    const hours = Math.floor(minutes / 60)
    const mins = minutes % 60
    if (hours > 0) {
      return `${hours}h ${mins}m`
    }
    return `${mins}m`
  }

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600'
    if (score >= 60) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getStreakColor = (days: number) => {
    if (days >= 7) return 'text-purple-600'
    if (days >= 3) return 'text-blue-600'
    return 'text-secondary-600'
  }

  const stats = [
    {
      title: 'Study Time',
      value: data ? formatStudyTime(data.total_study_time) : '0m',
      icon: Clock,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
    },
    {
      title: 'Quizzes Completed',
      value: data?.quizzes_completed?.toString() || '0',
      icon: Target,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
    },
    {
      title: 'Average Score',
      value: data ? `${Math.round(data.average_score)}%` : '0%',
      icon: TrendingUp,
      color: data ? getScoreColor(data.average_score) : 'text-secondary-600',
      bgColor: 'bg-yellow-50',
    },
    {
      title: 'Study Streak',
      value: data ? `${data.streak_days} days` : '0 days',
      icon: Zap,
      color: data ? getStreakColor(data.streak_days) : 'text-secondary-600',
      bgColor: 'bg-purple-50',
    },
  ]

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {stats.map((stat) => {
        const Icon = stat.icon
        return (
          <Card key={stat.title}>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-secondary-600 mb-1">
                    {stat.title}
                  </p>
                  <p className={`text-2xl font-bold ${stat.color}`}>
                    {stat.value}
                  </p>
                </div>
                <div className={`p-3 rounded-full ${stat.bgColor}`}>
                  <Icon className={`h-6 w-6 ${stat.color}`} />
                </div>
              </div>
            </CardContent>
          </Card>
        )
      })}
    </div>
  )
}