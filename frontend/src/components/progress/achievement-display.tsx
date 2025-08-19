'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Trophy, Medal, Star, Zap, Target, BookOpen } from 'lucide-react'
import { UserProgress } from '@/types/api'

interface AchievementDisplayProps {
  progressData?: UserProgress
  loading: boolean
}

interface Achievement {
  id: string
  title: string
  description: string
  icon: React.ComponentType<{ className?: string }>
  earned: boolean
  progress?: number
  maxProgress?: number
  category: 'study' | 'quiz' | 'streak' | 'milestone'
  rarity: 'common' | 'rare' | 'epic' | 'legendary'
}

export function AchievementDisplay({ progressData, loading }: AchievementDisplayProps) {
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Trophy className="h-5 w-5" />
            Achievements
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse space-y-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="flex items-center gap-3">
                <div className="h-10 w-10 bg-secondary-200 rounded-full"></div>
                <div className="flex-1">
                  <div className="h-4 bg-secondary-200 rounded w-3/4 mb-1"></div>
                  <div className="h-3 bg-secondary-200 rounded w-1/2"></div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    )
  }

  // Calculate achievements based on progress data
  const calculateAchievements = (): Achievement[] => {
    const data = progressData?.overall
    const certData = progressData?.by_certification || {}
    
    return [
      // Study Time Achievements
      {
        id: 'first-hour',
        title: 'First Hour',
        description: 'Complete your first hour of study',
        icon: BookOpen,
        earned: (data?.total_study_time || 0) >= 60,
        progress: Math.min(data?.total_study_time || 0, 60),
        maxProgress: 60,
        category: 'study',
        rarity: 'common'
      },
      {
        id: 'dedicated-learner',
        title: 'Dedicated Learner',
        description: 'Study for 10 hours total',
        icon: BookOpen,
        earned: (data?.total_study_time || 0) >= 600,
        progress: Math.min(data?.total_study_time || 0, 600),
        maxProgress: 600,
        category: 'study',
        rarity: 'rare'
      },
      {
        id: 'study-master',
        title: 'Study Master',
        description: 'Accumulate 50 hours of study time',
        icon: BookOpen,
        earned: (data?.total_study_time || 0) >= 3000,
        progress: Math.min(data?.total_study_time || 0, 3000),
        maxProgress: 3000,
        category: 'study',
        rarity: 'epic'
      },

      // Quiz Achievements
      {
        id: 'first-quiz',
        title: 'Quiz Rookie',
        description: 'Complete your first quiz',
        icon: Target,
        earned: (data?.quizzes_completed || 0) >= 1,
        progress: Math.min(data?.quizzes_completed || 0, 1),
        maxProgress: 1,
        category: 'quiz',
        rarity: 'common'
      },
      {
        id: 'quiz-enthusiast',
        title: 'Quiz Enthusiast',
        description: 'Complete 25 quizzes',
        icon: Target,
        earned: (data?.quizzes_completed || 0) >= 25,
        progress: Math.min(data?.quizzes_completed || 0, 25),
        maxProgress: 25,
        category: 'quiz',
        rarity: 'rare'
      },
      {
        id: 'high-scorer',
        title: 'High Scorer',
        description: 'Maintain an average score above 80%',
        icon: Star,
        earned: (data?.average_score || 0) >= 80,
        progress: Math.min(data?.average_score || 0, 80),
        maxProgress: 80,
        category: 'quiz',
        rarity: 'epic'
      },

      // Streak Achievements
      {
        id: 'consistent',
        title: 'Consistent',
        description: 'Study for 3 days in a row',
        icon: Zap,
        earned: (data?.streak_days || 0) >= 3,
        progress: Math.min(data?.streak_days || 0, 3),
        maxProgress: 3,
        category: 'streak',
        rarity: 'common'
      },
      {
        id: 'dedicated',
        title: 'Dedicated',
        description: 'Study for 7 days in a row',
        icon: Zap,
        earned: (data?.streak_days || 0) >= 7,
        progress: Math.min(data?.streak_days || 0, 7),
        maxProgress: 7,
        category: 'streak',
        rarity: 'rare'
      },
      {
        id: 'unstoppable',
        title: 'Unstoppable',
        description: 'Study for 30 days in a row',
        icon: Zap,
        earned: (data?.streak_days || 0) >= 30,
        progress: Math.min(data?.streak_days || 0, 30),
        maxProgress: 30,
        category: 'streak',
        rarity: 'legendary'
      },

      // Certification Milestones
      {
        id: 'cert-progress',
        title: 'Making Progress',
        description: 'Reach 50% progress in any certification',
        icon: Medal,
        earned: Object.values(certData).some(cert => cert.progress_percentage >= 50),
        category: 'milestone',
        rarity: 'rare'
      },
      {
        id: 'cert-ready',
        title: 'Certification Ready',
        description: 'Complete 100% progress in any certification',
        icon: Trophy,
        earned: Object.values(certData).some(cert => cert.progress_percentage >= 100),
        category: 'milestone',
        rarity: 'epic'
      }
    ]
  }

  const achievements = calculateAchievements()
  const earnedAchievements = achievements.filter(a => a.earned)
  const nextAchievements = achievements.filter(a => !a.earned).slice(0, 3)

  const getRarityColor = (rarity: Achievement['rarity']) => {
    switch (rarity) {
      case 'common': return 'text-gray-600 bg-gray-100'
      case 'rare': return 'text-blue-600 bg-blue-100'
      case 'epic': return 'text-purple-600 bg-purple-100'
      case 'legendary': return 'text-yellow-600 bg-yellow-100'
    }
  }

  const getCategoryIcon = (category: Achievement['category']) => {
    switch (category) {
      case 'study': return BookOpen
      case 'quiz': return Target
      case 'streak': return Zap
      case 'milestone': return Trophy
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Trophy className="h-5 w-5" />
          Achievements
          <span className="text-sm font-normal text-secondary-600">
            ({earnedAchievements.length}/{achievements.length})
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Recent Achievements */}
        {earnedAchievements.length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-secondary-700 mb-2">Recent Achievements</h4>
            <div className="space-y-2">
              {earnedAchievements.slice(-2).map((achievement) => {
                const Icon = achievement.icon
                return (
                  <div
                    key={achievement.id}
                    className={`flex items-center gap-3 p-2 rounded-lg ${getRarityColor(achievement.rarity)}`}
                  >
                    <div className="p-1.5 bg-white rounded-full">
                      <Icon className="h-4 w-4" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-sm">{achievement.title}</div>
                      <div className="text-xs opacity-80">{achievement.description}</div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* Progress Towards Next Achievements */}
        {nextAchievements.length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-secondary-700 mb-2">In Progress</h4>
            <div className="space-y-3">
              {nextAchievements.map((achievement) => {
                const Icon = achievement.icon
                const progress = achievement.progress || 0
                const maxProgress = achievement.maxProgress || 100
                const progressPercentage = (progress / maxProgress) * 100

                return (
                  <div key={achievement.id} className="space-y-2">
                    <div className="flex items-center gap-3">
                      <div className="p-1.5 bg-secondary-100 rounded-full">
                        <Icon className="h-4 w-4 text-secondary-600" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-sm text-secondary-900">
                          {achievement.title}
                        </div>
                        <div className="text-xs text-secondary-600">
                          {achievement.description}
                        </div>
                      </div>
                      <div className="text-xs text-secondary-500">
                        {achievement.maxProgress ? `${progress}/${maxProgress}` : ''}
                      </div>
                    </div>
                    
                    {achievement.maxProgress && (
                      <div className="ml-10">
                        <div className="h-1.5 bg-secondary-200 rounded-full">
                          <div
                            className="h-1.5 bg-primary-600 rounded-full transition-all duration-300"
                            style={{ width: `${Math.min(progressPercentage, 100)}%` }}
                          />
                        </div>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* Achievement Summary */}
        <div className="pt-3 border-t">
          <div className="grid grid-cols-2 gap-3 text-center">
            <div className="p-2 bg-primary-50 rounded">
              <div className="text-lg font-bold text-primary-900">
                {earnedAchievements.length}
              </div>
              <div className="text-xs text-primary-700">Earned</div>
            </div>
            <div className="p-2 bg-secondary-50 rounded">
              <div className="text-lg font-bold text-secondary-900">
                {Math.round((earnedAchievements.length / achievements.length) * 100)}%
              </div>
              <div className="text-xs text-secondary-700">Complete</div>
            </div>
          </div>
        </div>

        {earnedAchievements.length === 0 && (
          <div className="text-center py-6">
            <Trophy className="h-8 w-8 text-secondary-300 mx-auto mb-2" />
            <p className="text-sm text-secondary-600">No achievements yet</p>
            <p className="text-xs text-secondary-500 mt-1">
              Start studying to unlock your first achievement!
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}