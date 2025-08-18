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

describe('Chat Interface Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    
    // Mock authenticated session
    mockUseSession.mockReturnValue({
      data: {
        user: { id: '1', email: 'test@example.com' },
        accessToken: 'token'
      },
      status: 'authenticated',
      update: vi.fn()
    })
  })

  it('completes a full chat conversation flow', async () => {
    // Mock API responses
    const mockResponse = {
      response: 'AWS (Amazon Web Services) is a comprehensive cloud computing platform.',
      sources: ['AWS Documentation', 'AWS Getting Started Guide'],
      mode_used: 'rag',
      conversation_id: 'conv-123'
    }

    mockApiClient.post.mockResolvedValue(mockResponse)

    render(<ChatInterface />)
    
    // Verify initial state
    expect(screen.getByText('Start a conversation')).toBeInTheDocument()
    expect(screen.getByText('Curated Only')).toBeInTheDocument()
    expect(screen.getByDisplayValue('All Certifications')).toBeInTheDocument()
    
    // Send a message
    const input = screen.getByPlaceholderText(/Ask about/)
    const sendButton = screen.getByRole('button', { name: /send/i })
    
    fireEvent.change(input, { target: { value: 'What is AWS?' } })
    fireEvent.click(sendButton)
    
    // Verify user message appears
    expect(screen.getByText('What is AWS?')).toBeInTheDocument()
    
    // Wait for API response
    await waitFor(() => {
      expect(screen.getByText('AWS (Amazon Web Services) is a comprehensive cloud computing platform.')).toBeInTheDocument()
    })
    
    // Verify source citations appear
    expect(screen.getByText('Curated Study Materials:')).toBeInTheDocument()
    expect(screen.getByText('AWS Documentation')).toBeInTheDocument()
    expect(screen.getByText('AWS Getting Started Guide')).toBeInTheDocument()
    
    // Verify mode indicator
    expect(screen.getByText('Curated')).toBeInTheDocument()
    
    // Verify API was called correctly
    expect(mockApiClient.post).toHaveBeenCalledWith('/api/chat/message', {
      message: 'What is AWS?',
      mode: 'rag',
      conversation_id: undefined,
      certification: undefined
    })
  })

  it('switches to enhanced mode and shows different source types', async () => {
    const mockEnhancedResponse = {
      response: 'AWS offers over 200 services including compute, storage, and databases.',
      sources: ['AWS Documentation', 'Claude General Knowledge'],
      mode_used: 'enhanced',
      conversation_id: 'conv-124'
    }

    mockApiClient.post.mockResolvedValue(mockEnhancedResponse)

    render(<ChatInterface />)
    
    // Switch to enhanced mode
    const enhancedButton = screen.getByRole('button', { name: /enhanced/i })
    fireEvent.click(enhancedButton)
    
    expect(screen.getByText('Includes additional AWS knowledge when needed')).toBeInTheDocument()
    
    // Send a message
    const input = screen.getByPlaceholderText(/Ask about/)
    fireEvent.change(input, { target: { value: 'Tell me more about AWS services' } })
    fireEvent.click(screen.getByRole('button', { name: /send/i }))
    
    await waitFor(() => {
      expect(screen.getByText('AWS offers over 200 services including compute, storage, and databases.')).toBeInTheDocument()
    })
    
    // Verify both source types appear
    expect(screen.getByText('Curated Study Materials:')).toBeInTheDocument()
    expect(screen.getByText('Additional Context:')).toBeInTheDocument()
    expect(screen.getByText('Note: Prioritize curated materials for certification preparation')).toBeInTheDocument()
    
    // Verify enhanced mode indicator
    expect(screen.getByText('Enhanced')).toBeInTheDocument()
  })

  it('filters by certification and includes context in API call', async () => {
    const mockResponse = {
      response: 'For AWS Cloud Practitioner certification, focus on core services.',
      sources: ['AWS Cloud Practitioner Study Guide'],
      mode_used: 'rag',
      conversation_id: 'conv-125'
    }

    mockApiClient.post.mockResolvedValue(mockResponse)

    render(<ChatInterface />)
    
    // Select a certification
    const certificationSelect = screen.getByDisplayValue('All Certifications')
    fireEvent.change(certificationSelect, { target: { value: 'aws-cloud-practitioner' } })
    
    // Send a message
    const input = screen.getByPlaceholderText(/Ask about AWS Cloud Practitioner/)
    fireEvent.change(input, { target: { value: 'What should I study?' } })
    fireEvent.click(screen.getByRole('button', { name: /send/i }))
    
    await waitFor(() => {
      expect(mockApiClient.post).toHaveBeenCalledWith('/api/chat/message', {
        message: 'What should I study?',
        mode: 'rag',
        conversation_id: undefined,
        certification: 'aws-cloud-practitioner'
      })
    })
  })
})