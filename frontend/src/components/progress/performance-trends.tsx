'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

interface PerformanceTrendsProps {
  data?: Array<{
    date: string
    score: number
    study_time: number
  }>
  loading: boolean
  timeframe: 'week' | 'month' | 'quarter' | 'year'
}

export function PerformanceTrends({ data, loading, timeframe }: PerformanceTrendsProps) {
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Performance Trends</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse">
            <div className="h-64 bg-secondary-200 rounded"></div>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!data || data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Performance Trends</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-16">
            <TrendingUp className="h-12 w-12 text-secondary-300 mx-auto mb-3" />
            <p className="text-secondary-600">No performance data yet</p>
            <p className="text-sm text-secondary-500 mt-1">
              Complete some quizzes to see your trends
            </p>
          </div>
        </CardContent>
      </Card>
    )
  }

  // Calculate trend direction
  const calculateTrend = () => {
    if (data.length < 2) return 'neutral'
    
    const recent = data.slice(-5) // Last 5 data points
    const older = data.slice(-10, -5) // Previous 5 data points
    
    if (recent.length === 0 || older.length === 0) return 'neutral'
    
    const recentAvg = recent.reduce((sum, item) => sum + item.score, 0) / recent.length
    const olderAvg = older.reduce((sum, item) => sum + item.score, 0) / older.length
    
    const difference = recentAvg - olderAvg
    
    if (difference > 5) return 'up'
    if (difference < -5) return 'down'
    return 'neutral'
  }

  const trend = calculateTrend()
  const maxScore = Math.max(...data.map(d => d.score), 100)
  const maxStudyTime = Math.max(...data.map(d => d.study_time))

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    switch (timeframe) {
      case 'week':
        return date.toLocaleDateString('en-US', { weekday: 'short' })
      case 'month':
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
      case 'quarter':
      case 'year':
        return date.toLocaleDateString('en-US', { month: 'short' })
      default:
        return date.toLocaleDateString()
    }
  }

  const getTrendIcon = () => {
    switch (trend) {
      case 'up':
        return <TrendingUp className="h-4 w-4 text-green-600" />
      case 'down':
        return <TrendingDown className="h-4 w-4 text-red-600" />
      default:
        return <Minus className="h-4 w-4 text-secondary-600" />
    }
  }

  const getTrendText = () => {
    switch (trend) {
      case 'up':
        return 'Improving performance'
      case 'down':
        return 'Declining performance'
      default:
        return 'Stable performance'
    }
  }

  const getTrendColor = () => {
    switch (trend) {
      case 'up':
        return 'text-green-600'
      case 'down':
        return 'text-red-600'
      default:
        return 'text-secondary-600'
    }
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Performance Trends</CardTitle>
          <div className={`flex items-center gap-1 text-sm ${getTrendColor()}`}>
            {getTrendIcon()}
            {getTrendText()}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {/* Score Trend Chart */}
          <div>
            <h4 className="text-sm font-medium text-secondary-700 mb-3">Quiz Scores</h4>
            <div className="relative h-32">
              <svg className="w-full h-full" viewBox="0 0 400 120">
                {/* Grid lines */}
                {[0, 25, 50, 75, 100].map((value) => (
                  <g key={value}>
                    <line
                      x1="0"
                      y1={120 - (value / 100) * 120}
                      x2="400"
                      y2={120 - (value / 100) * 120}
                      stroke="#f1f5f9"
                      strokeWidth="1"
                    />
                    <text
                      x="5"
                      y={120 - (value / 100) * 120 - 5}
                      className="text-xs fill-secondary-500"
                    >
                      {value}%
                    </text>
                  </g>
                ))}
                
                {/* Score line */}
                <polyline
                  fill="none"
                  stroke="#3b82f6"
                  strokeWidth="2"
                  points={data
                    .map((item, index) => {
                      const x = (index / (data.length - 1)) * 380 + 20
                      const y = 120 - (item.score / 100) * 120
                      return `${x},${y}`
                    })
                    .join(' ')}
                />
                
                {/* Score points */}
                {data.map((item, index) => {
                  const x = (index / (data.length - 1)) * 380 + 20
                  const y = 120 - (item.score / 100) * 120
                  return (
                    <circle
                      key={index}
                      cx={x}
                      cy={y}
                      r="3"
                      fill="#3b82f6"
                      className="hover:r-4 transition-all cursor-pointer"
                    >
                      <title>{`${formatDate(item.date)}: ${item.score}%`}</title>
                    </circle>
                  )
                })}
              </svg>
            </div>
          </div>

          {/* Study Time Chart */}
          <div>
            <h4 className="text-sm font-medium text-secondary-700 mb-3">Study Time (minutes)</h4>
            <div className="relative h-24">
              <div className="flex items-end justify-between h-full">
                {data.map((item, index) => {
                  const height = maxStudyTime > 0 ? (item.study_time / maxStudyTime) * 100 : 0
                  return (
                    <div
                      key={index}
                      className="flex flex-col items-center group cursor-pointer"
                      style={{ width: `${100 / data.length}%` }}
                    >
                      <div
                        className="bg-green-500 rounded-t transition-all group-hover:bg-green-600"
                        style={{ 
                          height: `${height}%`,
                          minHeight: item.study_time > 0 ? '2px' : '0',
                          width: '80%'
                        }}
                        title={`${formatDate(item.date)}: ${item.study_time} minutes`}
                      />
                      <span className="text-xs text-secondary-500 mt-1 transform -rotate-45 origin-left">
                        {formatDate(item.date)}
                      </span>
                    </div>
                  )
                })}
              </div>
            </div>
          </div>

          {/* Summary Stats */}
          <div className="grid grid-cols-2 gap-4 pt-4 border-t">
            <div className="text-center">
              <div className="text-lg font-semibold text-secondary-900">
                {Math.round(data.reduce((sum, item) => sum + item.score, 0) / data.length)}%
              </div>
              <div className="text-sm text-secondary-600">Average Score</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-semibold text-secondary-900">
                {Math.round(data.reduce((sum, item) => sum + item.study_time, 0) / data.length)}m
              </div>
              <div className="text-sm text-secondary-600">Avg Study Time</div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}