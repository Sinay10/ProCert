'use client'

import { Card, CardContent } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Trophy, Star, Target, Award } from 'lucide-react'

interface AchievementStatsProps {
  totalAchievements: number
  earnedAchievements: number
  totalPoints: number
}

export function AchievementStats({ 
  totalAchievements, 
  earnedAchievements, 
  totalPoints 
}: AchievementStatsProps) {
  const completionPercentage = totalAchievements > 0 
    ? Math.round((earnedAchievements / totalAchievements) * 100) 
    : 0

  const getCompletionLevel = (percentage: number) => {
    if (percentage >= 90) return { level: 'Master', color: 'text-yellow-600', icon: Trophy }
    if (percentage >= 70) return { level: 'Expert', color: 'text-purple-600', icon: Award }
    if (percentage >= 50) return { level: 'Advanced', color: 'text-blue-600', icon: Target }
    if (percentage >= 25) return { level: 'Intermediate', color: 'text-green-600', icon: Star }
    return { level: 'Beginner', color: 'text-gray-600', icon: Star }
  }

  const levelInfo = getCompletionLevel(completionPercentage)
  const LevelIcon = levelInfo.icon

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
      {/* Overall Progress */}
      <Card className="md:col-span-2">
        <CardContent className="pt-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-semibold text-secondary-900">Overall Progress</h3>
              <p className="text-sm text-secondary-600">
                {earnedAchievements} of {totalAchievements} achievements unlocked
              </p>
            </div>
            <div className={`flex items-center space-x-2 ${levelInfo.color}`}>
              <LevelIcon className="h-5 w-5" />
              <span className="font-medium">{levelInfo.level}</span>
            </div>
          </div>
          
          <div className="space-y-2">
            <div className="flex justify-between text-sm text-secondary-600">
              <span>Completion</span>
              <span>{completionPercentage}%</span>
            </div>
            <Progress value={completionPercentage} className="h-3" />
          </div>
        </CardContent>
      </Card>

      {/* Total Points */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-yellow-100 rounded-lg">
              <Star className="h-5 w-5 text-yellow-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-secondary-900">{totalPoints}</p>
              <p className="text-sm text-secondary-600">Total Points</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Achievements Earned */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <Trophy className="h-5 w-5 text-green-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-secondary-900">{earnedAchievements}</p>
              <p className="text-sm text-secondary-600">Earned</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}