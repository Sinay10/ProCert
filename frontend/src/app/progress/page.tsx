import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Progress - ProCert Learning Platform',
  description: 'Track your learning progress and performance',
}

export default function ProgressPage() {
  return (
    <div className="max-w-6xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-secondary-900">Learning Progress</h1>
        <p className="text-secondary-600 mt-2">
          Track your performance and study analytics
        </p>
      </div>
      
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <p className="text-secondary-500 text-center">
          Progress dashboard will be implemented in task 10
        </p>
      </div>
    </div>
  )
}