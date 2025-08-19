'use client'

import { useEffect, useState } from 'react'
import { useSession } from 'next-auth/react'
import { useQuery } from '@tanstack/react-query'
import { apiClient, API_ENDPOINTS } from '@/lib/api-client'
import { UserProgress, UserAnalytics } from '@/types/api'
import { mockDataStore } from '@/lib/mock-data-store'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { ProgressOverview } from './progress-overview'
import { CertificationProgress } from './certification-progress'
import { PerformanceTrends } from './performance-trends'
import { StudyTimeTracker } from './study-time-tracker'
import { AchievementDisplay } from './achievement-display'
import { AnalyticsInsights } from './analytics-insights'
import { DemoBanner } from '@/components/demo'

export function ProgressDashboard() {
  const { data: session } = useSession()
  const [selectedTimeframe, setSelectedTimeframe] = useState<'week' | 'month' | 'quarter' | 'year'>('month')

  // Use centralized mock data store for consistent demo experience
  const [progressData, setProgressData] = useState<UserProgress | null>(null)
  const [analyticsData, setAnalyticsData] = useState<UserAnalytics | null>(null)
  const [usingMockData, setUsingMockData] = useState(false)

  useEffect(() => {
    const loadData = async () => {
      if (!session?.userId) return

      try {
        // Try to load real data first
        // const progressResponse = await apiClient.get<UserProgress>(API_ENDPOINTS.PROGRESS(session.userId))
        // const analyticsResponse = await apiClient.get<UserAnalytics>(API_ENDPOINTS.ANALYTICS(session.userId))
        // setProgressData(progressResponse)
        // setAnalyticsData(analyticsResponse)
        
        // For now, always use mock data
        throw new Error('API not implemented yet')
      } catch (error) {
        console.log('Using mock data for progress dashboard')
        setProgressData(mockDataStore.progress)
        setAnalyticsData(mockDataStore.analytics)
        setUsingMockData(true)
      }
    }

    loadData()

    // Subscribe to mock data updates if in demo mode
    const unsubscribe = mockDataStore.subscribe(() => {
      if (usingMockData) {
        setProgressData(mockDataStore.progress)
        setAnalyticsData(mockDataStore.analytics)
      }
    })

    return unsubscribe
  }, [session?.userId, usingMockData])

  const progressError = null

  if (!session?.userId) {
    return (
      <div className="max-w-6xl mx-auto">
        <Card>
          <CardContent className="p-6">
            <p className="text-center text-secondary-600">Please sign in to view your progress.</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (progressError) {
    return (
      <div className="max-w-6xl mx-auto">
        <Card>
          <CardContent className="p-6">
            <p className="text-center text-red-600">
              Error loading progress data. Please try again later.
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <>
      {usingMockData && <DemoBanner />}
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-secondary-900">Learning Progress</h1>
          <p className="text-secondary-600 mt-1">
            Track your performance and study analytics
          </p>
        </div>
        
        {/* Timeframe Selector */}
        <div className="flex bg-secondary-100 rounded-lg p-1">
          {(['week', 'month', 'quarter', 'year'] as const).map((timeframe) => (
            <button
              key={timeframe}
              onClick={() => setSelectedTimeframe(timeframe)}
              className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                selectedTimeframe === timeframe
                  ? 'bg-white text-primary-600 shadow-sm'
                  : 'text-secondary-600 hover:text-secondary-900'
              }`}
            >
              {timeframe.charAt(0).toUpperCase() + timeframe.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Demo Mode Indicator */}
      {usingMockData && (
        <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-yellow-800">Demo Mode</h3>
              <div className="mt-2 text-sm text-yellow-700">
                <p>You're viewing interactive demo data. Your actions across the app will update this progress dashboard in real-time!</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Progress Overview */}
      <ProgressOverview 
        data={progressData?.overall} 
        loading={!progressData} 
      />

      {/* Main Dashboard Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Charts and Trends */}
        <div className="lg:col-span-2 space-y-6">
          <PerformanceTrends 
            data={progressData?.trends} 
            loading={!progressData}
            timeframe={selectedTimeframe}
          />
          
          <CertificationProgress 
            data={progressData?.by_certification} 
            loading={!progressData} 
          />
        </div>

        {/* Right Column - Insights and Tracking */}
        <div className="space-y-6">
          <StudyTimeTracker 
            data={progressData?.overall} 
            loading={!progressData} 
          />
          
          <AchievementDisplay 
            progressData={progressData || undefined} 
            loading={!progressData} 
          />
          
          <AnalyticsInsights 
            data={analyticsData || undefined} 
            loading={!analyticsData} 
          />
        </div>
      </div>
      </div>
    </>
  )
}