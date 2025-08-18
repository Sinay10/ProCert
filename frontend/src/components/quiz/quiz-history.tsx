'use client'

import { useState, useEffect } from 'react'
import { useSession } from 'next-auth/react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { apiClient, API_ENDPOINTS } from '@/lib/api-client'

interface QuizHistoryItem {
  quiz_id: string
  certification: string
  difficulty: string
  score: number
  questions_count: number
  completed_at: string
  time_taken?: number
}

interface QuizHistoryResponse {
  quizzes: QuizHistoryItem[]
  statistics: {
    total_quizzes: number
    average_score: number
    best_score: number
    total_questions_answered: number
    by_certification: Record<string, {
      count: number
      average_score: number
      best_score: number
    }>
  }
}

interface QuizHistoryProps {
  onStartNewQuiz: () => void
}

export function QuizHistory({ onStartNewQuiz }: QuizHistoryProps) {
  const { data: session } = useSession()
  const [history, setHistory] = useState<QuizHistoryResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (session?.userId) {
      fetchHistory()
    }
  }, [session?.userId])

  const fetchHistory = async () => {
    if (!session?.userId) return

    setLoading(true)
    setError(null)

    try {
      const data = await apiClient.get<QuizHistoryResponse>(
        API_ENDPOINTS.QUIZ_HISTORY(session.userId)
      )
      setHistory(data)
    } catch (err: any) {
      console.error('Failed to fetch quiz history:', err)
      setError('Failed to load quiz history. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-success-600'
    if (score >= 60) return 'text-warning-600'
    return 'text-error-600'
  }

  const getScoreBadgeColor = (score: number) => {
    if (score >= 80) return 'bg-success-100 text-success-800'
    if (score >= 60) return 'bg-warning-100 text-warning-800'
    return 'bg-error-100 text-error-800'
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <Card>
          <CardContent className="p-8 text-center">
            <div className="loading-spinner w-8 h-8 mx-auto mb-4" />
            <p className="text-secondary-600">Loading quiz history...</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <Card>
          <CardContent className="p-8 text-center">
            <p className="text-error-600 mb-4">{error}</p>
            <Button onClick={fetchHistory} variant="outline">
              Try Again
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (!history || history.quizzes.length === 0) {
    return (
      <div className="space-y-6">
        <Card>
          <CardContent className="p-8 text-center">
            <div className="mb-4">
              <svg className="w-16 h-16 mx-auto text-secondary-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-secondary-900 mb-2">No Quiz History</h3>
            <p className="text-secondary-600 mb-6">
              You haven't taken any quizzes yet. Start your first quiz to begin tracking your progress!
            </p>
            <Button onClick={onStartNewQuiz}>
              Take Your First Quiz
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Statistics Overview */}
      <Card>
        <CardHeader>
          <CardTitle>Performance Overview</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-primary-600">
                {history.statistics.total_quizzes}
              </div>
              <p className="text-sm text-secondary-600">Total Quizzes</p>
            </div>
            <div className="text-center">
              <div className={`text-2xl font-bold ${getScoreColor(history.statistics.average_score)}`}>
                {Math.round(history.statistics.average_score)}%
              </div>
              <p className="text-sm text-secondary-600">Average Score</p>
            </div>
            <div className="text-center">
              <div className={`text-2xl font-bold ${getScoreColor(history.statistics.best_score)}`}>
                {Math.round(history.statistics.best_score)}%
              </div>
              <p className="text-sm text-secondary-600">Best Score</p>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-secondary-700">
                {history.statistics.total_questions_answered}
              </div>
              <p className="text-sm text-secondary-600">Questions Answered</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Performance by Certification */}
      {Object.keys(history.statistics.by_certification).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Performance by Certification</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Object.entries(history.statistics.by_certification).map(([cert, stats]) => (
                <div key={cert} className="flex items-center justify-between p-4 bg-secondary-50 rounded-lg">
                  <div>
                    <h4 className="font-medium text-secondary-900 capitalize">
                      {cert.replace(/-/g, ' ')}
                    </h4>
                    <p className="text-sm text-secondary-600">
                      {stats.count} quiz{stats.count !== 1 ? 'es' : ''} completed
                    </p>
                  </div>
                  <div className="text-right">
                    <div className={`text-lg font-semibold ${getScoreColor(stats.average_score)}`}>
                      {Math.round(stats.average_score)}%
                    </div>
                    <p className="text-xs text-secondary-500">
                      Best: {Math.round(stats.best_score)}%
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recent Quiz History */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Quizzes</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {history.quizzes.map((quiz) => (
              <div
                key={quiz.quiz_id}
                className="flex items-center justify-between p-4 border border-secondary-200 rounded-lg hover:bg-secondary-50 transition-colors"
              >
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h4 className="font-medium text-secondary-900 capitalize">
                      {quiz.certification.replace(/-/g, ' ')}
                    </h4>
                    <span className={`
                      px-2 py-1 rounded text-xs font-medium
                      ${getScoreBadgeColor(quiz.score)}
                    `}>
                      {Math.round(quiz.score)}%
                    </span>
                  </div>
                  <div className="flex items-center gap-4 text-sm text-secondary-600">
                    <span>{quiz.questions_count} questions</span>
                    <span className="capitalize">{quiz.difficulty}</span>
                    <span>{formatDate(quiz.completed_at)}</span>
                    {quiz.time_taken && (
                      <span>{Math.round(quiz.time_taken / 60)} min</span>
                    )}
                  </div>
                </div>
                <div className="text-right">
                  <div className={`text-lg font-semibold ${getScoreColor(quiz.score)}`}>
                    {Math.round(quiz.score)}%
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}