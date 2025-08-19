'use client'

import { useState } from 'react'
import { X, Zap, TrendingUp, Target } from 'lucide-react'
import { mockDataStore } from '@/lib/mock-data-store'

interface DemoBannerProps {
  onDismiss?: () => void
}

export function DemoBanner({ onDismiss }: DemoBannerProps) {
  const [isVisible, setIsVisible] = useState(true)

  const handleDismiss = () => {
    setIsVisible(false)
    onDismiss?.()
  }

  const handleQuickAction = (action: string) => {
    switch (action) {
      case 'complete-quiz':
        mockDataStore.completeQuiz({
          certification: 'AWS Solutions Architect',
          score: Math.floor(Math.random() * 20) + 80, // 80-100%
          total_questions: 10,
          correct_answers: Math.floor(Math.random() * 3) + 8, // 8-10 correct
          topics: ['EC2', 'S3', 'VPC']
        })
        break
      case 'add-study-time':
        mockDataStore.addStudyTime(30) // Add 30 minutes
        break
      case 'start-path':
        mockDataStore.startStudyPath({
          certification: 'SAA',
          totalTopics: 6,
          firstTopic: 'AWS Fundamentals',
          estimatedTime: 180,
          topics: [
            { id: 'topic-1', title: 'AWS Fundamentals', status: 'current' },
            { id: 'topic-2', title: 'EC2 Deep Dive', status: 'locked' },
            { id: 'topic-3', title: 'Storage Solutions', status: 'locked' },
            { id: 'topic-4', title: 'Networking', status: 'locked' },
            { id: 'topic-5', title: 'Security', status: 'locked' },
            { id: 'topic-6', title: 'Final Review', status: 'locked' }
          ]
        })
        break
    }
  }

  if (!isVisible) return null

  return (
    <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between py-3">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <Zap className="w-5 h-5 text-yellow-300" />
              <span className="font-medium">Interactive Demo Mode</span>
            </div>
            <div className="hidden sm:flex items-center space-x-4 text-sm">
              <span className="opacity-90">Try these quick actions:</span>
              <button
                onClick={() => handleQuickAction('complete-quiz')}
                className="flex items-center space-x-1 px-2 py-1 bg-white/20 rounded hover:bg-white/30 transition-colors"
              >
                <Target className="w-3 h-3" />
                <span>Complete Quiz</span>
              </button>
              <button
                onClick={() => handleQuickAction('add-study-time')}
                className="flex items-center space-x-1 px-2 py-1 bg-white/20 rounded hover:bg-white/30 transition-colors"
              >
                <TrendingUp className="w-3 h-3" />
                <span>Add Study Time</span>
              </button>
              <button
                onClick={() => handleQuickAction('start-path')}
                className="flex items-center space-x-1 px-2 py-1 bg-white/20 rounded hover:bg-white/30 transition-colors"
              >
                <Target className="w-3 h-3" />
                <span>Start New Path</span>
              </button>
            </div>
          </div>
          <button
            onClick={handleDismiss}
            className="p-1 hover:bg-white/20 rounded transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  )
}