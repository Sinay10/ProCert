'use client'

import { useState, useEffect } from 'react'
import { TrendingUp, Brain, Target, Clock, BookOpen, Award, ChevronRight } from 'lucide-react'
import { UserAnalytics, StudyRecommendation } from '@/types/api'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

interface PersonalizedSuggestionsProps {
  analytics: UserAnalytics | null
  recommendations: StudyRecommendation[]
  onSuggestionClick: (suggestion: PersonalizedSuggestion) => void
  loading?: boolean
}

interface PersonalizedSuggestion {
  id: string
  type: 'weakness_focus' | 'strength_build' | 'certification_prep' | 'time_optimization'
  title: string
  description: string
  reasoning: string
  estimatedTime: number
  priority: number
  actionItems: string[]
  relatedContent?: string[]
}

export function PersonalizedSuggestions({
  analytics,
  recommendations,
  onSuggestionClick,
  loading = false
}: PersonalizedSuggestionsProps) {
  const [suggestions, setSuggestions] = useState<PersonalizedSuggestion[]>([])
  const [selectedType, setSelectedType] = useState<string>('all')

  useEffect(() => {
    if (analytics && recommendations) {
      try {
        const generatedSuggestions = generatePersonalizedSuggestions(analytics, recommendations)
        setSuggestions(generatedSuggestions)
      } catch (error) {
        console.error('Error generating personalized suggestions:', error)
        setSuggestions([])
      }
    }
  }, [analytics, recommendations])

  const generatePersonalizedSuggestions = (
    analytics: UserAnalytics | null,
    recommendations: StudyRecommendation[]
  ): PersonalizedSuggestion[] => {
    const suggestions: PersonalizedSuggestion[] = []

    // Return empty suggestions if analytics is null
    if (!analytics) {
      return suggestions
    }

    // Ensure analytics has the expected structure with defaults
    const performance = analytics?.performance || {
      strengths: [],
      weaknesses: [],
      improvement_rate: 0.5
    }
    
    const predictions = analytics?.predictions || {
      certification_readiness: {},
      estimated_study_time: {}
    }

    // Weakness-focused suggestions
    if (performance.weaknesses.length > 0) {
      const topWeakness = performance.weaknesses[0]
      suggestions.push({
        id: 'weakness-focus-1',
        type: 'weakness_focus',
        title: `Strengthen Your ${topWeakness} Skills`,
        description: `Focus on improving your understanding of ${topWeakness} concepts`,
        reasoning: `Based on your recent quiz performance, ${topWeakness} appears to be an area where additional study would be most beneficial.`,
        estimatedTime: 45,
        priority: 9,
        actionItems: [
          `Review ${topWeakness} fundamentals`,
          `Take practice quizzes on ${topWeakness}`,
          `Ask the chatbot specific questions about ${topWeakness}`,
          'Schedule focused study sessions'
        ],
        relatedContent: recommendations
          .filter(r => r.reasoning.toLowerCase().includes(topWeakness.toLowerCase()))
          .map(r => r.content_id)
          .filter(Boolean) as string[]
      })
    }

    // Strength-building suggestions
    if (performance.strengths.length > 0) {
      const topStrength = performance.strengths[0]
      suggestions.push({
        id: 'strength-build-1',
        type: 'strength_build',
        title: `Advanced ${topStrength} Topics`,
        description: `Build on your strong foundation in ${topStrength}`,
        reasoning: `You've shown excellent performance in ${topStrength}. Consider exploring advanced topics to deepen your expertise.`,
        estimatedTime: 30,
        priority: 6,
        actionItems: [
          `Explore advanced ${topStrength} scenarios`,
          'Take challenging practice questions',
          'Review real-world case studies',
          'Consider teaching concepts to reinforce learning'
        ]
      })
    }

    // Certification readiness suggestions
    Object.entries(predictions.certification_readiness).forEach(([cert, readiness]) => {
      if (readiness > 0.7) {
        suggestions.push({
          id: `cert-prep-${cert}`,
          type: 'certification_prep',
          title: `${cert} Certification Final Prep`,
          description: `You're ${Math.round(readiness * 100)}% ready for ${cert}`,
          reasoning: `Your performance indicates strong readiness for the ${cert} certification. Focus on final preparation strategies.`,
          estimatedTime: 60,
          priority: 8,
          actionItems: [
            'Take full-length practice exams',
            'Review exam objectives checklist',
            'Focus on time management strategies',
            'Schedule your certification exam'
          ]
        })
      } else if (readiness > 0.4) {
        suggestions.push({
          id: `cert-study-${cert}`,
          type: 'certification_prep',
          title: `Continue ${cert} Preparation`,
          description: `Build towards ${cert} certification readiness`,
          reasoning: `You're making good progress towards ${cert} certification. Continue with structured study to improve readiness.`,
          estimatedTime: 90,
          priority: 7,
          actionItems: [
            'Focus on weak knowledge areas',
            'Increase practice quiz frequency',
            'Review certification study guide',
            'Join study groups or forums'
          ]
        })
      }
    })

    // Time optimization suggestions (only if we have some performance data)
    if (performance.improvement_rate < 0.5 && performance.improvement_rate > 0) {
      suggestions.push({
        id: 'time-optimization-1',
        type: 'time_optimization',
        title: 'Optimize Your Study Approach',
        description: 'Improve learning efficiency with better study strategies',
        reasoning: 'Your improvement rate suggests there may be opportunities to optimize your study methods for better results.',
        estimatedTime: 20,
        priority: 7,
        actionItems: [
          'Try spaced repetition techniques',
          'Use active recall methods',
          'Set specific learning objectives',
          'Track and analyze your study patterns'
        ]
      })
    }

    return suggestions.sort((a, b) => b.priority - a.priority)
  }

  const getSuggestionIcon = (type: string) => {
    switch (type) {
      case 'weakness_focus':
        return <Target className="w-5 h-5 text-red-600" />
      case 'strength_build':
        return <TrendingUp className="w-5 h-5 text-green-600" />
      case 'certification_prep':
        return <Award className="w-5 h-5 text-purple-600" />
      case 'time_optimization':
        return <Brain className="w-5 h-5 text-blue-600" />
      default:
        return <BookOpen className="w-5 h-5 text-gray-600" />
    }
  }

  const getSuggestionColor = (type: string) => {
    switch (type) {
      case 'weakness_focus':
        return 'border-red-200 bg-red-50'
      case 'strength_build':
        return 'border-green-200 bg-green-50'
      case 'certification_prep':
        return 'border-purple-200 bg-purple-50'
      case 'time_optimization':
        return 'border-blue-200 bg-blue-50'
      default:
        return 'border-gray-200 bg-gray-50'
    }
  }

  const filteredSuggestions = selectedType === 'all' 
    ? suggestions 
    : suggestions.filter(s => s.type === selectedType)

  if (loading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <Card key={i} className="p-6" data-testid="loading-skeleton">
            <div className="animate-pulse">
              <div className="flex items-center space-x-3 mb-3">
                <div className="w-5 h-5 bg-gray-200 rounded"></div>
                <div className="h-5 bg-gray-200 rounded w-1/3"></div>
              </div>
              <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
              <div className="h-3 bg-gray-200 rounded w-1/2"></div>
            </div>
          </Card>
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-900">Personalized Suggestions</h2>
        <select
          value={selectedType}
          onChange={(e) => setSelectedType(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="all">All Suggestions</option>
          <option value="weakness_focus">Focus on Weaknesses</option>
          <option value="strength_build">Build on Strengths</option>
          <option value="certification_prep">Certification Prep</option>
          <option value="time_optimization">Study Optimization</option>
        </select>
      </div>

      {filteredSuggestions.length === 0 ? (
        <Card className="p-8 text-center">
          <Brain className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Suggestions Available</h3>
          <p className="text-gray-600">
            Complete more activities to receive personalized study suggestions.
          </p>
        </Card>
      ) : (
        <div className="space-y-4">
          {filteredSuggestions.map((suggestion) => (
            <Card key={suggestion.id} className={`p-6 border-l-4 ${getSuggestionColor(suggestion.type)}`}>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-3">
                    {getSuggestionIcon(suggestion.type)}
                    <h3 className="text-lg font-semibold text-gray-900">
                      {suggestion.title}
                    </h3>
                    <span className="px-2 py-1 text-xs font-medium bg-gray-100 text-gray-800 rounded-full">
                      Priority: {suggestion.priority}/10
                    </span>
                  </div>

                  <p className="text-gray-700 mb-3">{suggestion.description}</p>

                  <div className="mb-4 p-3 bg-white rounded border">
                    <h4 className="font-medium text-gray-900 mb-2">Why this suggestion?</h4>
                    <p className="text-sm text-gray-700">{suggestion.reasoning}</p>
                  </div>

                  <div className="mb-4">
                    <h4 className="font-medium text-gray-900 mb-2">Action Items:</h4>
                    <ul className="space-y-1">
                      {suggestion.actionItems.map((item, index) => (
                        <li key={index} className="flex items-start space-x-2 text-sm text-gray-700">
                          <span className="text-blue-600 mt-1">•</span>
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div className="flex items-center space-x-4 text-sm text-gray-600">
                    <div className="flex items-center space-x-1">
                      <Clock className="w-4 h-4" />
                      <span>{suggestion.estimatedTime} min</span>
                    </div>
                    {suggestion.relatedContent && suggestion.relatedContent.length > 0 && (
                      <div className="flex items-center space-x-1">
                        <BookOpen className="w-4 h-4" />
                        <span>{suggestion.relatedContent.length} related resources</span>
                      </div>
                    )}
                  </div>
                </div>

                <Button
                  onClick={() => onSuggestionClick(suggestion)}
                  className="ml-4"
                >
                  Start <ChevronRight className="w-4 h-4 ml-1" />
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}