import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { useSession } from 'next-auth/react'
import { ChatInterface } from '../chat-interface'
import { apiClient } from '@/lib/api-client'
import { vi } from 'vitest'

// Mock dependencies
vi.mock('next-auth/react')
vi.mock('@/lib/api-client')

const mockUseSession = vi.mocked(useSession)
const mockApiClient = vi.mocked(apiClient)

describe('ChatInterface', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows sign-in message when user is not authenticated', () => {
    mockUseSession.mockReturnValue({
      data: null,
      status: 'unauthenticated',
      update: vi.fn()
    })

    render(<ChatInterface />)
    
    expect(screen.getByText('Please sign in to use the chat interface.')).toBeInTheDocument()
  })

  it('renders chat interface when user is authenticated', () => {
    mockUseSession.mockReturnValue({
      data: {
        user: { id: '1', email: 'test@example.com' },
        accessToken: 'token'
      },
      status: 'authenticated',
      update: vi.fn()
    })

    render(<ChatInterface />)
    
    expect(screen.getByText('Certification Focus')).toBeInTheDocument()
    expect(screen.getByText('Response Mode')).toBeInTheDocument()
    expect(screen.getByText('New Chat')).toBeInTheDocument()
    expect(screen.getByText('Start a conversation')).toBeInTheDocument()
  })

  it('sends message and displays response', async () => {
    mockUseSession.mockReturnValue({
      data: {
        user: { id: '1', email: 'test@example.com' },
        accessToken: 'token'
      },
      status: 'authenticated',
      update: vi.fn()
    })

    const mockResponse = {
      response: 'This is a test response',
      sources: ['AWS Documentation'],
      mode_used: 'rag',
      conversation_id: 'conv-123'
    }

    mockApiClient.post.mockResolvedValue(mockResponse)

    render(<ChatInterface />)
    
    const input = screen.getByPlaceholderText(/Ask about/)
    const sendButton = screen.getByText('Send')
    
    fireEvent.change(input, { target: { value: 'What is AWS?' } })
    fireEvent.click(sendButton)
    
    // Check that user message appears
    expect(screen.getByText('What is AWS?')).toBeInTheDocument()
    
    // Wait for API response
    await waitFor(() => {
      expect(screen.getByText('This is a test response')).toBeInTheDocument()
    })
    
    expect(mockApiClient.post).toHaveBeenCalledWith('/api/chat/message', {
      message: 'What is AWS?',
      mode: 'rag',
      conversation_id: undefined,
      certification: undefined
    })
  })

  it('switches between RAG and enhanced modes', () => {
    mockUseSession.mockReturnValue({
      data: {
        user: { id: '1', email: 'test@example.com' },
        accessToken: 'token'
      },
      status: 'authenticated',
      update: vi.fn()
    })

    render(<ChatInterface />)
    
    const enhancedButton = screen.getByText('Enhanced')
    fireEvent.click(enhancedButton)
    
    expect(screen.getByText('Includes additional AWS knowledge when needed')).toBeInTheDocument()
  })

  it('filters by certification', () => {
    mockUseSession.mockReturnValue({
      data: {
        user: { id: '1', email: 'test@example.com' },
        accessToken: 'token'
      },
      status: 'authenticated',
      update: vi.fn()
    })

    render(<ChatInterface />)
    
    const certificationSelect = screen.getByDisplayValue('All Certifications')
    fireEvent.change(certificationSelect, { target: { value: 'aws-cloud-practitioner' } })
    
    expect(screen.getByDisplayValue('AWS Cloud Practitioner')).toBeInTheDocument()
  })

  it('starts new conversation', () => {
    mockUseSession.mockReturnValue({
      data: {
        user: { id: '1', email: 'test@example.com' },
        accessToken: 'token'
      },
      status: 'authenticated',
      update: vi.fn()
    })

    render(<ChatInterface />)
    
    const newChatButton = screen.getByText('New Chat')
    fireEvent.click(newChatButton)
    
    // Should clear any existing messages and show empty state
    expect(screen.getByText('Start a conversation')).toBeInTheDocument()
  })

  it('handles API errors gracefully', async () => {
    mockUseSession.mockReturnValue({
      data: {
        user: { id: '1', email: 'test@example.com' },
        accessToken: 'token'
      },
      status: 'authenticated',
      update: vi.fn()
    })

    mockApiClient.post.mockRejectedValue(new Error('API Error'))

    render(<ChatInterface />)
    
    const input = screen.getByPlaceholderText(/Ask about/)
    const sendButton = screen.getByText('Send')
    
    fireEvent.change(input, { target: { value: 'Test message' } })
    fireEvent.click(sendButton)
    
    await waitFor(() => {
      expect(screen.getByText(/Sorry, I encountered an error/)).toBeInTheDocument()
    })
  })

  it('disables input while loading', async () => {
    mockUseSession.mockReturnValue({
      data: {
        user: { id: '1', email: 'test@example.com' },
        accessToken: 'token'
      },
      status: 'authenticated',
      update: vi.fn()
    })

    // Mock a delayed response
    mockApiClient.post.mockImplementation(() => 
      new Promise(resolve => setTimeout(() => resolve({
        response: 'Response',
        sources: [],
        mode_used: 'rag',
        conversation_id: 'conv-123'
      }), 100))
    )

    render(<ChatInterface />)
    
    const input = screen.getByPlaceholderText(/Ask about/)
    const sendButton = screen.getByText('Send')
    
    fireEvent.change(input, { target: { value: 'Test message' } })
    fireEvent.click(sendButton)
    
    // Check that input is disabled during loading
    expect(input).toBeDisabled()
    expect(screen.getByText('Sending')).toBeInTheDocument()
  })
})