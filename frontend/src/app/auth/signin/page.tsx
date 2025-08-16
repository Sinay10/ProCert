import { Metadata } from 'next'
import { SignInForm } from '@/components/auth/signin-form'

export const metadata: Metadata = {
  title: 'Sign In - ProCert Learning Platform',
  description: 'Sign in to your ProCert account',
}

export default function SignInPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-secondary-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <div className="mx-auto h-12 w-12 bg-primary-600 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-lg">PC</span>
          </div>
          <h2 className="mt-6 text-center text-3xl font-bold text-secondary-900">
            Sign in to your account
          </h2>
          <p className="mt-2 text-center text-sm text-secondary-600">
            Continue your AWS certification journey
          </p>
        </div>
        <SignInForm />
      </div>
    </div>
  )
}