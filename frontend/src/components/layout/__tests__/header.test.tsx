import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { Header } from '../header'

describe('Header', () => {
  it('renders logo and brand name', () => {
    render(<Header />)
    expect(screen.getByText('ProCert')).toBeInTheDocument()
  })

  it('has mobile menu button', () => {
    render(<Header />)
    // The mobile menu button should be present (hidden on desktop)
    const menuButtons = screen.getAllByRole('button')
    expect(menuButtons.length).toBeGreaterThan(0)
  })
})