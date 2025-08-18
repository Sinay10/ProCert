'use client'

import { ChatMessage } from '@/types/api'
import { SourceCitations } from './source-citations'
import { ModeIndicator } from './mode-indicator'

interface MessageBubbleProps {
  message: ChatMessage
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user'
  const timestamp = new Date(message.timestamp).toLocaleTimeString([], { 
    hour: '2-digit', 
    minute: '2-digit' 
  })

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-[80%] ${isUser ? 'order-2' : 'order-1'}`}>
        {/* Message bubble */}
        <div
          className={`px-4 py-3 rounded-lg ${
            isUser
              ? 'bg-primary-600 text-white'
              : 'bg-secondary-100 text-secondary-900'
          }`}
        >
          <div className="whitespace-pre-wrap break-words">
            {message.content}
          </div>
        </div>

        {/* Message metadata */}
        <div className={`mt-1 flex items-center gap-2 text-xs text-secondary-500 ${
          isUser ? 'justify-end' : 'justify-start'
        }`}>
          <span>{timestamp}</span>
          
          {!isUser && message.mode_used && (
            <ModeIndicator mode={message.mode_used} />
          )}
        </div>

        {/* Source citations for assistant messages */}
        {!isUser && message.sources && message.sources.length > 0 && (
          <div className="mt-2">
            <SourceCitations 
              sources={message.sources} 
              mode={message.mode_used}
            />
          </div>
        )}
      </div>

      {/* Avatar */}
      <div className={`flex-shrink-0 ${isUser ? 'order-1 mr-3' : 'order-2 ml-3'}`}>
        <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
          isUser 
            ? 'bg-primary-600 text-white' 
            : 'bg-secondary-600 text-white'
        }`}>
          {isUser ? 'U' : 'AI'}
        </div>
      </div>
    </div>
  )
}