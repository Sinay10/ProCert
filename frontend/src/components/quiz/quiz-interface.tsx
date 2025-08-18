'use client'

import { useState, useEffect } from 'react'
import { useSession } from 'next-auth/react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { QuizQuestion, QuizResponse, QuizResult } from '@/types/api'
import { apiClient, API_ENDPOINTS } from '@/lib/api-client'
import { QuizSettings } from './quiz-settings'
import { QuestionDisplay } from './question-display'
import { QuizResults } from './quiz-results'
import { QuizHistory } from './quiz-history'

interface QuizInterfaceProps {
  initialCertification?: string
}

type QuizState = 'settings' | 'active' | 'results' | 'history'

export function QuizInterface({ initialCertification }: QuizInterfaceProps) {
  const { data: session } = useSession()
  const [state, setState] = useState<QuizState>('settings')
  const [currentQuiz, setCurrentQuiz] = useState<QuizResponse | null>(null)
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [userAnswers, setUserAnswers] = useState<string[]>([])
  const [quizResult, setQuizResult] = useState<QuizResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleStartQuiz = async (settings: {
    certification: string
    difficulty: string
    count: number
  }) => {
    if (!session?.userId) {
      setError('Please sign in to take quizzes')
      return
    }

    setLoading(true)
    setError(null)

    try {
      // Map frontend certification to backend code
      const getCertificationCode = (frontendValue: string): string => {
        const certMap: Record<string, string> = {
          'aws-advanced-networking-specialty': 'ANS',
          'aws-cloud-practitioner': 'CLF',
          'aws-solutions-architect-associate': 'SAA',
          'aws-developer-associate': 'DVA',
          'aws-sysops-administrator-associate': 'SOA',
          'aws-solutions-architect-professional': 'SAP',
          'aws-devops-engineer-professional': 'DOP'
        }
        return certMap[frontendValue] || 'SAA'
      }

      const quiz = await apiClient.post<QuizResponse>(API_ENDPOINTS.QUIZ_GENERATE, {
        certification_type: getCertificationCode(settings.certification),
        difficulty: settings.difficulty,
        count: settings.count
      })

      setCurrentQuiz(quiz)
      setUserAnswers(new Array(quiz.questions.length).fill(''))
      setCurrentQuestionIndex(0)
      setState('active')
    } catch (err: any) {
      console.error('Failed to generate quiz:', err)
      setError(err.response?.data?.message || 'Failed to generate quiz. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleAnswerSelect = (answer: string) => {
    const newAnswers = [...userAnswers]
    newAnswers[currentQuestionIndex] = answer
    setUserAnswers(newAnswers)
  }

  const handleNextQuestion = () => {
    if (currentQuiz && currentQuestionIndex < currentQuiz.questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1)
    }
  }

  const handlePreviousQuestion = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(currentQuestionIndex - 1)
    }
  }

  const handleSubmitQuiz = async () => {
    if (!currentQuiz || !session?.userId) return

    setLoading(true)
    setError(null)

    try {
      // Format answers for backend
      const formattedAnswers = currentQuiz.questions.map((question, index) => ({
        question_id: question.question_id,
        selected_answer: userAnswers[index] || ""
      }))

      const result = await apiClient.post<QuizResult>(API_ENDPOINTS.QUIZ_SUBMIT, {
        quiz_id: currentQuiz.quiz_id,
        answers: formattedAnswers
      })

      setQuizResult(result)
      setState('results')
    } catch (err: any) {
      console.error('Failed to submit quiz:', err)
      setError(err.response?.data?.message || 'Failed to submit quiz. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleReturnToSettings = () => {
    setState('settings')
    setCurrentQuiz(null)
    setCurrentQuestionIndex(0)
    setUserAnswers([])
    setQuizResult(null)
    setError(null)
  }

  const handleViewHistory = () => {
    setState('history')
  }

  const currentQuestion = currentQuiz?.questions[currentQuestionIndex]
  const isLastQuestion = currentQuiz && currentQuestionIndex === currentQuiz.questions.length - 1
  const canProceed = userAnswers[currentQuestionIndex] !== ''

  if (state === 'history') {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-secondary-900">Quiz History</h1>
            <p className="text-secondary-600 mt-2">
              Review your past quiz performance
            </p>
          </div>
          <Button onClick={handleReturnToSettings} variant="outline">
            New Quiz
          </Button>
        </div>
        <QuizHistory onStartNewQuiz={handleReturnToSettings} />
      </div>
    )
  }

  if (state === 'results' && quizResult && currentQuiz) {
    return (
      <div className="max-w-4xl mx-auto">
        <QuizResults
          result={quizResult}
          quiz={currentQuiz}
          userAnswers={userAnswers}
          onRetakeQuiz={handleReturnToSettings}
          onViewHistory={handleViewHistory}
        />
      </div>
    )
  }

  if (state === 'active' && currentQuiz && currentQuestion) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-2xl font-bold text-secondary-900">
                {currentQuiz.metadata.certification_type} Quiz
              </h1>
              <p className="text-secondary-600">
                Question {currentQuestionIndex + 1} of {currentQuiz.questions.length}
              </p>
            </div>
            <Button onClick={handleReturnToSettings} variant="outline" size="sm">
              Exit Quiz
            </Button>
          </div>

          {/* Progress bar */}
          <div className="w-full bg-secondary-200 rounded-full h-2 mb-6">
            <div
              className="bg-primary-600 h-2 rounded-full transition-all duration-300"
              style={{
                width: `${((currentQuestionIndex + 1) / currentQuiz.questions.length) * 100}%`
              }}
            />
          </div>
        </div>

        <QuestionDisplay
          question={currentQuestion}
          selectedAnswer={userAnswers[currentQuestionIndex]}
          onAnswerSelect={handleAnswerSelect}
          questionNumber={currentQuestionIndex + 1}
          totalQuestions={currentQuiz.questions.length}
        />

        <div className="mt-8 flex justify-between">
          <Button
            onClick={handlePreviousQuestion}
            disabled={currentQuestionIndex === 0}
            variant="outline"
          >
            Previous
          </Button>

          <div className="flex gap-3">
            {isLastQuestion ? (
              <Button
                onClick={handleSubmitQuiz}
                disabled={!canProceed || loading}
                loading={loading}
              >
                Submit Quiz
              </Button>
            ) : (
              <Button
                onClick={handleNextQuestion}
                disabled={!canProceed}
              >
                Next Question
              </Button>
            )}
          </div>
        </div>

        {error && (
          <div className="mt-4 p-4 bg-error-50 border border-error-200 rounded-md">
            <p className="text-error-700">{error}</p>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-secondary-900">Practice Quizzes</h1>
          <p className="text-secondary-600 mt-2">
            Test your knowledge with adaptive practice questions
          </p>
        </div>
        <Button onClick={handleViewHistory} variant="outline">
          View History
        </Button>
      </div>

      <QuizSettings
        onStartQuiz={handleStartQuiz}
        loading={loading}
        error={error}
        initialCertification={initialCertification}
      />
    </div>
  )
}