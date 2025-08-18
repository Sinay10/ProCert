import { Metadata } from 'next'
import { ChatInterface } from '@/components/chat/chat-interface'

export const metadata: Metadata = {
  title: 'AI Chat - ProCert Learning Platform',
  description: 'Chat with AI for personalized learning assistance',
}

export default function ChatPage() {
  return (
    <div className="max-w-6xl mx-auto h-full">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-secondary-900">AI Chat Assistant</h1>
        <p className="text-secondary-600 mt-2">
          Get personalized help with your AWS certification studies. Choose between curated study materials or enhanced responses with additional context.
        </p>
      </div>
      

      
      <div className="h-[calc(100vh-400px)]">
        <ChatInterface className="h-full" />
      </div>
    </div>
  )
}