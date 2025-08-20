'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { QuizResult, QuizResponse } from '@/types/api'

interface QuizResultsProps {
  result: QuizResult
  quiz: QuizResponse
  userAnswers: string[]
  onRetakeQuiz: () => void
  onViewHistory: () => void
}

export function QuizResults({ result, quiz, userAnswers, onRetakeQuiz, onViewHistory }: QuizResultsProps) {
  const scorePercentage = Math.round(result.percentage)
  const correctCount = result.correct_answers
  const totalQuestions = result.total_questions

  // Helper function to get full answer text from letter
  const getAnswerText = (answerLetter: string, options: string[]) => {
    if (!answerLetter || !options) return answerLetter
    const answerIndex = answerLetter.charCodeAt(0) - 65 // Convert A,B,C,D to 0,1,2,3
    if (answerIndex >= 0 && answerIndex < options.length) {
      const optionText = options[answerIndex]
      // Remove the letter prefix if it exists (e.g., "A) Text" -> "Text")
      return optionText.replace(/^[A-D]\)\s*/, '')
    }
    return answerLetter
  }

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-success-600'
    if (score >= 60) return 'text-warning-600'
    return 'text-error-600'
  }

  const getScoreBgColor = (score: number) => {
    if (score >= 80) return 'bg-success-50 border-success-200'
    if (score >= 60) return 'bg-warning-50 border-warning-200'
    return 'bg-error-50 border-error-200'
  }

  const getPerformanceMessage = (score: number) => {
    if (score >= 90) return 'Excellent work! You have a strong understanding of this topic.'
    if (score >= 80) return 'Great job! You\'re well-prepared in this area.'
    if (score >= 70) return 'Good performance! A bit more study will help you excel.'
    if (score >= 60) return 'Fair performance. Focus on the areas you missed.'
    return 'Keep studying! Review the explanations and try again.'
  }

  return (
    <div className="space-y-6">
      {/* Overall Results */}
      <Card className={`${getScoreBgColor(scorePercentage)} border-2`}>
        <CardHeader className="text-center">
          <CardTitle className="text-2xl">Quiz Complete!</CardTitle>
        </CardHeader>
        <CardContent className="text-center space-y-4">
          <div className="space-y-2">
            <div className={`text-6xl font-bold ${getScoreColor(scorePercentage)}`}>
              {scorePercentage}%
            </div>
            <p className="text-lg text-secondary-700">
              {correctCount} out of {totalQuestions} correct
            </p>
          </div>
          
          <div className="max-w-md mx-auto">
            <p className="text-secondary-600">
              {getPerformanceMessage(scorePercentage)}
            </p>
          </div>

          <div className="flex justify-center gap-4 pt-4">
            <Button onClick={onRetakeQuiz} variant="primary">
              Take Another Quiz
            </Button>
            <Button onClick={onViewHistory} variant="outline">
              View History
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Quiz Metadata */}
      <Card>
        <CardHeader>
          <CardTitle>Quiz Details</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div>
              <span className="font-medium text-secondary-700">Certification:</span>
              <p className="text-secondary-900">{quiz.metadata.certification_type}</p>
            </div>
            <div>
              <span className="font-medium text-secondary-700">Difficulty:</span>
              <p className="text-secondary-900 capitalize">{quiz.metadata.difficulty}</p>
            </div>
            <div>
              <span className="font-medium text-secondary-700">Questions:</span>
              <p className="text-secondary-900">{totalQuestions}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Question-by-Question Results */}
      <Card>
        <CardHeader>
          <CardTitle>Question Review</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {result.results.map((questionResult, index) => {
              const userAnswer = questionResult.user_answer
              const isCorrect = questionResult.is_correct
              const userAnswerText = getAnswerText(userAnswer, questionResult.options)
              const correctAnswerText = getAnswerText(questionResult.correct_answer, questionResult.options)

              return (
                <div
                  key={questionResult.question_id}
                  className={`
                    border rounded-lg p-4
                    ${isCorrect ? 'border-success-200 bg-success-50' : 'border-error-200 bg-error-50'}
                  `}
                >
                  <div className="space-y-4">
                    {/* Question Header */}
                    <div className="flex items-start justify-between">
                      <h4 className="font-medium text-secondary-900">
                        Question {index + 1}
                      </h4>
                      <div className={`
                        px-2 py-1 rounded text-xs font-medium
                        ${isCorrect 
                          ? 'bg-success-100 text-success-800' 
                          : 'bg-error-100 text-error-800'
                        }
                      `}>
                        {isCorrect ? 'Correct' : 'Incorrect'}
                      </div>
                    </div>

                    {/* Question Text */}
                    <p className="text-secondary-700 text-sm leading-relaxed">
                      {questionResult.question_text}
                    </p>

                    {/* Answers */}
                    <div className="space-y-3 text-sm">
                      <div>
                        <span className="font-medium text-secondary-700">Your answer: </span>
                        <span className={`font-medium ${isCorrect ? 'text-success-700' : 'text-error-700'}`}>
                          {userAnswer}: {userAnswerText}
                        </span>
                      </div>
                      
                      <div>
                        <span className="font-medium text-secondary-700">Correct answer: </span>
                        <span className="font-medium text-success-700">
                          {questionResult.correct_answer}: {correctAnswerText}
                        </span>
                      </div>
                    </div>

                    {/* Explanation */}
                    {questionResult.explanation && (
                      <div className="bg-white border border-secondary-200 rounded p-3">
                        <h5 className="font-medium text-secondary-900 mb-2">Explanation:</h5>
                        <p className="text-secondary-700 text-sm leading-relaxed">
                          {questionResult.explanation}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}