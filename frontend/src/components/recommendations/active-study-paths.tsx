'use client'

import { useState, useEffect } from 'react'
import { Play, Pause, CheckCircle, Clock, BookOpen, Target, TrendingUp, Calendar } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'

interface ActiveStudyPath {
  id: string
  title: string
  certification: string
  startedAt: string
  lastAccessedAt: string
  totalTopics: number
  completedTopics: number
  currentTopic: string
  estimatedTimeRemaining: number // in minutes
  status: 'active' | 'paused' | 'completed'
  progressPercentage: number
  topics: Array<{
    id: string
    title: string
    status: 'completed' | 'current' | 'locked'
    completedAt?: string
    timeSpent?: number
  }>
}

interface ActiveStudyPathsProps {
  onContinuePath: (pathId: string) => void
  onPausePath: (pathId: string) => void
  onCompletePath: (pathId: string) => void
  activePaths?: ActiveStudyPath[]
  loading?: boolean
}

const mockActivePaths: ActiveStudyPath[] = [
  {
    id: 'path-1',
    title: 'AWS Solutions Architect Associate Study Path',
    certification: 'SAA',
    startedAt: '2024-01-15T10:00:00Z',
    lastAccessedAt: '2024-01-18T14:30:00Z',
    totalTopics: 8,
    completedTopics: 3,
    currentTopic: 'VPC Networking Fundamentals',
    estimatedTimeRemaining: 180,
    status: 'active',
    progressPercentage: 37.5,
    topics: [
      { id: 'topic-1', title: 'EC2 Fundamentals', status: 'completed', completedAt: '2024-01-15T12:00:00Z', timeSpent: 45 },
      { id: 'topic-2', title: 'S3 Storage Basics', status: 'completed', completedAt: '2024-01-16T11:00:00Z', timeSpent: 60 },
      { id: 'topic-3', title: 'IAM Security', status: 'completed', completedAt: '2024-01-17T15:00:00Z', timeSpent: 50 },
      { id: 'topic-4', title: 'VPC Networking Fundamentals', status: 'current' },
      { id: 'topic-5', title: 'Lambda Functions', status: 'locked' },
      { id: 'topic-6', title: 'RDS Databases', status: 'locked' },
      { id: 'topic-7', title: 'CloudFormation', status: 'locked' },
      { id: 'topic-8', title: 'Final Review', status: 'locked' }
    ]
  },
  {
    id: 'path-2',
    title: 'VPC Networking Deep Dive',
    certification: 'SAA',
    startedAt: '2024-01-10T09:00:00Z',
    lastAccessedAt: '2024-01-12T16:00:00Z',
    totalTopics: 5,
    completedTopics: 5,
    currentTopic: 'Completed',
    estimatedTimeRemaining: 0,
    status: 'completed',
    progressPercentage: 100,
    topics: [
      { id: 'topic-1', title: 'VPC Basics', status: 'completed', completedAt: '2024-01-10T10:00:00Z', timeSpent: 30 },
      { id: 'topic-2', title: 'Subnets & Routing', status: 'completed', completedAt: '2024-01-11T11:00:00Z', timeSpent: 45 },
      { id: 'topic-3', title: 'Security Groups', status: 'completed', completedAt: '2024-01-11T14:00:00Z', timeSpent: 35 },
      { id: 'topic-4', title: 'NAT & Internet Gateways', status: 'completed', completedAt: '2024-01-12T10:00:00Z', timeSpent: 40 },
      { id: 'topic-5', title: 'VPC Peering', status: 'completed', completedAt: '2024-01-12T16:00:00Z', timeSpent: 25 }
    ]
  }
]

