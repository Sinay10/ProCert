'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Brain, TrendingUp, AlertCircle, CheckCircle, Clock, Target } from 'lucide-react'
import { UserAnalytics } from '@/types/api'

interface AnalyticsInsightsProps {
  data?: UserAnalytics
  loading: boolean
}

export function AnalyticsInsights({ data, loading }: AnalyticsInsightsProps) {
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="h-5 w-5" />
            Analytics Insights
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse space-y-4">
            <div className="h-16 bg-secondary-200 rounded"></div>
            <div className="h-12 bg-secondary-200 rounded"></div>
            <div className="h-20 bg-secondary-200 rounded"></div>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!data) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="h-5 w-5" />
            Analytics Insights
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <Brain className="h-12 w-12 text-secondary-300 mx-auto mb-3" />
            <p className="text-secondary-600">No analytics data yet</p>
            <p className="text-sm text-secondary-500 mt-1">
              Complete more activities to see insights
            </p>
          </div>
        </CardContent>
      </Card>
    )
  }

  const getReadinessColor = (percentage: number) => {
    if (percentage >= 80) return 'text-green-600 bg-green-50'
    if (percentage >= 60) return 'text-yellow-600 bg-yellow-50'
    return 'text-red-600 bg-red-50'
  }

  const getReadinessIcon = (percentage: number) => {
    if (percentage >= 80) return CheckCircle
    if (percentage >= 60) return Clock
    return AlertCircle
  }

  const formatEstimatedTime = (hours: number) => {
    if (hours < 1) return `${Math.round(hours * 60)}m`
    if (hours < 24) return `${Math.round(hours)}h`
    const days = Math.round(hours / 24)
    return `${days}d`
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Brain className="h-5 w-5" />
          Analytics Insights
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Performance Overview */}
        <div>
          <h4 className="text-sm font-medium text-secondary-700 mb-3">Performance Analysis</h4>
          
          {/* Strengths */}
          {data.performance.strengths.length > 0 && (
            <div className="mb-3">
              <div className="flex items-center gap-2 mb-2">
                <CheckCircle className="h-4 w-4 text-green-600" />
                <span className="text-sm font-medium text-green-700">Strengths</span>
              </div>
              <div className="flex flex-wrap gap-1">
                {data.performance.strengths.slice(0, 3).map((strength, index) => (
                  <span
                    key={index}
                    className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full"
                  >
                    {strength}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Weaknesses */}
          {data.performance.weaknesses.length > 0 && (
            <div className="mb-3">
              <div className="flex items-center gap-2 mb-2">
                <AlertCircle className="h-4 w-4 text-red-600" />
                <span className="text-sm font-medium text-red-700">Areas to Improve</span>
              </div>
              <div className="flex flex-wrap gap-1">
                {data.performance.weaknesses.slice(0, 3).map((weakness, index) => (
                  <span
                    key={index}
                    className="px-2 py-1 bg-red-100 text-red-700 text-xs rounded-full"
                  >
                    {weakness}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Improvement Rate */}
          <div className="flex items-center justify-between p-2 bg-blue-50 rounded">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-blue-600" />
              <span className="text-sm font-medium text-blue-700">Improvement Rate</span>
            </div>
            <span className="text-sm font-bold text-blue-900">
              {Math.round(data.performance.improvement_rate * 100)}%
            </span>
          </div>
        </div>

        {/* Certification Readiness */}
        <div>
          <h4 className="text-sm font-medium text-secondary-700 mb-3">Certification Readiness</h4>
          <div className="space-y-2">
            {Object.entries(data.predictions.certification_readiness).map(([cert, readiness]) => {
              const percentage = Math.round(readiness * 100)
              const ReadinessIcon = getReadinessIcon(percentage)
              
              return (
                <div key={cert} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <ReadinessIcon className="h-4 w-4" />
                    <span className="text-sm text-secondary-900">
                      {cert.toUpperCase()}
                    </span>
                  </div>
                  <div className={`px-2 py-1 rounded text-xs font-medium ${getReadinessColor(percentage)}`}>
                    {percentage}%
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Study Time Estimates */}
        <div>
          <h4 className="text-sm font-medium text-secondary-700 mb-3">Estimated Study Time</h4>
          <div className="space-y-2">
            {Object.entries(data.predictions.estimated_study_time).map(([cert, hours]) => (
              <div key={cert} className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Target className="h-4 w-4 text-secondary-600" />
                  <span className="text-sm text-secondary-900">
                    {cert.toUpperCase()}
                  </span>
                </div>
                <span className="text-sm font-medium text-secondary-700">
                  {formatEstimatedTime(hours)}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* AI Recommendations */}
        <div>
          <h4 className="text-sm font-medium text-secondary-700 mb-3">AI Recommendations</h4>
          <div className="space-y-2">
            {data.recommendations.slice(0, 3).map((recommendation, index) => (
              <div
                key={index}
                className="p-3 bg-gradient-to-r from-primary-50 to-blue-50 rounded-lg border-l-2 border-primary-500"
              >
                <p className="text-sm text-secondary-800">{recommendation}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Quick Stats */}
        <div className="pt-3 border-t">
          <div className="grid grid-cols-2 gap-3 text-center">
            <div className="p-2 bg-secondary-50 rounded">
              <div className="text-lg font-bold text-secondary-900">
                {data.performance.strengths.length}
              </div>
              <div className="text-xs text-secondary-700">Strong Areas</div>
            </div>
            <div className="p-2 bg-secondary-50 rounded">
              <div className="text-lg font-bold text-secondary-900">
                {Object.keys(data.predictions.certification_readiness).length}
              </div>
              <div className="text-xs text-secondary-700">Certifications</div>
            </div>
          </div>
        </div>

        {/* Motivational Message */}
        <div className="bg-gradient-to-r from-primary-500 to-blue-600 text-white p-3 rounded-lg text-center">
          <p className="text-sm font-medium">
            {data.performance.improvement_rate > 0.1 
              ? "🚀 You're making excellent progress! Keep it up!"
              : data.performance.improvement_rate > 0.05
              ? "📈 Steady progress! Consider increasing study frequency."
              : "💪 Every expert was once a beginner. Stay consistent!"
            }
          </p>
        </div>
      </CardContent>
    </Card>
  )
}