import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'AI Chat - ProCert Learning Platform',
  description: 'Chat with AI for personalized learning assistance',
}

export default function ChatPage() {
  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-secondary-900">AI Chat Assistant</h1>
        <p className="text-secondary-600 mt-2">
          Get personalized help with your AWS certification studies
        </p>
      </div>
      
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <p className="text-secondary-500 text-center">
          Chat interface will be implemented in task 8
        </p>
      </div>
    </div>
  )
}