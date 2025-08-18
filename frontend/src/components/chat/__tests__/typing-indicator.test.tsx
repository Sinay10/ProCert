import { render, screen } from '@testing-library/react'
import { TypingIndicator } from '../typing-indicator'

describe('TypingIndicator', () => {
  it('renders typing indicator with AI avatar', () => {
    render(<TypingIndicator />)
    
    expect(screen.getByText('AI')).toBeInTheDocument()
    expect(screen.getByText('AI is typing...')).toBeInTheDocument()
  })

  it('displays animated dots', () => {
    const { container } = render(<TypingIndicator />)
    
    const dots = container.querySelectorAll('.animate-bounce')
    expect(dots).toHaveLength(3)
  })

  it('has proper styling for typing animation', () => {
    const { container } = render(<TypingIndicator />)
    
    const dots = container.querySelectorAll('.animate-bounce')
    
    // Check that dots have different animation delays
    expect(dots[0]).toHaveStyle('animation-delay: 0ms')
    expect(dots[1]).toHaveStyle('animation-delay: 150ms')
    expect(dots[2]).toHaveStyle('animation-delay: 300ms')
  })

  it('uses consistent styling with message bubbles', () => {
    const { container } = render(<TypingIndicator />)
    
    const avatar = screen.getByText('AI')
    const bubble = container.querySelector('.bg-secondary-100')
    
    expect(avatar).toHaveClass('w-8', 'h-8', 'rounded-full', 'bg-secondary-600', 'text-white')
    expect(bubble).toHaveClass('bg-secondary-100', 'text-secondary-900', 'px-4', 'py-3', 'rounded-lg')
  })

  it('positions correctly as assistant message', () => {
    const { container } = render(<TypingIndicator />)
    
    const wrapper = container.firstChild
    expect(wrapper).toHaveClass('flex', 'justify-start')
  })
})