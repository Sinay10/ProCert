'use client'

import { useState } from 'react'
import { CheckCircle, Circle, Lock, Clock, BookOpen, Target, TrendingUp } from 'lucide-react'
import { StudyPath } from '@/types/api'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

interface StudyPathVisualizationProps {
  studyPath: StudyPath
  onTopicClick: (topicIndex: number) => void
  onStartPath?: () => void
  loading?: boolean
}

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'completed':
      return <CheckCircle className="w-6 h-6 text-green-600" />
    case 'current':
      return <Circle className="w-6 h-6 text-blue-600 fill-current" />
    case 'locked':
      return <Lock className="w-6 h-6 text-gray-400" />
    default:
      return <Circle className="w-6 h-6 text-gray-400" />
  }
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'completed':
      return 'bg-green-50 border-green-200'
    case 'current':
      return 'bg-blue-50 border-blue-200'
    case 'locked':
      return 'bg-gray-50 border-gray-200'
    default:
      return 'bg-gray-50 border-gray-200'
  }
}

export function StudyPathVisualization({
  studyPath,
  onTopicClick,
  onStartPath,
  loading = false
}: StudyPathVisualizationProps) {
  const [selectedTopic, setSelectedTopic] = useState<number | null>(null)

  if (loading || !studyPath) {
    return (
      <div className="space-y-6">
        <Card className="p-6" data-testid="loading-skeleton">
          <div className="animate-pulse">
            <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
            <div className="space-y-3">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="flex items-center space-x-3">
                  <div className="w-6 h-6 bg-gray-200 rounded-full"></div>
                  <div className="h-4 bg-gray-200 rounded w-1/2"></div>
                </div>
              ))}
            </div>
          </div>
        </Card>
      </div>
    )
  }

  const progressPercentage = studyPath.progress 
    ? (studyPath.progress.completed_topics / studyPath.progress.total_topics) * 100 
    : 0

  return (
    <div className="space-y-6">
      {/* Progress Overview */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">Your Study Path</h2>
          <div className="text-sm text-gray-600">
            {studyPath.progress?.completed_topics || 0} of {studyPath.progress?.total_topics || 0} topics completed
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">Overall Progress</span>
            <span className="text-sm text-gray-600">{Math.round(progressPercentage)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div
              className="bg-blue-600 h-3 rounded-full transition-all duration-300"
              style={{ width: `${progressPercentage}%` }}
            ></div>
          </div>
        </div>

        {/* Estimated Completion */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4 text-sm text-gray-600">
            <div className="flex items-center space-x-1">
              <Clock className="w-4 h-4" />
              <span>Est. completion: {studyPath.progress?.estimated_completion || 'TBD'}</span>
            </div>
            <div className="flex items-center space-x-1">
              <Target className="w-4 h-4" />
              <span>{studyPath.progress?.total_topics || 0} total topics</span>
            </div>
          </div>
          
          {onStartPath && progressPercentage === 0 && (
            <Button onClick={onStartPath} className="ml-4">
              Start This Study Path
            </Button>
          )}
        </div>
      </Card>

      {/* Study Path Topics */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Learning Path</h3>
        
        <div className="space-y-4">
          {studyPath.path?.map((topic, index) => {
            const isSelected = selectedTopic === index
            const canAccess = topic.status !== 'locked'
            
            return (
              <div key={index} className="relative">
                {/* Connection Line */}
                {index < (studyPath.path?.length || 0) - 1 && (
                  <div className="absolute left-3 top-8 w-0.5 h-8 bg-gray-300"></div>
                )}
                
                <div
                  className={`flex items-start space-x-4 p-4 rounded-lg border-2 transition-all cursor-pointer ${
                    getStatusColor(topic.status)
                  } ${isSelected ? 'ring-2 ring-blue-500' : ''} ${
                    canAccess ? 'hover:shadow-md' : 'cursor-not-allowed opacity-60'
                  }`}
                  onClick={() => {
                    if (canAccess) {
                      setSelectedTopic(isSelected ? null : index)
                      onTopicClick(index)
                    }
                  }}
                >
                  <div className="flex-shrink-0 mt-1">
                    {getStatusIcon(topic.status)}
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="text-base font-medium text-gray-900 truncate">
                        {topic.topic}
                      </h4>
                      <div className="flex items-center space-x-2 text-sm text-gray-600">
                        <Clock className="w-4 h-4" />
                        <span>{topic.estimated_time} min</span>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-4 text-sm text-gray-600">
                      <div className="flex items-center space-x-1">
                        <BookOpen className="w-4 h-4" />
                        <span>{topic.content_ids.length} resources</span>
                      </div>
                      <div className="capitalize">
                        Status: {topic.status.replace('_', ' ')}
                      </div>
                    </div>

                    {isSelected && (
                      <div className="mt-4 p-3 bg-white rounded border">
                        <h5 className="font-medium text-gray-900 mb-2">Available Resources</h5>
                        <div className="space-y-2">
                          {topic.content_ids.map((contentId, contentIndex) => (
                            <div key={contentIndex} className="flex items-center space-x-2 text-sm">
                              <BookOpen className="w-3 h-3 text-gray-500" />
                              <span className="text-gray-700">Content ID: {contentId}</span>
                            </div>
                          ))}
                        </div>
                        {topic.status === 'current' && (
                          <Button size="sm" className="mt-3">
                            Continue Learning
                          </Button>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </Card>

      {/* Next Steps */}
      {studyPath.next_steps && studyPath.next_steps.length > 0 && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Recommended Next Steps</h3>
          <div className="space-y-3">
            {studyPath.next_steps.map((step, index) => (
              <div key={index} className="flex items-start space-x-3 p-3 bg-blue-50 rounded-lg">
                <TrendingUp className="w-5 h-5 text-blue-600 mt-0.5" />
                <div>
                  <p className="text-sm text-gray-800">{step}</p>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  )
}