export function ActiveStudyPaths({
  onContinuePath,
  onPausePath,
  onCompletePath,
  activePaths = mockActivePaths,
  loading = false
}: ActiveStudyPathsProps) {
  const [expandedPath, setExpandedPath] = useState<string | null>(null)

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60))
    
    if (diffInHours < 1) return 'Just now'
    if (diffInHours < 24) return `${diffInHours}h ago`
    const diffInDays = Math.floor(diffInHours / 24)
    if (diffInDays < 7) return `${diffInDays}d ago`
    return date.toLocaleDateString()
  }

  const formatEstimatedTime = (minutes: number) => {
    if (minutes === 0) return 'Completed'
    if (minutes < 60) return `${minutes}m remaining`
    const hours = Math.floor(minutes / 60)
    const remainingMinutes = minutes % 60
    return `${hours}h ${remainingMinutes}m remaining`
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-blue-100 text-blue-800 border-blue-200'
      case 'paused':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200'
      case 'completed':
        return 'bg-green-100 text-green-800 border-green-200'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <Play className="w-4 h-4" />
      case 'paused':
        return <Pause className="w-4 h-4" />
      case 'completed':
        return <CheckCircle className="w-4 h-4" />
      default:
        return <Clock className="w-4 h-4" />
    }
  }

  if (loading) {
    return (
      <div className="space-y-4">
        {[1, 2].map((i) => (
          <Card key={i} className="p-6">
            <div className="animate-pulse">
              <div className="flex items-center justify-between mb-4">
                <div className="h-5 bg-gray-200 rounded w-1/3"></div>
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

  if (activePaths.length === 0) {
    return (
      <Card className="p-8 text-center">
        <BookOpen className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">No Active Study Paths</h3>
        <p className="text-gray-600">
          Start a study path from the recommendations below to begin tracking your progress.
        </p>
      </Card>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-900">Active Study Paths</h2>
        <div className="text-sm text-gray-600">
          {activePaths.filter(p => p.status === 'active').length} active, {activePaths.filter(p => p.status === 'completed').length} completed
        </div>
      </div>

      {activePaths.map((path) => {
        const isExpanded = expandedPath === path.id
        
        return (
          <Card key={path.id} className="p-6 hover:shadow-md transition-shadow">
            <div className="flex items-start justify-between mb-4">
              <div className="flex-1">
                <div className="flex items-center space-x-3 mb-2">
                  <h3 className="text-lg font-semibold text-gray-900">{path.title}</h3>
                  <span className={`px-2 py-1 text-xs font-medium rounded-full border ${getStatusColor(path.status)}`}>
                    <div className="flex items-center space-x-1">
                      {getStatusIcon(path.status)}
                      <span className="capitalize">{path.status}</span>
                    </div>
                  </span>
                </div>
                
                <div className="flex items-center space-x-4 text-sm text-gray-600 mb-3">
                  <div className="flex items-center space-x-1">
                    <Target className="w-4 h-4" />
                    <span>{path.certification}</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <Calendar className="w-4 h-4" />
                    <span>Started {formatTimeAgo(path.startedAt)}</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <Clock className="w-4 h-4" />
                    <span>Last accessed {formatTimeAgo(path.lastAccessedAt)}</span>
                  </div>
                </div>

                {path.status !== 'completed' && (
                  <div className="mb-3">
                    <div className="text-sm font-medium text-gray-700 mb-1">
                      Current: {path.currentTopic}
                    </div>
                    <div className="text-sm text-gray-600">
                      {formatEstimatedTime(path.estimatedTimeRemaining)}
                    </div>
                  </div>
                )}
              </div>

              <div className="flex flex-col space-y-2 ml-4">
                {path.status === 'active' && (
                  <>
                    <Button
                      onClick={() => onContinuePath(path.id)}
                      size="sm"
                    >
                      Continue
                    </Button>
                    <Button
                      onClick={() => onPausePath(path.id)}
                      variant="outline"
                      size="sm"
                    >
                      Pause
                    </Button>
                  </>
                )}
                {path.status === 'paused' && (
                  <Button
                    onClick={() => onContinuePath(path.id)}
                    size="sm"
                  >
                    Resume
                  </Button>
                )}
                {path.status === 'completed' && (
                  <Button
                    onClick={() => setExpandedPath(isExpanded ? null : path.id)}
                    variant="outline"
                    size="sm"
                  >
                    View Details
                  </Button>
                )}
              </div>
            </div>

            {/* Progress Bar */}
            <div className="mb-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">Progress</span>
                <span className="text-sm text-gray-600">
                  {path.completedTopics} / {path.totalTopics} topics ({Math.round(path.progressPercentage)}%)
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full transition-all duration-300 ${
                    path.status === 'completed' ? 'bg-green-600' : 'bg-blue-600'
                  }`}
                  style={{ width: `${path.progressPercentage}%` }}
                ></div>
              </div>
            </div>

            {/* Expandable Topic Details */}
            {isExpanded && (
              <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                <h4 className="font-medium text-gray-900 mb-3">Topic Progress</h4>
                <div className="space-y-2">
                  {path.topics.map((topic, index) => (
                    <div key={topic.id} className="flex items-center justify-between p-2 bg-white rounded border">
                      <div className="flex items-center space-x-3">
                        <div className="flex-shrink-0">
                          {topic.status === 'completed' && (
                            <CheckCircle className="w-5 h-5 text-green-600" />
                          )}
                          {topic.status === 'current' && (
                            <div className="w-5 h-5 rounded-full bg-blue-600 flex items-center justify-center">
                              <div className="w-2 h-2 bg-white rounded-full"></div>
                            </div>
                          )}
                          {topic.status === 'locked' && (
                            <div className="w-5 h-5 rounded-full bg-gray-300"></div>
                          )}
                        </div>
                        <div>
                          <div className="font-medium text-gray-900">{topic.title}</div>
                          {topic.completedAt && (
                            <div className="text-xs text-gray-500">
                              Completed {formatTimeAgo(topic.completedAt)}
                              {topic.timeSpent && ` • ${topic.timeSpent}m`}
                            </div>
                          )}
                        </div>
                      </div>
                      <div className="text-sm text-gray-500 capitalize">
                        {topic.status}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {!isExpanded && path.topics.length > 0 && (
              <Button
                onClick={() => setExpandedPath(path.id)}
                variant="outline"
                size="sm"
                className="w-full mt-2"
              >
                View Topic Details
              </Button>
            )}
          </Card>
        )
      })}
    </div>
  )
}