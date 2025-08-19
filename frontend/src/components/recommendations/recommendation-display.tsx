'use client'

import { useState } from 'react'
import { Clock, BookOpen, Target, TrendingUp, Star, ChevronRight } from 'lucide-react'
import { StudyRecommendation } from '@/types/api'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'

interface RecommendationDisplayProps {
  recommendations: StudyRecommendation[]
  onRecommendationClick: (recommendation: StudyRecommendation) => void
  onFeedback: (recommendationId: string, feedback: 'helpful' | 'not_helpful' | 'completed') => void
  loading?: boolean
}

const getRecommendationIcon = (type: string) => {
  switch (type) {
    case 'content':
      return <BookOpen className="w-5 h-5 text-blue-600" />
    case 'quiz':
      return <Target className="w-5 h-5 text-green-600" />
    case 'review':
      return <TrendingUp className="w-5 h-5 text-orange-600" />
    default:
      return <Star className="w-5 h-5 text-purple-600" />
  }
}

const getPriorityColor = (priority: number) => {
  if (priority >= 8) return 'bg-red-100 text-red-800 border-red-200'
  if (priority >= 6) return 'bg-orange-100 text-orange-800 border-orange-200'
  if (priority >= 4) return 'bg-yellow-100 text-yellow-800 border-yellow-200'
  return 'bg-green-100 text-green-800 border-green-200'
}

const getPriorityLabel = (priority: number) => {
  if (priority >= 8) return 'High Priority'
  if (priority >= 6) return 'Medium Priority'
  if (priority >= 4) return 'Low Priority'
  return 'Optional'
}

export function RecommendationDisplay({
  recommendations,
  onRecommendationClick,
  onFeedback,
  loading = false
}: RecommendationDisplayProps) {
  const [expandedRecommendations, setExpandedRecommendations] = useState<Set<string>>(new Set())

  const toggleExpanded = (recommendationId: string) => {
    const newExpanded = new Set(expandedRecommendations)
    if (newExpanded.has(recommendationId)) {
      newExpanded.delete(recommendationId)
    } else {
      newExpanded.add(recommendationId)
    }
    setExpandedRecommendations(newExpanded)
  }

  if (loading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <Card key={i} className="p-6" data-testid="loading-skeleton">
            <div className="animate-pulse">
              <div className="flex items-center space-x-3 mb-3">
                <div className="w-5 h-5 bg-gray-200 rounded"></div>
                <div className="h-4 bg-gray-200 rounded w-1/4"></div>
                <div className="h-6 bg-gray-200 rounded w-20"></div>
              </div>
              <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
              <div className="h-3 bg-gray-200 rounded w-1/2"></div>
            </div>
          </Card>
        ))}
      </div>
    )
  }

  if (recommendations.length === 0) {
    return (
      <Card className="p-8 text-center">
        <Star className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">No Recommendations Available</h3>
        <p className="text-gray-600">
          Complete some quizzes or interact with the chatbot to get personalized study recommendations.
        </p>
      </Card>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-gray-900">Study Recommendations</h2>
        <div className="text-sm text-gray-600">
          {recommendations.length} recommendation{recommendations.length !== 1 ? 's' : ''} available
        </div>
      </div>

      {recommendations.map((recommendation) => {
        const isExpanded = expandedRecommendations.has(recommendation.recommendation_id)
        
        return (
          <Card key={recommendation.recommendation_id} className="p-6 hover:shadow-md transition-shadow">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center space-x-3 mb-3">
                  {getRecommendationIcon(recommendation.type)}
                  <span className="font-medium text-gray-900 capitalize">
                    {recommendation.type} Recommendation
                  </span>
                  <span className={`px-2 py-1 text-xs font-medium rounded-full border ${getPriorityColor(recommendation.priority)}`}>
                    {getPriorityLabel(recommendation.priority)}
                  </span>
                </div>

                <div className="mb-3">
                  <p className="text-gray-700 leading-relaxed">
                    {recommendation.reasoning}
                  </p>
                </div>

                <div className="flex items-center space-x-4 text-sm text-gray-600 mb-4">
                  <div className="flex items-center space-x-1">
                    <Clock className="w-4 h-4" />
                    <span>{recommendation.estimated_time} min</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <Target className="w-4 h-4" />
                    <span>Priority: {recommendation.priority}/10</span>
                  </div>
                </div>

                {isExpanded && (
                  <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                    <h4 className="font-medium text-gray-900 mb-2">Why this recommendation?</h4>
                    <p className="text-sm text-gray-700 mb-3">
                      This recommendation is based on your recent performance patterns and learning goals. 
                      It's designed to help you improve in areas where you need the most support.
                    </p>
                    {recommendation.content_id && (
                      <div className="text-sm text-gray-600">
                        <strong>Content ID:</strong> {recommendation.content_id}
                      </div>
                    )}
                  </div>
                )}
              </div>

              <div className="flex flex-col space-y-2 ml-4">
                <Button
                  onClick={() => toggleExpanded(recommendation.recommendation_id)}
                  variant="outline"
                  size="sm"
                  className="text-xs"
                >
                  {isExpanded ? 'Less Info' : 'More Info'}
                </Button>
                <Button
                  onClick={() => onRecommendationClick(recommendation)}
                  size="sm"
                  className="text-xs"
                >
                  Start <ChevronRight className="w-3 h-3 ml-1" />
                </Button>
              </div>
            </div>

            <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-200">
              <div className="text-xs text-gray-500">
                Created {new Date(recommendation.created_at).toLocaleDateString()}
              </div>
              <div className="flex space-x-2">
                <Button
                  onClick={() => onFeedback(recommendation.recommendation_id, 'helpful')}
                  variant="outline"
                  size="sm"
                  className="text-xs"
                >
                  👍 Helpful
                </Button>
                <Button
                  onClick={() => onFeedback(recommendation.recommendation_id, 'not_helpful')}
                  variant="outline"
                  size="sm"
                  className="text-xs"
                >
                  👎 Not Helpful
                </Button>
                <Button
                  onClick={() => onFeedback(recommendation.recommendation_id, 'completed')}
                  variant="outline"
                  size="sm"
                  className="text-xs"
                >
                  ✅ Completed
                </Button>
              </div>
            </div>
          </Card>
        )
      })}
    </div>
  )
}