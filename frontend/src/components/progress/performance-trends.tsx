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

  // Filter data based on timeframe
  const getFilteredData = () => {
    if (!data || data.length === 0) return []
    
    const now = new Date()
    const filtered = data.filter(item => {
      const itemDate = new Date(item.date)
      const diffInDays = Math.floor((now.getTime() - itemDate.getTime()) / (1000 * 60 * 60 * 24))
      
      // Don't show future dates
      if (diffInDays < 0) return false
      
      switch (timeframe) {
        case 'week':
          return diffInDays <= 7
        case 'month':
          return diffInDays <= 30
        case 'quarter':
          return diffInDays <= 90
        case 'year':
          return diffInDays <= 365
        default:
          return true
      }
    })
    
    return filtered.sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
  }

  const filteredData = getFilteredData()

  // Calculate trend direction
  const calculateTrend = () => {
    if (filteredData.length < 2) return 'neutral'
    
    const recent = filteredData.slice(-3) // Last 3 data points
    const older = filteredData.slice(0, -3) // Earlier data points
    
    if (recent.length === 0 || older.length === 0) return 'neutral'
    
    const recentAvg = recent.reduce((sum, item) => sum + item.score, 0) / recent.length
    const olderAvg = older.reduce((sum, item) => sum + item.score, 0) / older.length
    
    const difference = recentAvg - olderAvg
    
    if (difference > 3) return 'up'
    if (difference < -3) return 'down'
    return 'neutral'
  }

  const trend = calculateTrend()
  const maxScore = Math.max(...filteredData.map(d => d.score), 100)
  const maxStudyTime = Math.max(...filteredData.map(d => d.study_time), 1)

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
                {filteredData.length > 1 && (
                  <polyline
                    fill="none"
                    stroke="#3b82f6"
                    strokeWidth="2"
                    points={filteredData
                      .map((item, index) => {
                        const x = (index / Math.max(filteredData.length - 1, 1)) * 380 + 20
                        const y = 120 - (item.score / 100) * 120
                        return `${x},${y}`
                      })
                      .join(' ')}
                  />
                )}
                
                {/* Score points */}
                {filteredData.map((item, index) => {
                  const x = (index / Math.max(filteredData.length - 1, 1)) * 380 + 20
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
            <div className="relative h-32">
              <svg className="w-full h-full" viewBox="0 0 400 120">
                {/* Grid lines for study time */}
                {[0, 30, 60, 90, 120].map((value) => (
                  <g key={value}>
                    <line
                      x1="0"
                      y1={120 - (value / Math.max(maxStudyTime, 120)) * 120}
                      x2="400"
                      y2={120 - (value / Math.max(maxStudyTime, 120)) * 120}
                      stroke="#f1f5f9"
                      strokeWidth="1"
                    />
                    <text
                      x="5"
                      y={120 - (value / Math.max(maxStudyTime, 120)) * 120 - 5}
                      className="text-xs fill-secondary-500"
                    >
                      {value}m
                    </text>
                  </g>
                ))}
                
                {/* Study time bars */}
                {filteredData.map((item, index) => {
                  const barWidth = 320 / Math.max(filteredData.length, 1)
                  const x = (index * barWidth) + 40 + (barWidth * 0.1) // Add padding
                  const barHeight = (item.study_time / Math.max(maxStudyTime, 120)) * 120
                  const y = 120 - barHeight
                  
                  return (
                    <g key={index}>
                      <rect
                        x={x}
                        y={y}
                        width={barWidth * 0.8}
                        height={barHeight}
                        fill="#10b981"
                        className="hover:fill-green-600 transition-colors cursor-pointer"
                        rx="2"
                      >
                        <title>{`${formatDate(item.date)}: ${item.study_time} minutes`}</title>
                      </rect>
                      
                      {/* Date labels */}
                      <text
                        x={x + (barWidth * 0.4)}
                        y={135}
                        className="text-xs fill-secondary-500 text-anchor-middle"
                        textAnchor="middle"
                      >
                        {formatDate(item.date)}
                      </text>
                      
                      {/* Value labels on top of bars */}
                      {item.study_time >= 0 && (
                        <text
                          x={x + (barWidth * 0.4)}
                          y={Math.max(y - 5, 10)} // Ensure label doesn't go above chart
                          className="text-xs fill-secondary-700 text-anchor-middle font-medium"
                          textAnchor="middle"
                        >
                          {item.study_time}m
                        </text>
                      )}
                    </g>
                  )
                })}
              </svg>
            </div>
          </div>

          {/* Summary Stats */}
          <div className="grid grid-cols-2 gap-4 pt-4 border-t">
            <div className="text-center">
              <div className="text-lg font-semibold text-secondary-900">
                {filteredData.length > 0 ? Math.round(filteredData.reduce((sum, item) => sum + item.score, 0) / filteredData.length) : 0}%
              </div>
              <div className="text-sm text-secondary-600">Average Score</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-semibold text-secondary-900">
                {filteredData.length > 0 ? Math.round(filteredData.reduce((sum, item) => sum + item.study_time, 0) / filteredData.length) : 0}m
              </div>
              <div className="text-sm text-secondary-600">Avg Study Time</div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}