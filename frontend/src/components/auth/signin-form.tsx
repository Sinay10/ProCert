'use client'

import { useState, Suspense } from 'react'
import { signIn } from 'next-auth/react'
import { useRouter, useSearchParams } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { API_ENDPOINTS } from '@/lib/api-client'

function SignInFormContent() {
  const [isLoading, setIsLoading] = useState(false)
  const [isRegistering, setIsRegistering] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [error, setError] = useState('')
  const router = useRouter()
  const searchParams = useSearchParams()
  const callbackUrl = searchParams.get('callbackUrl') || '/dashboard'

  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!email || !password) {
      setError('Please fill in all fields')
      return
    }

    try {
      setIsLoading(true)
      setError('')
      
      const result = await signIn('credentials', {
        email,
        password,
        redirect: false,
      })

      if (result?.ok) {
        router.push(callbackUrl)
      } else {
        console.error('Sign in failed:', result)
        setError(result?.error || 'Invalid email or password')
      }
    } catch (error) {
      console.error('Sign in error:', error)
      setError('An error occurred during sign in')
    } finally {
      setIsLoading(false)
    }
  }

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!email || !password || !name) {
      setError('Please fill in all fields')
      return
    }

    try {
      setIsLoading(true)
      setError('')

      console.log('Attempting registration with:', { email, name })
      console.log('API URL:', process.env.NEXT_PUBLIC_API_BASE_URL)

      // Register user with your API using fetch (since it works)
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}${API_ENDPOINTS.AUTH_REGISTER}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify({
          email,
          password,
          name,
        }),
      })

      console.log('Registration response status:', response.status)
      console.log('Registration response headers:', Object.fromEntries(response.headers.entries()))

      if (response.ok) {
        const registrationData = await response.json()
        console.log('Registration successful:', registrationData)

        // After successful registration, sign in
        console.log('Attempting sign in after registration...')
        const result = await signIn('credentials', {
          email,
          password,
          redirect: false,
        })

        console.log('Sign in result:', result)

        if (result?.ok) {
          console.log('Sign in successful, redirecting to:', callbackUrl)
          router.push(callbackUrl)
        } else {
          console.error('Sign in after registration failed:', result)
          setError(`Registration successful! Please try signing in manually. Error: ${result?.error || 'Unknown error'}`)
        }
      } else {
        const data = await response.json().catch(() => ({ message: 'Registration failed' }))
        console.error('Registration failed:', response.status, data)
        setError(data.error || data.message || `Registration failed (${response.status})`)
      }
    } catch (error) {
      console.error('Registration error:', error)
      setError('An error occurred during registration')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>
          {isRegistering ? 'Create Account' : 'Sign In'}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={isRegistering ? handleRegister : handleSignIn} className="space-y-4">
          {isRegistering && (
            <Input
              label="Full Name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Enter your full name"
              required
            />
          )}
          
          <Input
            label="Email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Enter your email"
            required
          />
          
          <Input
            label="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Enter your password"
            required
          />

          {error && (
            <div className="text-sm text-error-600 bg-error-50 p-3 rounded-md">
              {error}
            </div>
          )}

          <Button
            type="submit"
            loading={isLoading}
            className="w-full"
            size="lg"
          >
            {isRegistering ? 'Create Account' : 'Sign In'}
          </Button>
          
          <div className="text-center text-sm text-secondary-600">
            <p>
              {isRegistering ? 'Already have an account?' : 'New to ProCert?'}{' '}
              <button
                type="button"
                onClick={() => {
                  setIsRegistering(!isRegistering)
                  setError('')
                }}
                className="font-medium text-primary-600 hover:text-primary-500"
              >
                {isRegistering ? 'Sign In' : 'Create an account'}
              </button>
            </p>
            
            {/* Temporary test button */}
            <div className="mt-4">
              <button
                type="button"
                onClick={async () => {
                  console.log('Testing registration with API client...')
                  try {
                    const { apiClient } = await import('@/lib/api-client')
                    const testUser = {
                      email: `test-${Date.now()}@example.com`,
                      password: 'TestPass123!',
                      name: 'API Test User'
                    }
                    console.log('Making API call to:', API_ENDPOINTS.AUTH_REGISTER)
                    const result = await apiClient.post(API_ENDPOINTS.AUTH_REGISTER, testUser)
                    console.log('✅ API Client registration success:', result)
                    setError('✅ API Client test successful! Registration works with axios fallback.')
                  } catch (error: any) {
                    console.error('❌ API Client registration failed:', error)
                    setError(`❌ API Client test failed: ${error.message}`)
                  }
                }}
                className="text-xs text-secondary-500 hover:text-secondary-700"
              >
                🔧 Test API Client Registration
              </button>
            </div>
          </div>
        </form>
      </CardContent>
    </Card>
  )
}

export function SignInForm() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <SignInFormContent />
    </Suspense>
  )
}