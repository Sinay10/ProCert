'use client'

import { useState, useEffect } from 'react'
import { useSession } from 'next-auth/react'
import { Conversation } from '@/types/api'
import { apiClient, API_ENDPOINTS } from '@/lib/api-client'
import { Button } from '@/components/ui/button'

interface ConversationManagerProps {
  conversations: Conversation[]
  currentConversationId: string | null
  onLoadConversation: (conversation: Conversation) => void
  onDeleteConversation: (conversationId: string) => void
  onConversationsChange: (conversations: Conversation[]) => void
}

export function ConversationManager({
  conversations,
  currentConversationId,
  onLoadConversation,
  onDeleteConversation,
  onConversationsChange
}: ConversationManagerProps) {
  const { data: session } = useSession()
  const [isExpanded, setIsExpanded] = useState(false)
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    if (session?.user) {
      loadConversations()
    }
  }, [session])

  const loadConversations = async () => {
    if (!session?.user) return
    
    setIsLoading(true)
    try {
      // Note: This endpoint would need to be implemented to list user conversations
      // For now, we'll use a placeholder implementation
      const userConversations: Conversation[] = []
      onConversationsChange(userConversations)
    } catch (error) {
      console.error('Failed to load conversations:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const formatConversationTitle = (conversation: Conversation): string => {
    if (conversation.messages.length === 0) return 'Empty conversation'
    
    const firstUserMessage = conversation.messages.find(m => m.role === 'user')
    if (!firstUserMessage) return 'New conversation'
    
    // Truncate long messages
    const title = firstUserMessage.content.slice(0, 50)
    return title.length < firstUserMessage.content.length ? `${title}...` : title
  }

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString)
    const now = new Date()
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60)
    
    if (diffInHours < 24) {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    } else if (diffInHours < 24 * 7) {
      return date.toLocaleDateString([], { weekday: 'short' })
    } else {
      return date.toLocaleDateString([], { month: 'short', day: 'numeric' })
    }
  }

  if (!session?.user) return null

  return (
    <div className="bg-white rounded-lg shadow-sm border">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-secondary-50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <svg className="w-5 h-5 text-secondary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
          <span className="font-medium text-secondary-900">
            Recent Conversations ({conversations.length})
          </span>
        </div>
        
        <svg 
          className={`w-5 h-5 text-secondary-400 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
          fill="none" 
          viewBox="0 0 24 24" 
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isExpanded && (
        <div className="border-t">
          {isLoading ? (
            <div className="p-4 text-center text-secondary-500">
              <div className="inline-flex items-center gap-2">
                <div className="w-4 h-4 border-2 border-secondary-300 border-t-secondary-600 rounded-full animate-spin" />
                Loading conversations...
              </div>
            </div>
          ) : conversations.length === 0 ? (
            <div className="p-4 text-center text-secondary-500">
              No previous conversations found
            </div>
          ) : (
            <div className="max-h-64 overflow-y-auto">
              {conversations.map((conversation) => (
                <div
                  key={conversation.conversation_id}
                  className={`flex items-center gap-3 p-3 hover:bg-secondary-50 transition-colors ${
                    currentConversationId === conversation.conversation_id ? 'bg-blue-50 border-l-4 border-blue-600' : ''
                  }`}
                >
                  <button
                    onClick={() => onLoadConversation(conversation)}
                    className="flex-1 text-left min-w-0"
                  >
                    <div className="font-medium text-secondary-900 truncate">
                      {formatConversationTitle(conversation)}
                    </div>
                    <div className="text-sm text-secondary-500 flex items-center gap-2">
                      <span>{formatDate(conversation.created_at)}</span>
                      {conversation.certification_context && (
                        <>
                          <span>•</span>
                          <span className="truncate">{conversation.certification_context}</span>
                        </>
                      )}
                    </div>
                  </button>
                  
                  <Button
                    onClick={() => onDeleteConversation(conversation.conversation_id)}
                    variant="outline"
                    size="sm"
                    className="text-red-600 hover:text-red-700 hover:bg-red-50 border-red-200"
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </Button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}