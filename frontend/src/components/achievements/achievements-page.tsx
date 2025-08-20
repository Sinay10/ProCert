'use client'

import { useState, useEffect } from 'react'
import { useSession } from 'next-auth/react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { 
  Trophy, 
  Award, 
  Star, 
  Target, 
  Clock, 
  BookOpen, 
  Brain, 
  TrendingUp,
  Calendar,
  Zap,
  Shield,
  Crown,
  Loader2,
  AlertCircle
} from 'lucide-react'
import { AchievementStats } from './achievement-stats'
import { AchievementCard } from './achievement-card'
import { apiClient, API_ENDPOINTS } from '@/lib/api-client'
import { UserProgress } from '@/types/api'
import { mockDataStore } from '@/lib/mock-data-store'
import { DemoBanner } from '@/components/demo'

export interface Achievement {
  id: string
  title: string
  description: string
  icon: any
  rarity: 'common' | 'rare' | 'epic' | 'legendary'
  category: 'study' | 'quiz' | 'streak' | 'milestone' | 'special'
  earned: boolean
  earnedAt?: string
  progress?: number
  maxProgress?: number
  requirement: string
  points: number
}

export function AchievementsPage() {
  const { data: session } = useSession()
  const [achievements, setAchievements] = useState<Achievement[]>([])
  const [progressData, setProgressData] = useState<UserProgress | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  const [usingMockData, setUsingMockData] = useState(false)

  useEffect(() => {
    if (session?.userId) {
      fetchProgressData()
    }
  }, [session?.userId])

  useEffect(() => {
    if (progressData) {
      calculateAchievements()
    }
  }, [progressData])

  // Subscribe to mock data updates
  useEffect(() => {
    const unsubscribe = mockDataStore.subscribe(() => {
      if (usingMockData) {
        setProgressData(mockDataStore.progress)
      }
    })

    return unsubscribe
  }, [usingMockData])

  const fetchProgressData = async () => {
    if (!session?.userId) return

    try {
      setLoading(true)
      setError(null)
      
      // Try to load real data first
      // const data = await apiClient.get<UserProgress>(API_ENDPOINTS.PROGRESS(session.userId))
      // setProgressData(data)
      // setUsingMockData(false)
      
      // For now, always use mock data
      throw new Error('API not implemented yet')
    } catch (err) {
      console.log('Using mock data for achievements page')
      setProgressData(mockDataStore.progress)
      setUsingMockData(true)
    } finally {
      setLoading(false)
    }
  }

  const calculateAchievements = () => {
    if (!progressData) return

    const data = progressData.overall
    const certData = progressData.by_certification || {}
    
    // Get earned achievements from mock data store
    const earnedAchievements = mockDataStore.achievements

    // Helper function to check if achievement is earned
    const isAchievementEarned = (id: string) => {
      return earnedAchievements.some(a => a.id === id)
    }

    // Helper function to get earned date
    const getEarnedDate = (id: string) => {
      const earned = earnedAchievements.find(a => a.id === id)
      return earned?.earned_date
    }

    const allAchievements: Achievement[] = [
      // Study Time Achievements
      {
        id: 'first-quiz',
        title: earnedAchievements.find(a => a.id === 'first-quiz')?.title || 'First Quiz Completed',
        description: earnedAchievements.find(a => a.id === 'first-quiz')?.description || 'Complete your first quiz',
        icon: Trophy,
        rarity: 'common',
        category: 'milestone',
        earned: isAchievementEarned('first-quiz'),
        earnedAt: getEarnedDate('first-quiz'),
        progress: data.quizzes_completed >= 1 ? 1 : 0,
        maxProgress: 1,
        requirement: 'Complete 1 quiz',
        points: 15
      },
      {
        id: 'study-streak-3',
        title: earnedAchievements.find(a => a.id === 'study-streak-3')?.title || '3-Day Study Streak',
        description: earnedAchievements.find(a => a.id === 'study-streak-3')?.description || 'Study for 3 consecutive days',
        icon: Calendar,
        rarity: 'common',
        category: 'streak',
        earned: isAchievementEarned('study-streak-3'),
        earnedAt: getEarnedDate('study-streak-3'),
        progress: Math.min(data.streak_days, 3),
        maxProgress: 3,
        requirement: '3-day study streak',
        points: 50
      },
      {
        id: 'score-improvement',
        title: earnedAchievements.find(a => a.id === 'score-improvement')?.title || 'Score Improver',
        description: earnedAchievements.find(a => a.id === 'score-improvement')?.description || 'Improved average score significantly',
        icon: TrendingUp,
        rarity: 'rare',
        category: 'quiz',
        earned: isAchievementEarned('score-improvement'),
        earnedAt: getEarnedDate('score-improvement'),
        progress: data.average_score >= 75 ? 100 : Math.round((data.average_score / 75) * 100),
        maxProgress: 100,
        requirement: 'Improve quiz performance',
        points: 100
      },
      {
        id: 'quiz-master-10',
        title: earnedAchievements.find(a => a.id === 'quiz-master-10')?.title || 'Quiz Master',
        description: earnedAchievements.find(a => a.id === 'quiz-master-10')?.description || 'Complete 10 practice quizzes',
        icon: Crown,
        rarity: 'rare',
        category: 'milestone',
        earned: isAchievementEarned('quiz-master-10'),
        earnedAt: getEarnedDate('quiz-master-10'),
        progress: Math.min(data.quizzes_completed, 10),
        maxProgress: 10,
        requirement: 'Complete 10 quizzes',
        points: 150
      },
      {
        id: 'high-scorer',
        title: earnedAchievements.find(a => a.id === 'high-scorer')?.title || 'High Scorer',
        description: earnedAchievements.find(a => a.id === 'high-scorer')?.description || 'Achieved 90%+ on a quiz',
        icon: Star,
        rarity: 'epic',
        category: 'quiz',
        earned: isAchievementEarned('high-scorer'),
        earnedAt: getEarnedDate('high-scorer'),
        progress: data.average_score >= 90 ? 100 : Math.round((data.average_score / 90) * 100),
        maxProgress: 100,
        requirement: 'Score 90%+ on any quiz',
        points: 200
      },

      // Additional achievements based on current progress
      {
        id: 'dedicated-learner',
        title: 'Dedicated Learner',
        description: 'Study for 10+ hours total',
        icon: BookOpen,
        rarity: 'common',
        category: 'study',
        earned: data.total_study_time >= 600,
        earnedAt: data.total_study_time >= 600 ? '2025-08-18' : undefined,
        progress: Math.min(data.total_study_time, 600),
        maxProgress: 600,
        requirement: 'Study for 10 hours',
        points: 75
      },
      {
        id: 'quiz-enthusiast',
        title: 'Quiz Enthusiast',
        description: 'Complete 25+ quizzes',
        icon: Brain,
        rarity: 'rare',
        category: 'quiz',
        earned: data.quizzes_completed >= 25,
        earnedAt: data.quizzes_completed >= 25 ? '2025-08-16' : undefined,
        progress: Math.min(data.quizzes_completed, 25),
        maxProgress: 25,
        requirement: 'Complete 25 quizzes',
        points: 125
      },
      {
        id: 'high-achiever',
        title: 'High Achiever',
        description: 'Maintain 85%+ average score',
        icon: Award,
        rarity: 'epic',
        category: 'quiz',
        earned: data.average_score >= 85,
        earnedAt: data.average_score >= 85 ? '2025-08-17' : undefined,
        progress: Math.min(data.average_score, 85),
        maxProgress: 85,
        requirement: 'Average 85% quiz score',
        points: 175
      },

      // Certification-specific achievements
      ...Object.entries(certData).map(([certType, certProgress]) => ({
        id: `cert-${certType}`,
        title: `${certType.replace('-', ' ').toUpperCase()} Explorer`,
        description: `Make progress in ${certType.replace('-', ' ').toUpperCase()} certification`,
        icon: Shield,
        rarity: 'rare' as const,
        category: 'milestone' as const,
        earned: certProgress.progress_percentage >= 50,
        earnedAt: certProgress.progress_percentage >= 50 ? '2025-08-15' : undefined,
        progress: Math.min(certProgress.progress_percentage, 50),
        maxProgress: 50,
        requirement: `50% ${certType.replace('-', ' ').toUpperCase()} progress`,
        points: 200
      }))
    ]

    setAchievements(allAchievements)
  }

  const categories = [
    { id: 'all', name: 'All Achievements', icon: Trophy },
    { id: 'study', name: 'Study Time', icon: Clock },
    { id: 'quiz', name: 'Quiz Mastery', icon: Brain },
    { id: 'streak', name: 'Consistency', icon: Calendar },
    { id: 'milestone', name: 'Milestones', icon: Target },
    { id: 'special', name: 'Special', icon: Star }
  ]

  const filteredAchievements = selectedCategory === 'all' 
    ? achievements 
    : achievements.filter(a => a.category === selectedCategory)

  const earnedAchievements = achievements.filter(a => a.earned)
  const totalPoints = earnedAchievements.reduce((sum, a) => sum + a.points, 0)

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary-600 mx-auto mb-4" />
          <p className="text-secondary-600">Loading achievements...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <Card className="border-red-200 bg-red-50">
        <CardContent className="pt-6">
          <div className="flex items-center space-x-3">
            <AlertCircle className="h-5 w-5 text-red-600" />
            <div>
              <h3 className="text-sm font-medium text-red-800">Error Loading Achievements</h3>
              <p className="text-sm text-red-700 mt-1">{error}</p>
            </div>
          </div>
          <Button 
            onClick={fetchProgressData}
            variant="outline"
            size="sm"
            className="mt-4"
          >
            Try Again
          </Button>
        </CardContent>
      </Card>
    )
  }

  return (
    <>
      {usingMockData && <DemoBanner />}
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-secondary-900">Achievements</h1>
          <p className="text-secondary-600 mt-2">
            Track your learning milestones and celebrate your progress
          </p>
        </div>

      {/* Achievement Stats */}
      <AchievementStats 
        totalAchievements={achievements.length}
        earnedAchievements={earnedAchievements.length}
        totalPoints={totalPoints}
      />

      {/* Category Filter */}
      <div className="flex flex-wrap gap-2">
        {categories.map((category) => {
          const Icon = category.icon
          const count = category.id === 'all' 
            ? achievements.length 
            : achievements.filter(a => a.category === category.id).length
          
          return (
            <Button
              key={category.id}
              variant={selectedCategory === category.id ? "primary" : "outline"}
              size="sm"
              onClick={() => setSelectedCategory(category.id)}
              className="flex items-center space-x-2"
            >
              <Icon className="h-4 w-4" />
              <span>{category.name}</span>
              <Badge variant="secondary" className="ml-1">
                {count}
              </Badge>
            </Button>
          )
        })}
      </div>

      {/* Achievements Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredAchievements.map((achievement) => (
          <AchievementCard key={achievement.id} achievement={achievement} />
        ))}
      </div>

      {filteredAchievements.length === 0 && (
        <div className="text-center py-12">
          <Trophy className="h-12 w-12 text-secondary-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-secondary-900 mb-2">No achievements found</h3>
          <p className="text-secondary-600">
            Try selecting a different category
          </p>
        </div>
      )}
      </div>
    </>
  )
}