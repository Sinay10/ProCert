import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { MessageSquare, Brain, TrendingUp, Award, CheckCircle } from 'lucide-react'

const features = [
  {
    name: 'AI-Powered Chat',
    description: 'Get instant answers to your AWS questions with our intelligent chatbot that uses curated study materials.',
    icon: MessageSquare,
  },
  {
    name: 'Adaptive Quizzes',
    description: 'Practice with dynamic quizzes that adapt to your knowledge level and focus on your weak areas.',
    icon: Brain,
  },
  {
    name: 'Progress Tracking',
    description: 'Monitor your learning journey with detailed analytics and performance insights.',
    icon: TrendingUp,
  },
  {
    name: 'Certification Ready',
    description: 'Get personalized study paths and readiness assessments for AWS certifications.',
    icon: Award,
  },
]

const benefits = [
  'Personalized learning experience',
  'Real-time progress tracking',
  'Expert-curated content',
  'Adaptive difficulty levels',
  'Comprehensive analytics',
  'Mobile-friendly interface',
]

export function LandingPage() {
  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="border-b border-secondary-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center space-x-2">
              <div className="h-8 w-8 bg-primary-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">PC</span>
              </div>
              <span className="text-xl font-bold text-secondary-900">ProCert</span>
            </div>
            <Link href="/auth/signin">
              <Button>Get Started</Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="py-20 bg-gradient-to-br from-primary-50 to-secondary-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="text-4xl font-bold tracking-tight text-secondary-900 sm:text-6xl">
              Master AWS Certifications with{' '}
              <span className="text-primary-600">AI-Powered Learning</span>
            </h1>
            <p className="mt-6 text-lg leading-8 text-secondary-600 max-w-2xl mx-auto">
              Transform your AWS certification journey with personalized AI assistance, 
              adaptive quizzes, and comprehensive progress tracking.
            </p>
            <div className="mt-10 flex items-center justify-center gap-x-6">
              <Link href="/auth/signin">
                <Button size="lg">
                  Start Learning Today
                </Button>
              </Link>
              <Button variant="outline" size="lg">
                Learn More
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h2 className="text-3xl font-bold tracking-tight text-secondary-900 sm:text-4xl">
              Everything you need to succeed
            </h2>
            <p className="mt-4 text-lg text-secondary-600">
              Comprehensive tools designed to accelerate your AWS certification journey
            </p>
          </div>
          
          <div className="mt-16 grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-4">
            {features.map((feature) => {
              const Icon = feature.icon
              return (
                <Card key={feature.name} className="text-center">
                  <CardHeader>
                    <div className="mx-auto h-12 w-12 bg-primary-100 rounded-lg flex items-center justify-center">
                      <Icon className="h-6 w-6 text-primary-600" />
                    </div>
                    <CardTitle className="text-lg">{feature.name}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <CardDescription>{feature.description}</CardDescription>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        </div>
      </section>

      {/* Benefits Section */}
      <section className="py-24 bg-secondary-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-3xl font-bold tracking-tight text-secondary-900 sm:text-4xl">
                Why choose ProCert?
              </h2>
              <p className="mt-4 text-lg text-secondary-600">
                Our platform combines the latest in AI technology with expert-curated 
                content to provide the most effective learning experience.
              </p>
              
              <div className="mt-8 space-y-4">
                {benefits.map((benefit) => (
                  <div key={benefit} className="flex items-center">
                    <CheckCircle className="h-5 w-5 text-success-500 mr-3" />
                    <span className="text-secondary-700">{benefit}</span>
                  </div>
                ))}
              </div>
              
              <div className="mt-8">
                <Link href="/auth/signin">
                  <Button size="lg">
                    Get Started Now
                  </Button>
                </Link>
              </div>
            </div>
            
            <div className="relative">
              <Card className="p-8">
                <div className="space-y-4">
                  <div className="h-4 bg-secondary-200 rounded w-3/4"></div>
                  <div className="h-4 bg-secondary-200 rounded w-1/2"></div>
                  <div className="h-4 bg-primary-200 rounded w-2/3"></div>
                  <div className="h-32 bg-secondary-100 rounded"></div>
                  <div className="flex space-x-2">
                    <div className="h-8 bg-primary-600 rounded flex-1"></div>
                    <div className="h-8 bg-secondary-200 rounded flex-1"></div>
                  </div>
                </div>
              </Card>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 bg-primary-600">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
            Ready to ace your AWS certification?
          </h2>
          <p className="mt-4 text-lg text-primary-100">
            Join thousands of successful candidates who chose ProCert
          </p>
          <div className="mt-8">
            <Link href="/auth/signin">
              <Button size="lg" variant="secondary">
                Start Your Journey
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-secondary-900 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <div className="flex items-center justify-center space-x-2 mb-4">
              <div className="h-8 w-8 bg-primary-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">PC</span>
              </div>
              <span className="text-xl font-bold text-white">ProCert</span>
            </div>
            <p className="text-secondary-400">
              © 2025 ProCert Learning Platform. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}