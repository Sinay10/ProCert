'use client'

import { useState, useRef, useEffect } from 'react'
import { useSession } from 'next-auth/react'
import { ChatMessage, ChatRequest, ChatResponse, Conversation } from '@/types/api'
import { apiClient, API_ENDPOINTS } from '@/lib/api-client'
import { MessageList } from './message-list'
import { MessageInput } from './message-input'
import { ModeSelector } from './mode-selector'
import { ConversationManager } from './conversation-manager'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'

interface ChatInterfaceProps {
  className?: string
}

export function ChatInterface({ className }: ChatInterfaceProps) {
  const { data: session } = useSession()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isTyping, setIsTyping] = useState(false)
  const [currentMode, setCurrentMode] = useState<'rag' | 'enhanced'>('rag')
  const [selectedCertification, setSelectedCertification] = useState<string>('')
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [conversations, setConversations] = useState<Conversation[]>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    if (messagesEndRef.current && typeof messagesEndRef.current.scrollIntoView === 'function') {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = async (content: string) => {
    if (!content.trim() || isLoading) return

    const userMessage: ChatMessage = {
      role: 'user',
      content: content.trim(),
      timestamp: new Date().toISOString()
    }

    setMessages(prev => [...prev, userMessage])
    setIsLoading(true)
    setIsTyping(true)

    try {
      const request: ChatRequest = {
        message: content.trim(),
        mode: currentMode,
        conversation_id: conversationId || undefined,
        certification: selectedCertification || undefined
      }

      console.log('Sending chat request:', {
        endpoint: API_ENDPOINTS.CHAT_MESSAGE,
        request,
        session: session ? { user: session.user, hasToken: !!session.accessToken } : null
      })

      const response = await apiClient.post<ChatResponse>(
        API_ENDPOINTS.CHAT_MESSAGE,
        request
      )

      console.log('Chat response received:', response)

      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: response.response,
        timestamp: new Date().toISOString(),
        sources: response.sources,
        mode_used: response.mode_used as 'rag' | 'enhanced'
      }

      setMessages(prev => [...prev, assistantMessage])
      
      // Update conversation ID if this is a new conversation
      if (!conversationId && response.conversation_id) {
        setConversationId(response.conversation_id)
      }

    } catch (error: any) {
      console.error('Failed to send message:', error)
      console.error('Error details:', {
        status: error?.response?.status,
        statusText: error?.response?.statusText,
        data: error?.response?.data,
        message: error?.message,
        config: error?.config
      })
      
      let errorContent = 'Sorry, I encountered an error while processing your message. Please try again.'
      
      // Handle specific error cases
      if (error?.response?.status === 401) {
        errorContent = 'Authentication required. Please sign in to use the chat feature.'
      } else if (error?.response?.status === 403) {
        errorContent = 'Your session has expired. Please sign out and sign back in to continue.'
      } else if (error?.response?.status === 429) {
        errorContent = 'Rate limit exceeded. Please wait a moment before sending another message.'
      } else if (error?.response?.status >= 500) {
        errorContent = 'The AI service is temporarily unavailable. Please try again in a few moments.'
      } else if (error?.code === 'NETWORK_ERROR' || error?.message?.includes('Network Error')) {
        errorContent = 'Network connection error. Please check your internet connection and try again.'
      }
      
      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: errorContent,
        timestamp: new Date().toISOString()
      }
      
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
      setIsTyping(false)
    }
  }

  const handleNewConversation = () => {
    setMessages([])
    setConversationId(null)
  }

  const handleLoadConversation = async (conversation: Conversation) => {
    setMessages(conversation.messages)
    setConversationId(conversation.conversation_id)
    if (conversation.certification_context) {
      setSelectedCertification(conversation.certification_context)
    }
  }

  const handleDeleteConversation = async (conversationId: string) => {
    try {
      await apiClient.delete(API_ENDPOINTS.CHAT_CONVERSATION(conversationId))
      setConversations(prev => prev.filter(c => c.conversation_id !== conversationId))
      
      // If we're currently viewing this conversation, start a new one
      if (conversationId === conversationId) {
        handleNewConversation()
      }
    } catch (error) {
      console.error('Failed to delete conversation:', error)
    }
  }

  const certificationOptions = [
    { value: '', label: 'All Certifications' },
    { value: 'aws-cloud-practitioner', label: 'AWS Cloud Practitioner' },
    { value: 'aws-solutions-architect-associate', label: 'AWS Solutions Architect Associate' },
    { value: 'aws-developer-associate', label: 'AWS Developer Associate' },
    { value: 'aws-sysops-administrator-associate', label: 'AWS SysOps Administrator Associate' },
    { value: 'aws-solutions-architect-professional', label: 'AWS Solutions Architect Professional' },
    { value: 'aws-devops-engineer-professional', label: 'AWS DevOps Engineer Professional' },
    { value: 'aws-machine-learning-specialty', label: 'AWS Machine Learning Specialty' },
    { value: 'aws-security-specialty', label: 'AWS Security Specialty' },
    { value: 'aws-advanced-networking-specialty', label: 'AWS Advanced Networking Specialty' },
    { value: 'aws-ai-practitioner', label: 'AWS AI Practitioner' },
    { value: 'aws-machine-learning-engineer-associate', label: 'AWS Machine Learning Engineer Associate' },
    { value: 'aws-data-engineer-associate', label: 'AWS Data Engineer Associate' },
  ]

  if (!session) {
    return (
      <Card className="p-6 text-center">
        <div className="max-w-md mx-auto">
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
            Sign in to chat
          </h3>
          <p className="text-secondary-600 mb-4">
            Please sign in to access the AI chat assistant for personalized AWS certification help.
          </p>
          <div className="bg-blue-50 border border-blue-200 rounded-md p-3 text-sm">
            <p className="text-blue-800 font-medium mb-1">Demo Account Available:</p>
            <p className="text-blue-700">
              Email: <code className="bg-blue-100 px-1 rounded">demo@procert.com</code><br />
              Password: <code className="bg-blue-100 px-1 rounded">DemoPass123!</code>
            </p>
          </div>
        </div>
      </Card>
    )
  }

  return (
    <div className={`flex flex-col h-full ${className}`}>
      {/* Header with controls */}
      <div className="flex flex-col sm:flex-row gap-4 mb-4 p-4 bg-white rounded-lg shadow-sm border">
        <div className="flex-1">
          <label htmlFor="certification-select" className="block text-sm font-medium text-secondary-700 mb-1">
            Certification Focus
          </label>
          <select
            id="certification-select"
            value={selectedCertification}
            onChange={(e) => setSelectedCertification(e.target.value)}
            className="w-full px-3 py-2 border border-secondary-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          >
            {certificationOptions.map(option => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
        
        <div className="flex-1">
          <ModeSelector
            currentMode={currentMode}
            onModeChange={setCurrentMode}
          />
        </div>
        
        <div className="flex items-end">
          <Button
            onClick={handleNewConversation}
            variant="outline"
            className="whitespace-nowrap"
          >
            New Chat
          </Button>
        </div>
      </div>

      {/* Conversation Manager */}
      <div className="mb-4">
        <ConversationManager
          conversations={conversations}
          currentConversationId={conversationId}
          onLoadConversation={handleLoadConversation}
          onDeleteConversation={handleDeleteConversation}
          onConversationsChange={setConversations}
        />
      </div>

      {/* Chat Messages */}
      <div className="flex-1 bg-white rounded-lg shadow-sm border overflow-hidden flex flex-col">
        <div className="flex-1 overflow-y-auto">
          <MessageList
            messages={messages}
            isTyping={isTyping}
            className="h-full"
          />
          <div ref={messagesEndRef} />
        </div>
        
        {/* Message Input */}
        <div className="border-t p-4">
          <MessageInput
            onSendMessage={handleSendMessage}
            disabled={isLoading}
            placeholder={`Ask about ${selectedCertification || 'AWS certifications'}...`}
          />
        </div>
      </div>
    </div>
  )
}