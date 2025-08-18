import { render, screen } from '@testing-library/react'
import { MessageBubble } from '../message-bubble'
import { ChatMessage } from '@/types/api'

describe('MessageBubble', () => {
  const mockUserMessage: ChatMessage = {
    role: 'user',
    content: 'Hello, how are you?',
    timestamp: '2025-01-01T12:00:00Z'
  }

  const mockAssistantMessage: ChatMessage = {
    role: 'assistant',
    content: 'I am doing well, thank you!',
    timestamp: '2025-01-01T12:01:00Z',
    sources: ['AWS Documentation', 'Study Guide'],
    mode_used: 'rag'
  }

  it('renders user message correctly', () => {
    render(<MessageBubble message={mockUserMessage} />)
    
    expect(screen.getByText('Hello, how are you?')).toBeInTheDocument()
    expect(screen.getByText('U')).toBeInTheDocument() // User avatar
    expect(screen.getByText(/\d{1,2}:\d{2} [AP]M/)).toBeInTheDocument() // Timestamp
  })

  it('renders assistant message correctly', () => {
    render(<MessageBubble message={mockAssistantMessage} />)
    
    expect(screen.getByText('I am doing well, thank you!')).toBeInTheDocument()
    expect(screen.getByText('AI')).toBeInTheDocument() // AI avatar
    expect(screen.getByText(/\d{1,2}:\d{2} [AP]M/)).toBeInTheDocument() // Timestamp
  })

  it('displays mode indicator for assistant messages', () => {
    render(<MessageBubble message={mockAssistantMessage} />)
    
    expect(screen.getByText('Curated')).toBeInTheDocument()
  })

  it('displays source citations for assistant messages', () => {
    render(<MessageBubble message={mockAssistantMessage} />)
    
    expect(screen.getByText('Curated Study Materials:')).toBeInTheDocument()
    expect(screen.getByText('AWS Documentation')).toBeInTheDocument()
    expect(screen.getByText('Study Guide')).toBeInTheDocument()
  })

  it('does not display sources for user messages', () => {
    render(<MessageBubble message={mockUserMessage} />)
    
    expect(screen.queryByText('Curated Study Materials:')).not.toBeInTheDocument()
  })

  it('handles enhanced mode messages', () => {
    const enhancedMessage: ChatMessage = {
      ...mockAssistantMessage,
      mode_used: 'enhanced',
      sources: ['AWS Documentation', 'Claude General Knowledge']
    }

    render(<MessageBubble message={enhancedMessage} />)
    
    expect(screen.getByText('Enhanced')).toBeInTheDocument()
  })

  it('handles messages without sources', () => {
    const messageWithoutSources: ChatMessage = {
      role: 'assistant',
      content: 'Response without sources',
      timestamp: '2025-01-01T12:02:00Z'
    }

    render(<MessageBubble message={messageWithoutSources} />)
    
    expect(screen.getByText('Response without sources')).toBeInTheDocument()
    expect(screen.queryByText('Curated Study Materials:')).not.toBeInTheDocument()
  })

  it('preserves line breaks in message content', () => {
    const multilineMessage: ChatMessage = {
      role: 'user',
      content: 'Line 1\nLine 2\nLine 3',
      timestamp: '2025-01-01T12:03:00Z'
    }

    render(<MessageBubble message={multilineMessage} />)
    
    const messageElement = screen.getByText('Line 1\nLine 2\nLine 3', { selector: '.whitespace-pre-wrap' })
    expect(messageElement).toHaveClass('whitespace-pre-wrap')
  })
})