import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Study Path - ProCert Learning Platform',
  description: 'Follow your personalized study path',
}

export default function StudyPathPage() {
  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-secondary-900">Study Path</h1>
        <p className="text-secondary-600 mt-2">
          Follow your personalized learning journey
        </p>
      </div>
      
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <p className="text-secondary-500 text-center">
          Study path interface will be implemented in task 11
        </p>
      </div>
    </div>
  )
}