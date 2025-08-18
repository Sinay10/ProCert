import { render, screen, fireEvent } from '@testing-library/react'
import { MessageInput } from '../message-input'
import { vi } from 'vitest'

describe('MessageInput', () => {
  const mockOnSendMessage = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders input field and send button', () => {
    render(<MessageInput onSendMessage={mockOnSendMessage} />)
    
    expect(screen.getByPlaceholderText('Type your message...')).toBeInTheDocument()
    expect(screen.getByText('Send')).toBeInTheDocument()
  })

  it('uses custom placeholder when provided', () => {
    render(<MessageInput onSendMessage={mockOnSendMessage} placeholder="Custom placeholder" />)
    
    expect(screen.getByPlaceholderText('Custom placeholder')).toBeInTheDocument()
  })

  it('sends message when send button is clicked', () => {
    render(<MessageInput onSendMessage={mockOnSendMessage} />)
    
    const input = screen.getByPlaceholderText('Type your message...')
    const sendButton = screen.getByText('Send')
    
    fireEvent.change(input, { target: { value: 'Test message' } })
    fireEvent.click(sendButton)
    
    expect(mockOnSendMessage).toHaveBeenCalledWith('Test message')
  })

  it('sends message when Enter key is pressed', () => {
    render(<MessageInput onSendMessage={mockOnSendMessage} />)
    
    const input = screen.getByPlaceholderText('Type your message...')
    
    fireEvent.change(input, { target: { value: 'Test message' } })
    fireEvent.keyDown(input, { key: 'Enter', shiftKey: false })
    
    expect(mockOnSendMessage).toHaveBeenCalledWith('Test message')
  })

  it('does not send message when Shift+Enter is pressed', () => {
    render(<MessageInput onSendMessage={mockOnSendMessage} />)
    
    const input = screen.getByPlaceholderText('Type your message...')
    
    fireEvent.change(input, { target: { value: 'Test message' } })
    fireEvent.keyDown(input, { key: 'Enter', shiftKey: true })
    
    expect(mockOnSendMessage).not.toHaveBeenCalled()
  })

  it('clears input after sending message', () => {
    render(<MessageInput onSendMessage={mockOnSendMessage} />)
    
    const input = screen.getByPlaceholderText('Type your message...') as HTMLTextAreaElement
    const sendButton = screen.getByText('Send')
    
    fireEvent.change(input, { target: { value: 'Test message' } })
    fireEvent.click(sendButton)
    
    expect(input.value).toBe('')
  })

  it('trims whitespace from messages', () => {
    render(<MessageInput onSendMessage={mockOnSendMessage} />)
    
    const input = screen.getByPlaceholderText('Type your message...')
    const sendButton = screen.getByText('Send')
    
    fireEvent.change(input, { target: { value: '  Test message  ' } })
    fireEvent.click(sendButton)
    
    expect(mockOnSendMessage).toHaveBeenCalledWith('Test message')
  })

  it('does not send empty or whitespace-only messages', () => {
    render(<MessageInput onSendMessage={mockOnSendMessage} />)
    
    const input = screen.getByPlaceholderText('Type your message...')
    const sendButton = screen.getByText('Send')
    
    // Test empty message
    fireEvent.change(input, { target: { value: '' } })
    fireEvent.click(sendButton)
    expect(mockOnSendMessage).not.toHaveBeenCalled()
    
    // Test whitespace-only message
    fireEvent.change(input, { target: { value: '   ' } })
    fireEvent.click(sendButton)
    expect(mockOnSendMessage).not.toHaveBeenCalled()
  })

  it('disables input and button when disabled prop is true', () => {
    render(<MessageInput onSendMessage={mockOnSendMessage} disabled={true} />)
    
    const input = screen.getByPlaceholderText('Type your message...')
    const sendButton = screen.getByRole('button', { name: /sending/i })
    
    expect(input).toBeDisabled()
    expect(sendButton).toBeDisabled()
  })

  it('shows loading state when disabled', () => {
    render(<MessageInput onSendMessage={mockOnSendMessage} disabled={true} />)
    
    expect(screen.getByText('Sending')).toBeInTheDocument()
    expect(screen.queryByText('Send')).not.toBeInTheDocument()
  })

  it('disables send button when input is empty', () => {
    render(<MessageInput onSendMessage={mockOnSendMessage} />)
    
    const sendButton = screen.getByRole('button', { name: /send/i })
    expect(sendButton).toBeDisabled()
    
    const input = screen.getByPlaceholderText('Type your message...')
    fireEvent.change(input, { target: { value: 'Test' } })
    expect(sendButton).not.toBeDisabled()
  })

  it('shows keyboard shortcut hint', () => {
    render(<MessageInput onSendMessage={mockOnSendMessage} />)
    
    expect(screen.getByText('Press Enter to send, Shift+Enter for new line')).toBeInTheDocument()
  })

  it('auto-resizes textarea based on content', () => {
    render(<MessageInput onSendMessage={mockOnSendMessage} />)
    
    const textarea = screen.getByPlaceholderText('Type your message...') as HTMLTextAreaElement
    
    // Mock scrollHeight to simulate content height
    Object.defineProperty(textarea, 'scrollHeight', {
      configurable: true,
      value: 80
    })
    
    fireEvent.change(textarea, { target: { value: 'Line 1\nLine 2\nLine 3' } })
    
    expect(textarea.style.height).toBe('80px')
  })
})