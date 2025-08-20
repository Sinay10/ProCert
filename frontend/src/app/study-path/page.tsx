'use client'

import { useState, useEffect } from 'react'
import { useSession } from 'next-auth/react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  RecommendationDisplay,
  StudyPathVisualization,
  RecommendationFeedback,
  PersonalizedSuggestions,
  StudyScheduler,
  GoalSetting,
  ActiveStudyPaths
} from '@/components/recommendations'
import { DemoBanner } from '@/components/demo'
import { apiClient, API_ENDPOINTS } from '@/lib/api-client'
import { 
  StudyRecommendation, 
  StudyPath, 
  UserAnalytics,
  RecommendationResponse 
} from '@/types/api'

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

// Helper function to convert frontend certification names to backend format
const getCertificationType = (certification: string): string => {
  const certMap: Record<string, string> = {
    'aws-solutions-architect-associate': 'SAA',
    'aws-developer-associate': 'DVA',
    'aws-sysops-administrator': 'SOA',
    'aws-solutions-architect-professional': 'SAP'
  }
  return certMap[certification] || 'SAA'
}

import { mockDataStore } from '@/lib/mock-data-store'

export default function StudyPathPage() {
  const { data: session } = useSession()
  const [recommendations, setRecommendations] = useState<StudyRecommendation[]>([])
  const [studyPath, setStudyPath] = useState<StudyPath | null>(null)
  const [analytics, setAnalytics] = useState<UserAnalytics | null>(null)
  const [loading, setLoading] = useState(true)
  const [selectedCertification, setSelectedCertification] = useState('aws-solutions-architect-associate')
  const [showFeedback, setShowFeedback] = useState<string | null>(null)
  const [usingMockData, setUsingMockData] = useState(false)
  
  // Use centralized mock data store for demo mode
  const [activePaths, setActivePaths] = useState<any[]>([])
  const [studySessions, setStudySessions] = useState<any[]>([])
  const [goals, setGoals] = useState<any[]>([])

  // Subscribe to mock data updates
  useEffect(() => {
    const unsubscribe = mockDataStore.subscribe(() => {
      if (usingMockData || mockDataStore.demoMode) {
        setActivePaths(mockDataStore.activePaths)
        setStudySessions(mockDataStore.studySessions)
        setGoals(mockDataStore.goals)
        setAnalytics(mockDataStore.analytics)
        setRecommendations(mockDataStore.recommendations)
        setStudyPath(mockDataStore.studyPath)
      }
    })
    
    // Initialize with current mock data if using mock data
    if (usingMockData || mockDataStore.demoMode) {
      setActivePaths(mockDataStore.activePaths)
      setStudySessions(mockDataStore.studySessions)
      setGoals(mockDataStore.goals)
    }
    
    return unsubscribe
  }, [usingMockData])

  useEffect(() => {
    if (session?.userId) {
      loadData()
    }
  }, [session?.userId, selectedCertification])

  const loadData = async () => {
    if (!session?.userId) {
      console.log('No session userId available')
      return
    }

    setLoading(true)
    
    try {
      // Try to load real data first
      // const certType = getCertificationType(selectedCertification)
      // const recommendationsData = await apiClient.get<RecommendationResponse>(API_ENDPOINTS.RECOMMENDATIONS(session.userId) + `?certification_type=${certType}&limit=10`)
      // const studyPathData = await apiClient.get<StudyPath>(API_ENDPOINTS.STUDY_PATH(session.userId, selectedCertification) + `?certification_type=${certType}`)
      // const analyticsData = await apiClient.get<UserAnalytics>(API_ENDPOINTS.ANALYTICS(session.userId))
      
      // For now, always use mock data
      throw new Error('API not implemented yet')
    } catch (error) {
      console.log('Using mock data for study path page')
      setRecommendations(mockDataStore.recommendations)
      setStudyPath(mockDataStore.studyPath)
      setAnalytics(mockDataStore.analytics)
      setUsingMockData(true)
      
      // Enable demo mode and populate demo data
      mockDataStore.setDemoMode(true)
    } finally {
      setLoading(false)
    }
  }

  const handleRecommendationClick = (recommendation: StudyRecommendation) => {
    // Navigate to appropriate section based on recommendation type
    switch (recommendation.type) {
      case 'quiz':
        window.location.href = '/quizzes'
        break
      case 'content':
        window.location.href = '/chat'
        break
      case 'review':
        // Could navigate to a review section or open content
        break
      default:
        console.log('Starting recommendation:', recommendation)
    }
  }

  const handleRecommendationFeedback = async (
    recommendationId: string, 
    feedback: 'helpful' | 'not_helpful' | 'completed'
  ) => {
    if (!session?.userId) return

    try {
      await apiClient.post(API_ENDPOINTS.RECOMMENDATION_FEEDBACK, {
        user_id: session.userId,
        recommendation_id: recommendationId,
        action: feedback
      })
      
      // Refresh recommendations
      loadData()
    } catch (error) {
      console.error('Failed to submit feedback:', error)
    }
  }

  const handleDetailedFeedback = async (feedback: {
    recommendationId: string
    rating: number
    helpful: boolean
    comments?: string
    categories: string[]
  }) => {
    if (!session?.userId) return

    try {
      await apiClient.post(API_ENDPOINTS.RECOMMENDATION_FEEDBACK, {
        user_id: session.userId,
        recommendation_id: feedback.recommendationId,
        action: feedback.helpful ? 'helpful' : 'not_helpful',
        rating: feedback.rating,
        comments: feedback.comments,
        categories: feedback.categories
      })
      
      setShowFeedback(null)
      loadData()
    } catch (error) {
      console.error('Failed to submit detailed feedback:', error)
    }
  }

  const handleTopicClick = (topicIndex: number) => {
    if (!studyPath || !studyPath.path || topicIndex >= studyPath.path.length) return
    
    const topic = studyPath.path[topicIndex]
    if (topic && topic.status === 'current') {
      // Navigate to study the current topic
      window.location.href = '/chat'
    }
  }

  const handleStartStudyPathFromVisualization = () => {
    if (!studyPath || !studyPath.path || studyPath.path.length === 0) return
    
    const pathData = {
      certification: getCertificationType(selectedCertification),
      totalTopics: studyPath.path.length,
      firstTopic: studyPath.path.find(topic => topic.status === 'current')?.topic || studyPath.path[0]?.topic,
      estimatedTime: studyPath.path.reduce((total, topic) => total + topic.estimated_time, 0),
      topics: studyPath.path.map((topic, index) => ({
        id: `topic-${index}`,
        title: topic.topic,
        status: index === 0 ? 'current' : 'locked'
      }))
    }
    
    handleStartStudyPath(pathData)
  }

  const handleSuggestionClick = (suggestion: PersonalizedSuggestion) => {
    // Handle different suggestion types
    switch (suggestion.type) {
      case 'weakness_focus':
      case 'strength_build':
        window.location.href = '/quizzes'
        break
      case 'certification_prep':
        window.location.href = '/progress'
        break
      case 'time_optimization':
        // Could open study tips or scheduling
        break
    }
  }

  // Session management functions (these would connect to backend in production)
  const handleScheduleSession = async (session: any) => {
    console.log('Scheduling session:', session)
    
    if (usingMockData) {
      mockDataStore.addStudySession(session)
    } else {
      // Real API call would go here
      const newSession = {
        ...session,
        id: `session-${Date.now()}`,
        completed: false
      }
      setStudySessions(prev => [...prev, newSession])
    }
  }

  const handleUpdateSession = async (sessionId: string, updates: any) => {
    console.log('Updating session:', sessionId, updates)
    
    if (usingMockData) {
      mockDataStore.updateStudySession(sessionId, updates)
    } else {
      // Real API call would go here
      setStudySessions(prev => prev.map(session => 
        session.id === sessionId 
          ? { ...session, ...updates }
          : session
      ))
    }
  }

  const handleDeleteSession = async (sessionId: string) => {
    console.log('Deleting session:', sessionId)
    
    if (usingMockData) {
      mockDataStore.deleteStudySession(sessionId)
    } else {
      // Real API call would go here
      setStudySessions(prev => prev.filter(session => session.id !== sessionId))
    }
  }

  const handleCreateGoal = async (goal: any) => {
    console.log('Creating goal:', goal)
    
    if (usingMockData) {
      mockDataStore.addGoal(goal)
    } else {
      // Real API call would go here
      const newGoal = {
        ...goal,
        id: `goal-${Date.now()}`,
        createdAt: new Date().toISOString()
      }
      setGoals(prev => [...prev, newGoal])
    }
  }

  const handleUpdateGoal = async (goalId: string, updates: any) => {
    console.log('Updating goal:', goalId, updates)
    
    if (usingMockData) {
      mockDataStore.updateGoal(goalId, updates)
    } else {
      // Real API call would go here
      setGoals(prev => prev.map(goal => 
        goal.id === goalId 
          ? { ...goal, ...updates }
          : goal
      ))
    }
  }

  const handleDeleteGoal = async (goalId: string) => {
    console.log('Deleting goal:', goalId)
    
    if (usingMockData) {
      mockDataStore.deleteGoal(goalId)
    } else {
      // Real API call would go here
      setGoals(prev => prev.filter(goal => goal.id !== goalId))
    }
  }

  // Active Study Path handlers
  const handleStartStudyPath = async (pathData: any) => {
    console.log('Starting new study path:', pathData)
    
    if (usingMockData) {
      mockDataStore.startStudyPath(pathData)
    } else {
      // Real API call would go here
      const newPath = {
        id: `path-${Date.now()}`,
        title: `${pathData.certification} Study Path`,
        certification: pathData.certification,
        startedAt: new Date().toISOString(),
        lastAccessedAt: new Date().toISOString(),
        totalTopics: pathData.totalTopics || 8,
        completedTopics: 0,
        currentTopic: pathData.firstTopic || 'Getting Started',
        estimatedTimeRemaining: pathData.estimatedTime || 240,
        status: 'active' as const,
        progressPercentage: 0,
        topics: pathData.topics || []
      }
      setActivePaths(prev => [newPath, ...prev])
    }
    
    // Navigate to the study content (could be chat, quiz, or dedicated study page)
    window.location.href = '/chat'
  }

  const handleContinuePath = async (pathId: string) => {
    console.log('Continuing study path:', pathId)
    
    const updates = { 
      lastAccessedAt: new Date().toISOString(), 
      status: 'active' 
    }
    
    if (usingMockData) {
      mockDataStore.updateActivePath(pathId, updates)
    } else {
      // Real API call would go here
      setActivePaths(prev => prev.map(path => 
        path.id === pathId ? { ...path, ...updates } : path
      ))
    }
    
    // Navigate to appropriate study content
    window.location.href = '/chat'
  }

  const handlePausePath = async (pathId: string) => {
    console.log('Pausing study path:', pathId)
    
    const updates = { status: 'paused' }
    
    if (usingMockData) {
      mockDataStore.updateActivePath(pathId, updates)
    } else {
      // Real API call would go here
      setActivePaths(prev => prev.map(path => 
        path.id === pathId ? { ...path, ...updates } : path
      ))
    }
  }

  const handleCompletePath = async (pathId: string) => {
    console.log('Completing study path:', pathId)
    
    const updates = { 
      status: 'completed', 
      progressPercentage: 100, 
      completedTopics: activePaths.find(p => p.id === pathId)?.totalTopics || 0
    }
    
    if (usingMockData) {
      mockDataStore.updateActivePath(pathId, updates)
    } else {
      // Real API call would go here
      setActivePaths(prev => prev.map(path => 
        path.id === pathId ? { ...path, ...updates } : path
      ))
    }
  }

  if (!session) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-lg shadow-sm border p-8 text-center">
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Sign In Required</h2>
          <p className="text-gray-600">Please sign in to access your personalized study path.</p>
        </div>
      </div>
    )
  }

  return (
    <>
      {usingMockData && <DemoBanner />}
      <div className="max-w-6xl mx-auto">
        <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Study Path & Recommendations</h1>
        <p className="text-gray-600 mt-2">
          Follow your personalized learning journey and track your progress
        </p>
        
        {usingMockData && (
          <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-yellow-800">
                  Demo Mode
                </h3>
                <div className="mt-2 text-sm text-yellow-700">
                  <p>
                    You're viewing sample recommendation data. To see your personalized recommendations, 
                    please ensure you're properly signed in and have completed some quizzes or study activities.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Certification Selector */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Select Certification
        </label>
        <select
          value={selectedCertification}
          onChange={(e) => setSelectedCertification(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="aws-solutions-architect-associate">AWS Solutions Architect Associate</option>
          <option value="aws-developer-associate">AWS Developer Associate</option>
          <option value="aws-sysops-administrator">AWS SysOps Administrator</option>
          <option value="aws-solutions-architect-professional">AWS Solutions Architect Professional</option>
        </select>
      </div>

      {/* Active Study Paths Section - Always visible at top */}
      <div className="mb-8">
        <ActiveStudyPaths
          onContinuePath={handleContinuePath}
          onPausePath={handlePausePath}
          onCompletePath={handleCompletePath}
          activePaths={activePaths}
          loading={loading}
        />
      </div>

      <Tabs defaultValue="recommendations" className="space-y-6">
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="recommendations">Recommendations</TabsTrigger>
          <TabsTrigger value="study-path">Study Path</TabsTrigger>
          <TabsTrigger value="suggestions">Suggestions</TabsTrigger>
          <TabsTrigger value="scheduler">Schedule</TabsTrigger>
          <TabsTrigger value="goals">Goals</TabsTrigger>
          <TabsTrigger value="feedback">Feedback</TabsTrigger>
        </TabsList>

        <TabsContent value="recommendations" className="space-y-6">
          <RecommendationDisplay
            recommendations={recommendations}
            onRecommendationClick={handleRecommendationClick}
            onFeedback={handleRecommendationFeedback}
            loading={loading}
          />
        </TabsContent>

        <TabsContent value="study-path" className="space-y-6">
          {studyPath ? (
            <StudyPathVisualization
              studyPath={studyPath}
              onTopicClick={handleTopicClick}
              onStartPath={handleStartStudyPathFromVisualization}
              loading={loading}
            />
          ) : (
            <div className="bg-white rounded-lg shadow-sm border p-8 text-center">
              <p className="text-gray-600">
                {loading ? 'Loading study path...' : 'No study path available for this certification.'}
              </p>
            </div>
          )}
        </TabsContent>

        <TabsContent value="suggestions" className="space-y-6">
          {analytics ? (
            <PersonalizedSuggestions
              analytics={analytics}
              recommendations={recommendations}
              onSuggestionClick={handleSuggestionClick}
              loading={loading}
            />
          ) : (
            <div className="bg-white rounded-lg shadow-sm border p-8 text-center">
              <p className="text-gray-600">
                {loading ? 'Loading suggestions...' : 'Complete some activities to receive personalized suggestions.'}
              </p>
            </div>
          )}
        </TabsContent>

        <TabsContent value="scheduler" className="space-y-6">
          <StudyScheduler
            onScheduleSession={handleScheduleSession}
            onUpdateSession={handleUpdateSession}
            onDeleteSession={handleDeleteSession}
            existingSessions={studySessions}
          />
        </TabsContent>

        <TabsContent value="goals" className="space-y-6">
          <GoalSetting
            onCreateGoal={handleCreateGoal}
            onUpdateGoal={handleUpdateGoal}
            onDeleteGoal={handleDeleteGoal}
            existingGoals={goals}
            userProgress={{
              totalStudyTime: 120,
              quizzesCompleted: 15,
              averageScore: 78,
              streakDays: 5
            }}
          />
        </TabsContent>

        <TabsContent value="feedback" className="space-y-6">
          {showFeedback ? (
            <RecommendationFeedback
              recommendationId={showFeedback}
              onSubmitFeedback={handleDetailedFeedback}
              onClose={() => setShowFeedback(null)}
            />
          ) : (
            <div className="bg-white rounded-lg shadow-sm border p-8 text-center">
              <h3 className="text-lg font-medium text-gray-900 mb-2">Recommendation Feedback</h3>
              <p className="text-gray-600 mb-4">
                Select a recommendation from the Recommendations tab to provide detailed feedback.
              </p>
              <button
                onClick={() => setShowFeedback('demo-recommendation')}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Try Demo Feedback
              </button>
            </div>
          )}
        </TabsContent>
      </Tabs>
      </div>
    </>
  )
}