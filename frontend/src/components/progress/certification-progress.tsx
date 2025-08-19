'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Award, Calendar } from 'lucide-react'

interface CertificationProgressProps {
  data?: Record<string, {
    progress_percentage: number
    topics_completed: number
    total_topics: number
    last_activity: string
  }>
  loading: boolean
}

export function CertificationProgress({ data, loading }: CertificationProgressProps) {
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Award className="h-5 w-5" />
            Certification Progress
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="animate-pulse">
                <div className="h-4 bg-secondary-200 rounded w-1/3 mb-2"></div>
                <div className="h-2 bg-secondary-200 rounded w-full mb-1"></div>
                <div className="h-3 bg-secondary-200 rounded w-1/4"></div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!data || Object.keys(data).length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Award className="h-5 w-5" />
            Certification Progress
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <Award className="h-12 w-12 text-secondary-300 mx-auto mb-3" />
            <p className="text-secondary-600">No certification progress yet</p>
            <p className="text-sm text-secondary-500 mt-1">
              Start taking quizzes to track your progress
            </p>
          </div>
        </CardContent>
      </Card>
    )
  }

  const formatLastActivity = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60))
    
    if (diffInHours < 1) return 'Just now'
    if (diffInHours < 24) return `${diffInHours}h ago`
    
    const diffInDays = Math.floor(diffInHours / 24)
    if (diffInDays < 7) return `${diffInDays}d ago`
    
    return date.toLocaleDateString()
  }

  const getProgressColor = (percentage: number) => {
    if (percentage >= 80) return 'bg-green-500'
    if (percentage >= 60) return 'bg-blue-500'
    if (percentage >= 40) return 'bg-yellow-500'
    return 'bg-red-500'
  }

  const getProgressBgColor = (percentage: number) => {
    if (percentage >= 80) return 'bg-green-100'
    if (percentage >= 60) return 'bg-blue-100'
    if (percentage >= 40) return 'bg-yellow-100'
    return 'bg-red-100'
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Award className="h-5 w-5" />
          Certification Progress
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {Object.entries(data).map(([certification, progress]) => (
            <div key={certification} className="space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-medium text-secondary-900">
                    {certification.replace(/-/g, ' ').toUpperCase()}
                  </h4>
                  <p className="text-sm text-secondary-600">
                    {progress.topics_completed} of {progress.total_topics} topics completed
                  </p>
                </div>
                <div className="text-right">
                  <div className="text-lg font-semibold text-secondary-900">
                    {Math.round(progress.progress_percentage)}%
                  </div>
                  <div className="flex items-center gap-1 text-xs text-secondary-500">
                    <Calendar className="h-3 w-3" />
                    {formatLastActivity(progress.last_activity)}
                  </div>
                </div>
              </div>
              
              {/* Progress Bar */}
              <div className="relative">
                <div className={`h-2 rounded-full ${getProgressBgColor(progress.progress_percentage)}`}>
                  <div
                    className={`h-2 rounded-full transition-all duration-300 ${getProgressColor(progress.progress_percentage)}`}
                    style={{ width: `${Math.min(progress.progress_percentage, 100)}%` }}
                  />
                </div>
              </div>
              
              {/* Milestone Indicators */}
              <div className="flex justify-between text-xs text-secondary-500">
                <span className={progress.progress_percentage >= 25 ? 'text-secondary-700 font-medium' : ''}>
                  25%
                </span>
                <span className={progress.progress_percentage >= 50 ? 'text-secondary-700 font-medium' : ''}>
                  50%
                </span>
                <span className={progress.progress_percentage >= 75 ? 'text-secondary-700 font-medium' : ''}>
                  75%
                </span>
                <span className={progress.progress_percentage >= 100 ? 'text-green-600 font-medium' : ''}>
                  Complete
                </span>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}