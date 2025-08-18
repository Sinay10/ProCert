'use client'

export function TypingIndicator() {
  return (
    <div className="flex justify-start">
      <div className="flex-shrink-0 mr-3">
        <div className="w-8 h-8 rounded-full bg-secondary-600 text-white flex items-center justify-center text-sm font-medium">
          AI
        </div>
      </div>
      
      <div className="max-w-[80%]">
        <div className="bg-secondary-100 text-secondary-900 px-4 py-3 rounded-lg">
          <div className="flex items-center space-x-1">
            <div className="flex space-x-1">
              <div className="w-2 h-2 bg-secondary-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
              <div className="w-2 h-2 bg-secondary-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
              <div className="w-2 h-2 bg-secondary-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
            <span className="text-sm text-secondary-600 ml-2">AI is typing...</span>
          </div>
        </div>
      </div>
    </div>
  )
}