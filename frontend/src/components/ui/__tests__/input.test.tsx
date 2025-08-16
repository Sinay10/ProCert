import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { Input } from '../input'

describe('Input', () => {
  it('renders with default props', () => {
    render(<Input placeholder="Enter text" />)
    const input = screen.getByPlaceholderText('Enter text')
    expect(input).toBeInTheDocument()
    expect(input).toHaveClass('input')
  })

  it('renders with label', () => {
    render(<Input label="Username" placeholder="Enter username" />)
    expect(screen.getByLabelText('Username')).toBeInTheDocument()
    expect(screen.getByText('Username')).toBeInTheDocument()
  })

  it('shows error state', () => {
    render(<Input error="This field is required" placeholder="Enter text" />)
    const input = screen.getByPlaceholderText('Enter text')
    expect(input).toHaveClass('border-error-500', 'focus:ring-error-500')
    expect(screen.getByText('This field is required')).toBeInTheDocument()
  })

  it('shows helper text', () => {
    render(<Input helperText="This is helper text" placeholder="Enter text" />)
    expect(screen.getByText('This is helper text')).toBeInTheDocument()
  })

  it('prioritizes error over helper text', () => {
    render(
      <Input 
        error="Error message" 
        helperText="Helper text" 
        placeholder="Enter text" 
      />
    )
    expect(screen.getByText('Error message')).toBeInTheDocument()
    expect(screen.queryByText('Helper text')).not.toBeInTheDocument()
  })

  it('handles input changes', () => {
    const handleChange = vi.fn()
    render(<Input onChange={handleChange} placeholder="Enter text" />)
    
    const input = screen.getByPlaceholderText('Enter text')
    fireEvent.change(input, { target: { value: 'test value' } })
    
    expect(handleChange).toHaveBeenCalled()
  })

  it('renders with icons', () => {
    const LeftIcon = () => <span data-testid="left-icon">←</span>
    const RightIcon = () => <span data-testid="right-icon">→</span>
    
    render(
      <Input 
        leftIcon={<LeftIcon />} 
        rightIcon={<RightIcon />}
        placeholder="Enter text"
      />
    )
    
    expect(screen.getByTestId('left-icon')).toBeInTheDocument()
    expect(screen.getByTestId('right-icon')).toBeInTheDocument()
    
    const input = screen.getByPlaceholderText('Enter text')
    expect(input).toHaveClass('pl-10', 'pr-10')
  })
})