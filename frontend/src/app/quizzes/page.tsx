import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Practice Quizzes - ProCert Learning Platform',
  description: 'Test your knowledge with adaptive practice quizzes',
}

export default function QuizzesPage() {
  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-secondary-900">Practice Quizzes</h1>
        <p className="text-secondary-600 mt-2">
          Test your knowledge with adaptive practice questions
        </p>
      </div>
      
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <p className="text-secondary-500 text-center">
          Quiz interface will be implemented in task 9
        </p>
      </div>
    </div>
  )
}