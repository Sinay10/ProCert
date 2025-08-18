import { Metadata } from 'next'
import { QuizInterface } from '@/components/quiz'

export const metadata: Metadata = {
  title: 'Practice Quizzes - ProCert Learning Platform',
  description: 'Test your knowledge with adaptive practice quizzes',
}

export default function QuizzesPage() {
  return <QuizInterface />
}