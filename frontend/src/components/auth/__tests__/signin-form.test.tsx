import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { SignInForm } from '../signin-form'

describe('SignInForm', () => {
  it('renders sign in button', () => {
    render(<SignInForm />)
    expect(screen.getByText('Sign in with AWS Cognito')).toBeInTheDocument()
  })

  it('shows create account link', () => {
    render(<SignInForm />)
    expect(screen.getByText('New to ProCert?')).toBeInTheDocument()
    expect(screen.getByText('Create an account')).toBeInTheDocument()
  })
})