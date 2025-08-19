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

  const fetchProgressData = async () => {
    if (!session?.userId) return

    try {
      setLoading(true)
      setError(null)
      const data = await apiClient.get<UserProgress>(
        API_ENDPOINTS.PROGRESS(session.userId)
      )
      setProgressData(data)
    } catch (err) {
      console.error('Error fetching progress data:', err)
      setError('Failed to load progress data')
    } finally {
      setLoading(false)
    }
  }

  const calculateAchievements = () => {
    if (!progressData) return

    const data = progressData.overall
    const certData = progressData.by_certification || {}

    const allAchievements: Achievement[] = [
      // Study Time Achievements
      {
        id: 'first-hour',
        title: 'First Steps',
        description: 'Complete your first hour of study',
        icon: Clock,
        rarity: 'common',
        category: 'study',
        earned: data.total_study_time >= 60,
        earnedAt: data.total_study_time >= 60 ? new Date().toISOString() : undefined,
        progress: Math.min(data.total_study_time, 60),
        maxProgress: 60,
        requirement: 'Study for 1 hour',
        points: 10
      },
      {
        id: 'dedicated-learner',
        title: 'Dedicated Learner',
        description: 'Study for 10 hours total',
        icon: BookOpen,
        rarity: 'common',
        category: 'study',
        earned: data.total_study_time >= 600,
        earnedAt: data.total_study_time >= 600 ? new Date().toISOString() : undefined,
        progress: Math.min(data.total_study_time, 600),
        maxProgress: 600,
        requirement: 'Study for 10 hours',
        points: 50
      },
      {
        id: 'study-marathon',
        title: 'Study Marathon',
        description: 'Study for 50 hours total',
        icon: Target,
        rarity: 'rare',
        category: 'study',
        earned: data.total_study_time >= 3000,
        earnedAt: data.total_study_time >= 3000 ? new Date().toISOString() : undefined,
        progress: Math.min(data.total_study_time, 3000),
        maxProgress: 3000,
        requirement: 'Study for 50 hours',
        points: 200
      },

      // Quiz Achievements
      {
        id: 'first-quiz',
        title: 'Quiz Rookie',
        description: 'Complete your first quiz',
        icon: Brain,
        rarity: 'common',
        category: 'quiz',
        earned: data.quizzes_completed >= 1,
        earnedAt: data.quizzes_completed >= 1 ? new Date().toISOString() : undefined,
        progress: Math.min(data.quizzes_completed, 1),
        maxProgress: 1,
        requirement: 'Complete 1 quiz',
        points: 15
      },
      {
        id: 'quiz-enthusiast',
        title: 'Quiz Enthusiast',
        description: 'Complete 10 quizzes',
        icon: Star,
        rarity: 'common',
        category: 'quiz',
        earned: data.quizzes_completed >= 10,
        earnedAt: data.quizzes_completed >= 10 ? new Date().toISOString() : undefined,
        progress: Math.min(data.quizzes_completed, 10),
        maxProgress: 10,
        requirement: 'Complete 10 quizzes',
        points: 75
      },
      {
        id: 'quiz-master',
        title: 'Quiz Master',
        description: 'Complete 50 quizzes',
        icon: Crown,
        rarity: 'epic',
        category: 'quiz',
        earned: data.quizzes_completed >= 50,
        earnedAt: data.quizzes_completed >= 50 ? new Date().toISOString() : undefined,
        progress: Math.min(data.quizzes_completed, 50),
        maxProgress: 50,
        requirement: 'Complete 50 quizzes',
        points: 300
      },

      // Performance Achievements
      {
        id: 'high-achiever',
        title: 'High Achiever',
        description: 'Maintain an average score of 80% or higher',
        icon: TrendingUp,
        rarity: 'rare',
        category: 'milestone',
        earned: data.average_score >= 80,
        earnedAt: data.average_score >= 80 ? new Date().toISOString() : undefined,
        progress: Math.min(data.average_score, 80),
        maxProgress: 80,
        requirement: 'Average 80% quiz score',
        points: 150
      },
      {
        id: 'perfectionist',
        title: 'Perfectionist',
        description: 'Achieve a perfect 100% score on a quiz',
        icon: Shield,
        rarity: 'epic',
        category: 'milestone',
        earned: data.average_score >= 100, // This would need to be tracked differently in real implementation
        earnedAt: data.average_score >= 100 ? new Date().toISOString() : undefined,
        progress: data.average_score >= 100 ? 100 : 0,
        maxProgress: 100,
        requirement: 'Score 100% on any quiz',
        points: 250
      },

      // Streak Achievements
      {
        id: 'consistent',
        title: 'Consistent Learner',
        description: 'Study for 7 days in a row',
        icon: Calendar,
        rarity: 'rare',
        category: 'streak',
        earned: data.streak_days >= 7,
        earnedAt: data.streak_days >= 7 ? new Date().toISOString() : undefined,
        progress: Math.min(data.streak_days, 7),
        maxProgress: 7,
        requirement: '7-day study streak',
        points: 100
      },
      {
        id: 'unstoppable',
        title: 'Unstoppable',
        description: 'Study for 30 days in a row',
        icon: Zap,
        rarity: 'legendary',
        category: 'streak',
        earned: data.streak_days >= 30,
        earnedAt: data.streak_days >= 30 ? new Date().toISOString() : undefined,
        progress: Math.min(data.streak_days, 30),
        maxProgress: 30,
        requirement: '30-day study streak',
        points: 500
      },

      // Certification-specific achievements
      ...Object.entries(certData).map(([certType, certProgress]) => ({
        id: `cert-${certType}`,
        title: `${certType.toUpperCase()} Explorer`,
        description: `Complete 50% of ${certType.toUpperCase()} content`,
        icon: Award,
        rarity: 'rare' as const,
        category: 'milestone' as const,
        earned: certProgress.progress_percentage >= 50,
        earnedAt: certProgress.progress_percentage >= 50 ? new Date().toISOString() : undefined,
        progress: Math.min(certProgress.progress_percentage, 50),
        maxProgress: 50,
        requirement: `50% ${certType.toUpperCase()} progress`,
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
  )
}