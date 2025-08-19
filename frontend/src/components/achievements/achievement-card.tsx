'use client'

import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Achievement } from './achievements-page'
import { CheckCircle, Circle } from 'lucide-react'

interface AchievementCardProps {
  achievement: Achievement
}

export function AchievementCard({ achievement }: AchievementCardProps) {
  const Icon = achievement.icon

  const getRarityColor = (rarity: Achievement['rarity']) => {
    switch (rarity) {
      case 'common':
        return 'bg-gray-100 text-gray-800 border-gray-200'
      case 'rare':
        return 'bg-blue-100 text-blue-800 border-blue-200'
      case 'epic':
        return 'bg-purple-100 text-purple-800 border-purple-200'
      case 'legendary':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  const getRarityGlow = (rarity: Achievement['rarity']) => {
    if (!achievement.earned) return ''
    
    switch (rarity) {
      case 'rare':
        return 'shadow-blue-200 shadow-lg'
      case 'epic':
        return 'shadow-purple-200 shadow-lg'
      case 'legendary':
        return 'shadow-yellow-200 shadow-xl'
      default:
        return ''
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    })
  }

  return (
    <Card 
      className={`
        transition-all duration-200 hover:shadow-md
        ${achievement.earned ? 'border-primary-200 bg-primary-50/30' : 'border-secondary-200'}
        ${getRarityGlow(achievement.rarity)}
      `}
    >
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center space-x-3">
            <div 
              className={`
                p-2 rounded-lg transition-colors
                ${achievement.earned 
                  ? 'bg-primary-100 text-primary-600' 
                  : 'bg-secondary-100 text-secondary-400'
                }
              `}
            >
              <Icon className="h-5 w-5" />
            </div>
            <div className="flex-1">
              <div className="flex items-center space-x-2 mb-1">
                <Badge 
                  className={getRarityColor(achievement.rarity)}
                  variant="secondary"
                >
                  {achievement.rarity}
                </Badge>
                <Badge variant="outline" className="text-xs">
                  {achievement.points} pts
                </Badge>
              </div>
            </div>
          </div>
          
          <div className="flex-shrink-0">
            {achievement.earned ? (
              <CheckCircle className="h-5 w-5 text-green-600" />
            ) : (
              <Circle className="h-5 w-5 text-secondary-300" />
            )}
          </div>
        </div>
        
        <div>
          <h3 className={`
            font-semibold text-lg leading-tight
            ${achievement.earned ? 'text-secondary-900' : 'text-secondary-600'}
          `}>
            {achievement.title}
          </h3>
          <p className={`
            text-sm mt-1
            ${achievement.earned ? 'text-secondary-700' : 'text-secondary-500'}
          `}>
            {achievement.description}
          </p>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-3">
        {/* Progress Bar (for unearned achievements) */}
        {!achievement.earned && achievement.progress !== undefined && achievement.maxProgress && (
          <div className="space-y-2">
            <div className="flex justify-between text-xs text-secondary-600">
              <span>Progress</span>
              <span>{achievement.progress}/{achievement.maxProgress}</span>
            </div>
            <Progress 
              value={(achievement.progress / achievement.maxProgress) * 100} 
              className="h-2"
            />
          </div>
        )}
        
        {/* Requirement */}
        <div className="text-xs text-secondary-600">
          <span className="font-medium">Requirement:</span> {achievement.requirement}
        </div>
        
        {/* Earned Date */}
        {achievement.earned && achievement.earnedAt && (
          <div className="text-xs text-green-600 font-medium">
            Earned on {formatDate(achievement.earnedAt)}
          </div>
        )}
        
        {/* Category Badge */}
        <div className="flex justify-between items-center">
          <Badge variant="outline" className="text-xs capitalize">
            {achievement.category}
          </Badge>
          
          {achievement.earned && (
            <div className="text-xs text-primary-600 font-medium">
              ✨ Completed
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}