import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient, API_ENDPOINTS } from '@/lib/api-client'
import type {
  ChatRequest,
  ChatResponse,
  QuizRequest,
  QuizResponse,
  QuizSubmission,
  QuizResult,
  RecommendationResponse,
  StudyPath,
  UserProgress,
  UserAnalytics,
  ProgressInteraction,
} from '@/types/api'

// Chat hooks
export function useSendMessage() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (data: ChatRequest) => 
      apiClient.post<ChatResponse>(API_ENDPOINTS.CHAT_MESSAGE, data),
    onSuccess: () => {
      // Invalidate conversation queries
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
    },
  })
}

export function useConversation(conversationId: string) {
  return useQuery({
    queryKey: ['conversation', conversationId],
    queryFn: () => apiClient.get(API_ENDPOINTS.CHAT_CONVERSATION(conversationId)),
    enabled: !!conversationId,
  })
}

// Quiz hooks
export function useGenerateQuiz() {
  return useMutation({
    mutationFn: (data: QuizRequest) => 
      apiClient.post<QuizResponse>(API_ENDPOINTS.QUIZ_GENERATE, data),
  })
}

export function useSubmitQuiz() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (data: QuizSubmission) => 
      apiClient.post<QuizResult>(API_ENDPOINTS.QUIZ_SUBMIT, data),
    onSuccess: (_, variables) => {
      // Invalidate quiz history and progress
      queryClient.invalidateQueries({ queryKey: ['quiz-history', variables.user_id] })
      queryClient.invalidateQueries({ queryKey: ['progress', variables.user_id] })
    },
  })
}

export function useQuizHistory(userId: string) {
  return useQuery({
    queryKey: ['quiz-history', userId],
    queryFn: () => apiClient.get(API_ENDPOINTS.QUIZ_HISTORY(userId)),
    enabled: !!userId,
  })
}

// Recommendation hooks
export function useRecommendations(userId: string, certification?: string) {
  return useQuery({
    queryKey: ['recommendations', userId, certification],
    queryFn: () => apiClient.get<RecommendationResponse>(
      API_ENDPOINTS.RECOMMENDATIONS(userId),
      { params: { certification } }
    ),
    enabled: !!userId,
  })
}

export function useStudyPath(userId: string, certification: string) {
  return useQuery({
    queryKey: ['study-path', userId, certification],
    queryFn: () => apiClient.get<StudyPath>(
      API_ENDPOINTS.STUDY_PATH(userId, certification)
    ),
    enabled: !!userId && !!certification,
  })
}

export function useRecommendationFeedback() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (data: { user_id: string; recommendation_id: string; action: string }) =>
      apiClient.post(API_ENDPOINTS.RECOMMENDATION_FEEDBACK, data),
    onSuccess: (_, variables) => {
      // Invalidate recommendations
      queryClient.invalidateQueries({ queryKey: ['recommendations', variables.user_id] })
    },
  })
}

// Progress hooks
export function useProgress(userId: string, certification?: string, timeframe?: string) {
  return useQuery({
    queryKey: ['progress', userId, certification, timeframe],
    queryFn: () => apiClient.get<UserProgress>(
      API_ENDPOINTS.PROGRESS(userId),
      { params: { certification, timeframe } }
    ),
    enabled: !!userId,
  })
}

export function useTrackInteraction() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (data: ProgressInteraction) =>
      apiClient.post(API_ENDPOINTS.PROGRESS_INTERACTION, data),
    onSuccess: (_, variables) => {
      // Invalidate progress queries
      queryClient.invalidateQueries({ queryKey: ['progress', variables.user_id] })
    },
  })
}

export function useAnalytics(userId: string) {
  return useQuery({
    queryKey: ['analytics', userId],
    queryFn: () => apiClient.get<UserAnalytics>(API_ENDPOINTS.ANALYTICS(userId)),
    enabled: !!userId,
  })
}

// Generic hooks for common patterns
export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value)

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value)
    }, delay)

    return () => {
      clearTimeout(handler)
    }
  }, [value, delay])

  return debouncedValue
}

import { useState, useEffect } from 'react'

export function useLocalStorage<T>(key: string, initialValue: T) {
  const [storedValue, setStoredValue] = useState<T>(() => {
    if (typeof window === 'undefined') {
      return initialValue
    }
    try {
      const item = window.localStorage.getItem(key)
      return item ? JSON.parse(item) : initialValue
    } catch (error) {
      console.error(`Error reading localStorage key "${key}":`, error)
      return initialValue
    }
  })

  const setValue = (value: T | ((val: T) => T)) => {
    try {
      const valueToStore = value instanceof Function ? value(storedValue) : value
      setStoredValue(valueToStore)
      if (typeof window !== 'undefined') {
        window.localStorage.setItem(key, JSON.stringify(valueToStore))
      }
    } catch (error) {
      console.error(`Error setting localStorage key "${key}":`, error)
    }
  }

  return [storedValue, setValue] as const
}