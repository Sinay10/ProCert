'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { QuizQuestion } from '@/types/api'

interface QuestionDisplayProps {
  question: QuizQuestion
  selectedAnswer: string
  onAnswerSelect: (answer: string) => void
  questionNumber: number
  totalQuestions: number
}

export function QuestionDisplay({
  question,
  selectedAnswer,
  onAnswerSelect,
  questionNumber,
  totalQuestions
}: QuestionDisplayProps) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">
            Question {questionNumber}
          </CardTitle>
          <span className="text-sm text-secondary-500">
            {questionNumber} of {totalQuestions}
          </span>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {/* Question Text */}
          <div className="prose prose-sm max-w-none">
            <p className="text-secondary-900 text-base leading-relaxed">
              {question.question_text}
            </p>
          </div>

          {/* Answer Options */}
          <div className="space-y-3">
            {question.options.map((option, index) => {
              const optionLetter = String.fromCharCode(65 + index) // A, B, C, D
              const isSelected = selectedAnswer === optionLetter
              
              return (
                <label
                  key={index}
                  className={`
                    relative flex cursor-pointer rounded-lg border p-4 focus:outline-none transition-all
                    ${isSelected
                      ? 'border-primary-600 bg-primary-50 ring-2 ring-primary-600'
                      : 'border-secondary-300 bg-white hover:bg-secondary-50 hover:border-secondary-400'
                    }
                  `}
                >
                  <input
                    type="radio"
                    name={`question-${question.question_id}`}
                    value={optionLetter}
                    checked={isSelected}
                    onChange={(e) => onAnswerSelect(e.target.value)}
                    className="sr-only"
                  />
                  
                  <div className="flex items-start w-full">
                    {/* Option Letter */}
                    <div className={`
                      flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium mr-4
                      ${isSelected
                        ? 'bg-primary-600 text-white'
                        : 'bg-secondary-100 text-secondary-600'
                      }
                    `}>
                      {optionLetter}
                    </div>
                    
                    {/* Option Text */}
                    <div className="flex-1">
                      <span className="block text-sm text-secondary-900 leading-relaxed">
                        {option}
                      </span>
                    </div>
                    
                    {/* Selection Indicator */}
                    {isSelected && (
                      <div className="flex-shrink-0 ml-4">
                        <div className="w-5 h-5 rounded-full bg-primary-600 flex items-center justify-center">
                          <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                          </svg>
                        </div>
                      </div>
                    )}
                  </div>
                </label>
              )
            })}
          </div>

          {/* Helper Text */}
          <div className="text-sm text-secondary-500 bg-secondary-50 p-3 rounded-md">
            <p>Select the best answer from the options above. You can change your selection before moving to the next question.</p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}