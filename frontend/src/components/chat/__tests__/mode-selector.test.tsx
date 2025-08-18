import { render, screen, fireEvent } from '@testing-library/react'
import { ModeSelector } from '../mode-selector'
import { vi } from 'vitest'
import { it } from 'node:test'
import { it } from 'node:test'
import { it } from 'node:test'
import { it } from 'node:test'
import { it } from 'node:test'
import { it } from 'node:test'
import { it } from 'node:test'
import { it } from 'node:test'
import { it } from 'node:test'
import { beforeEach } from 'node:test'
import { describe } from 'node:test'

describe('ModeSelector', () => {
  const mockOnModeChange = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders mode selector with both options', () => {
    render(<ModeSelector currentMode="rag" onModeChange={mockOnModeChange} />)
    
    expect(screen.getByText('Response Mode')).toBeInTheDocument()
    expect(screen.getByText('Curated Only')).toBeInTheDocument()
    expect(screen.getByText('Enhanced')).toBeInTheDocument()
  })

  it('highlights current mode correctly', () => {
    render(<ModeSelector currentMode="rag" onModeChange={mockOnModeChange} />)
    
    const curatedButton = screen.getByRole('button', { name: /curated only/i })
    const enhancedButton = screen.getByRole('button', { name: /enhanced/i })
    
    expect(curatedButton).toHaveClass('bg-blue-600', 'text-white')
    expect(enhancedButton).toHaveClass('bg-white', 'text-secondary-700')
  })

  it('highlights enhanced mode when selected', () => {
    render(<ModeSelector currentMode="enhanced" onModeChange={mockOnModeChange} />)
    
    const curatedButton = screen.getByRole('button', { name: /curated only/i })
    const enhancedButton = screen.getByRole('button', { name: /enhanced/i })
    
    expect(curatedButton).toHaveClass('bg-white', 'text-secondary-700')
    expect(enhancedButton).toHaveClass('bg-amber-600', 'text-white')
  })

  it('calls onModeChange when curated mode is clicked', () => {
    render(<ModeSelector currentMode="enhanced" onModeChange={mockOnModeChange} />)
    
    const curatedButton = screen.getByRole('button', { name: /curated only/i })
    fireEvent.click(curatedButton)
    
    expect(mockOnModeChange).toHaveBeenCalledWith('rag')
  })

  it('calls onModeChange when enhanced mode is clicked', () => {
    render(<ModeSelector currentMode="rag" onModeChange={mockOnModeChange} />)
    
    const enhancedButton = screen.getByRole('button', { name: /enhanced/i })
    fireEvent.click(enhancedButton)
    
    expect(mockOnModeChange).toHaveBeenCalledWith('enhanced')
  })

  it('shows correct description for RAG mode', () => {
    render(<ModeSelector currentMode="rag" onModeChange={mockOnModeChange} />)
    
    expect(screen.getByText('Uses only curated study materials')).toBeInTheDocument()
  })

  it('shows correct description for enhanced mode', () => {
    render(<ModeSelector currentMode="enhanced" onModeChange={mockOnModeChange} />)
    
    expect(screen.getByText('Includes additional AWS knowledge when needed')).toBeInTheDocument()
  })

  it('displays mode indicators with correct colors', () => {
    render(<ModeSelector currentMode="rag" onModeChange={mockOnModeChange} />)
    
    const curatedIndicator = screen.getByText('Curated Only').querySelector('div')
    const enhancedIndicator = screen.getByText('Enhanced').querySelector('div')
    
    expect(curatedIndicator).toHaveClass('bg-blue-200') // Active state
    expect(enhancedIndicator).toHaveClass('bg-amber-600') // Inactive state
  })

  it('has proper accessibility attributes', () => {
    render(<ModeSelector currentMode="rag" onModeChange={mockOnModeChange} />)
    
    const curatedButton = screen.getByRole('button', { name: /curated only/i })
    const enhancedButton = screen.getByRole('button', { name: /enhanced/i })
    
    expect(curatedButton.tagName).toBe('BUTTON')
    expect(enhancedButton.tagName).toBe('BUTTON')
  })
})