'use client'

import { ChatMessage } from '@/types/api'
import { MessageBubble } from './message-bubble'
import { TypingIndicator } from './typing-indicator'

interface MessageListProps {
  messages: ChatMessage[]
  isTyping?: boolean
  className?: string
}

export function MessageList({ messages, isTyping = false, className }: MessageListProps) {
  if (messages.length === 0 && !isTyping) {
    return (
      <div className={`flex items-center justify-center h-full ${className}`}>
        <div className="text-center text-secondary-500 max-w-md">
          <div className="mb-4">
            <svg
              className="mx-auto h-12 w-12 text-secondary-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
              />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-secondary-900 mb-2">
            Start a conversation
          </h3>
          <p className="text-sm">
            Ask me anything about AWS certifications. I can help you with study materials, 
            practice questions, and personalized guidance.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className={`p-4 space-y-4 ${className}`}>
      {messages.map((message, index) => (
        <MessageBubble
          key={`${message.timestamp}-${index}`}
          message={message}
        />
      ))}
      
      {isTyping && <TypingIndicator />}
    </div>
  )
}