'use client'

import { useState } from 'react'
import { ThumbsUp, ThumbsDown, Star, MessageSquare, Send } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'

interface RecommendationFeedbackProps {
  recommendationId: string
  onSubmitFeedback: (feedback: {
    recommendationId: string
    rating: number
    helpful: boolean
    comments?: string
    categories: string[]
  }) => void
  onClose?: () => void
}

const feedbackCategories = [
  { id: 'relevant', label: 'Relevant to my goals' },
  { id: 'difficulty', label: 'Appropriate difficulty' },
  { id: 'timing', label: 'Good timing' },
  { id: 'clear', label: 'Clear explanation' },
  { id: 'actionable', label: 'Actionable advice' },
  { id: 'personalized', label: 'Feels personalized' }
]

export function RecommendationFeedback({
  recommendationId,
  onSubmitFeedback,
  onClose
}: RecommendationFeedbackProps) {
  const [rating, setRating] = useState<number>(0)
  const [helpful, setHelpful] = useState<boolean | null>(null)
  const [comments, setComments] = useState('')
  const [selectedCategories, setSelectedCategories] = useState<string[]>([])
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleCategoryToggle = (categoryId: string) => {
    setSelectedCategories(prev => 
      prev.includes(categoryId)
        ? prev.filter(id => id !== categoryId)
        : [...prev, categoryId]
    )
  }

  const handleSubmit = async () => {
    if (helpful === null || rating === 0) return

    setIsSubmitting(true)
    try {
      await onSubmitFeedback({
        recommendationId,
        rating,
        helpful,
        comments: comments.trim() || undefined,
        categories: selectedCategories
      })
      onClose?.()
    } catch (error) {
      console.error('Failed to submit feedback:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  const canSubmit = helpful !== null && rating > 0

  return (
    <Card className="p-6 max-w-md mx-auto">
      <div className="space-y-6">
        <div className="text-center">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            How was this recommendation?
          </h3>
          <p className="text-sm text-gray-600">
            Your feedback helps us improve future recommendations
          </p>
        </div>

        {/* Helpful/Not Helpful */}
        <div className="space-y-3">
          <label className="text-sm font-medium text-gray-700">
            Was this recommendation helpful?
          </label>
          <div className="flex space-x-3">
            <Button
              variant={helpful === true ? "primary" : "outline"}
              onClick={() => setHelpful(true)}
              className="flex-1"
            >
              <ThumbsUp className="w-4 h-4 mr-2" />
              Yes, helpful
            </Button>
            <Button
              variant={helpful === false ? "primary" : "outline"}
              onClick={() => setHelpful(false)}
              className="flex-1"
            >
              <ThumbsDown className="w-4 h-4 mr-2" />
              Not helpful
            </Button>
          </div>
        </div>

        {/* Star Rating */}
        <div className="space-y-3">
          <label className="text-sm font-medium text-gray-700">
            Overall rating
          </label>
          <div className="flex space-x-1">
            {[1, 2, 3, 4, 5].map((star) => (
              <button
                key={star}
                onClick={() => setRating(star)}
                className="p-1 hover:scale-110 transition-transform"
              >
                <Star
                  className={`w-6 h-6 ${
                    star <= rating
                      ? 'text-yellow-400 fill-current'
                      : 'text-gray-300'
                  }`}
                />
              </button>
            ))}
          </div>
        </div>

        {/* Feedback Categories */}
        {helpful === true && (
          <div className="space-y-3">
            <label className="text-sm font-medium text-gray-700">
              What made it helpful? (Select all that apply)
            </label>
            <div className="grid grid-cols-2 gap-2">
              {feedbackCategories.map((category) => (
                <button
                  key={category.id}
                  onClick={() => handleCategoryToggle(category.id)}
                  className={`p-2 text-xs rounded border text-left transition-colors ${
                    selectedCategories.includes(category.id)
                      ? 'bg-blue-50 border-blue-200 text-blue-800'
                      : 'bg-gray-50 border-gray-200 text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  {category.label}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Comments */}
        <div className="space-y-3">
          <label className="text-sm font-medium text-gray-700">
            Additional comments (optional)
          </label>
          <div className="relative">
            <textarea
              value={comments}
              onChange={(e) => setComments(e.target.value)}
              placeholder="Tell us more about your experience..."
              className="w-full p-3 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows={3}
              maxLength={500}
            />
            <MessageSquare className="absolute top-3 right-3 w-4 h-4 text-gray-400" />
          </div>
          <div className="text-xs text-gray-500 text-right">
            {comments.length}/500 characters
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex space-x-3 pt-4">
          {onClose && (
            <Button
              variant="outline"
              onClick={onClose}
              className="flex-1"
              disabled={isSubmitting}
            >
              Cancel
            </Button>
          )}
          <Button
            onClick={handleSubmit}
            disabled={!canSubmit || isSubmitting}
            className="flex-1"
          >
            {isSubmitting ? (
              <div className="flex items-center space-x-2">
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                <span>Submitting...</span>
              </div>
            ) : (
              <div className="flex items-center space-x-2">
                <Send className="w-4 h-4" />
                <span>Submit Feedback</span>
              </div>
            )}
          </Button>
        </div>
      </div>
    </Card>
  )
}