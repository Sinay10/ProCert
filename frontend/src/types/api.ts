// Chat types
export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  sources?: string[]
  mode_used?: 'rag' | 'enhanced'
}

export interface ChatRequest {
  message: string
  certification?: string
  mode?: 'rag' | 'enhanced'
  conversation_id?: string
}

export interface ChatResponse {
  response: string
  sources: string[]
  mode_used: string
  conversation_id: string
}

export interface Conversation {
  conversation_id: string
  user_id: string
  messages: ChatMessage[]
  certification_context?: string
  created_at: string
}

// Quiz types
export interface QuizQuestion {
  question_id: string
  question_text: string
  options: string[]
  correct_answer: string
  user_answer?: string
  explanation: string
}

export interface QuizRequest {
  certification: string
  difficulty?: string
  count?: number
  user_id: string
}

export interface QuizResponse {
  quiz_id: string
  questions: QuizQuestion[]
  metadata: {
    certification: string
    difficulty: string
    estimated_time: number
  }
}

export interface QuizSubmission {
  quiz_id: string
  answers: string[]
  user_id: string
}

export interface QuizResult {
  score: number
  results: Array<{
    question_id: string
    correct: boolean
    user_answer: string
    correct_answer: string
  }>
  feedback: Array<{
    question_id: string
    explanation: string
    additional_resources?: string[]
  }>
}

// Recommendation types
export interface StudyRecommendation {
  recommendation_id: string
  type: 'content' | 'quiz' | 'review'
  priority: number
  content_id?: string
  reasoning: string
  estimated_time: number
  created_at: string
}

export interface RecommendationResponse {
  recommendations: StudyRecommendation[]
  reasoning: string[]
}

export interface StudyPath {
  path: Array<{
    topic: string
    status: 'completed' | 'current' | 'locked'
    estimated_time: number
    content_ids: string[]
  }>
  progress: {
    completed_topics: number
    total_topics: number
    estimated_completion: string
  }
  next_steps: string[]
}

// Progress types
export interface UserProgress {
  overall: {
    total_study_time: number
    quizzes_completed: number
    average_score: number
    streak_days: number
  }
  by_certification: Record<string, {
    progress_percentage: number
    topics_completed: number
    total_topics: number
    last_activity: string
  }>
  trends: Array<{
    date: string
    score: number
    study_time: number
  }>
}

export interface ProgressInteraction {
  user_id: string
  content_id: string
  interaction_type: 'view' | 'quiz' | 'chat' | 'bookmark'
  data: Record<string, any>
}

export interface UserAnalytics {
  performance: {
    strengths: string[]
    weaknesses: string[]
    improvement_rate: number
  }
  predictions: {
    certification_readiness: Record<string, number>
    estimated_study_time: Record<string, number>
  }
  recommendations: string[]
}

// Common types
export interface ApiError {
  code: string
  message: string
  details?: Record<string, any>
  timestamp: string
  request_id: string
}

export interface PaginatedResponse<T> {
  data: T[]
  pagination: {
    page: number
    limit: number
    total: number
    has_next: boolean
    has_prev: boolean
  }
}