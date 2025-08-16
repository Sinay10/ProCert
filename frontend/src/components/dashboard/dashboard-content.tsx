'use client'

import { useSession } from 'next-auth/react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { 
  MessageSquare, 
  Brain, 
  TrendingUp, 
  BookOpen, 
  Award,
  Clock,
  Target,
  Zap
} from 'lucide-react'
import Link from 'next/link'

const quickActions = [
  {
    title: 'Start AI Chat',
    description: 'Get instant help with your AWS questions',
    icon: MessageSquare,
    href: '/chat',
    color: 'bg-blue-500',
  },
  {
    title: 'Take a Quiz',
    description: 'Test your knowledge with practice questions',
    icon: Brain,
    href: '/quizzes',
    color: 'bg-green-500',
  },
  {
    title: 'View Progress',
    description: 'Check your learning analytics',
    icon: TrendingUp,
    href: '/progress',
    color: 'bg-purple-500',
  },
  {
    title: 'Study Path',
    description: 'Follow your personalized learning journey',
    icon: BookOpen,
    href: '/study-path',
    color: 'bg-orange-500',
  },
]

const stats = [
  {
    name: 'Study Streak',
    value: '7 days',
    icon: Zap,
    change: '+2 from last week',
    changeType: 'positive',
  },
  {
    name: 'Quiz Average',
    value: '85%',
    icon: Target,
    change: '+5% from last week',
    changeType: 'positive',
  },
  {
    name: 'Study Time',
    value: '12.5h',
    icon: Clock,
    change: 'This week',
    changeType: 'neutral',
  },
  {
    name: 'Certifications',
    value: '2 in progress',
    icon: Award,
    change: 'AWS SAA, AWS DVA',
    changeType: 'neutral',
  },
]

export function DashboardContent() {
  const { data: session } = useSession()

  return (
    <div className="space-y-6">
      {/* Welcome Section */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-secondary-900">
          Welcome back, {session?.user?.name || session?.user?.email?.split('@')[0] || 'Learner'}!
        </h1>
        <p className="text-secondary-600 mt-2">
          Ready to continue your AWS certification journey?
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat) => {
          const Icon = stat.icon
          return (
            <Card key={stat.name}>
              <CardContent className="p-6">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <Icon className="h-6 w-6 text-secondary-600" />
                  </div>
                  <div className="ml-4 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-secondary-500 truncate">
                        {stat.name}
                      </dt>
                      <dd className="text-lg font-semibold text-secondary-900">
                        {stat.value}
                      </dd>
                      <dd className="text-sm text-secondary-600">
                        {stat.change}
                      </dd>
                    </dl>
                  </div>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-lg font-semibold text-secondary-900 mb-4">
          Quick Actions
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {quickActions.map((action) => {
            const Icon = action.icon
            return (
              <Link key={action.title} href={action.href}>
                <Card className="hover:shadow-md transition-shadow cursor-pointer">
                  <CardHeader className="pb-3">
                    <div className={`w-10 h-10 ${action.color} rounded-lg flex items-center justify-center mb-3`}>
                      <Icon className="h-5 w-5 text-white" />
                    </div>
                    <CardTitle className="text-base">{action.title}</CardTitle>
                    <CardDescription className="text-sm">
                      {action.description}
                    </CardDescription>
                  </CardHeader>
                </Card>
              </Link>
            )
          })}
        </div>
      </div>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
            <CardDescription>Your latest learning activities</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center space-x-3">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-secondary-900">
                    Completed AWS SAA Quiz #5
                  </p>
                  <p className="text-xs text-secondary-500">Score: 92% • 2 hours ago</p>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-secondary-900">
                    Chat session about EC2 instances
                  </p>
                  <p className="text-xs text-secondary-500">5 hours ago</p>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-secondary-900">
                    Studied VPC networking concepts
                  </p>
                  <p className="text-xs text-secondary-500">Yesterday</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Recommendations</CardTitle>
            <CardDescription>Personalized study suggestions</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="p-3 bg-blue-50 rounded-lg">
                <p className="text-sm font-medium text-blue-900">
                  Focus on Lambda Functions
                </p>
                <p className="text-xs text-blue-700 mt-1">
                  Based on your recent quiz performance, spend more time on serverless concepts.
                </p>
                <Button size="sm" variant="outline" className="mt-2">
                  Start Learning
                </Button>
              </div>
              <div className="p-3 bg-green-50 rounded-lg">
                <p className="text-sm font-medium text-green-900">
                  Take Practice Exam
                </p>
                <p className="text-xs text-green-700 mt-1">
                  You're ready for a comprehensive practice test for AWS SAA.
                </p>
                <Button size="sm" variant="outline" className="mt-2">
                  Take Exam
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}