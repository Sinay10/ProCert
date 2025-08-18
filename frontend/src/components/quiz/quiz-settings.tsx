'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

interface QuizSettingsProps {
  onStartQuiz: (settings: {
    certification: string
    difficulty: string
    count: number
  }) => void
  loading: boolean
  error: string | null
  initialCertification?: string
}

const CERTIFICATIONS = [
  { value: 'aws-advanced-networking-specialty', label: 'AWS Advanced Networking Specialty', backendCode: 'ANS' },
  { value: 'aws-cloud-practitioner', label: 'AWS Cloud Practitioner', backendCode: 'CLF' },
  { value: 'aws-solutions-architect-associate', label: 'AWS Solutions Architect Associate', backendCode: 'SAA' },
  { value: 'aws-developer-associate', label: 'AWS Developer Associate', backendCode: 'DVA' },
  { value: 'aws-sysops-administrator-associate', label: 'AWS SysOps Administrator Associate', backendCode: 'SOA' },
  { value: 'aws-solutions-architect-professional', label: 'AWS Solutions Architect Professional', backendCode: 'SAP' },
  { value: 'aws-devops-engineer-professional', label: 'AWS DevOps Engineer Professional', backendCode: 'DOP' },
]

// Helper function to get backend certification code
const getCertificationCode = (frontendValue: string): string => {
  const cert = CERTIFICATIONS.find(c => c.value === frontendValue)
  return cert?.backendCode || 'SAA' // Default to SAA if not found
}

const DIFFICULTIES = [
  { value: 'beginner', label: 'Beginner', description: 'Basic concepts and fundamentals' },
  { value: 'intermediate', label: 'Intermediate', description: 'Practical applications and scenarios' },
  { value: 'advanced', label: 'Advanced', description: 'Complex scenarios and best practices' },
  { value: 'mixed', label: 'Mixed', description: 'Variety of difficulty levels' },
]

const QUESTION_COUNTS = [5, 10, 15, 20, 25]

export function QuizSettings({ onStartQuiz, loading, error, initialCertification }: QuizSettingsProps) {
  const [certification, setCertification] = useState(initialCertification || 'aws-advanced-networking-specialty')
  const [difficulty, setDifficulty] = useState('mixed')
  const [count, setCount] = useState(10)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onStartQuiz({ certification, difficulty, count })
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Quiz Settings</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Certification Selection */}
          <div>
            <label className="block text-sm font-medium text-secondary-700 mb-2">
              Certification
            </label>
            <select
              value={certification}
              onChange={(e) => setCertification(e.target.value)}
              className="input w-full"
              required
            >
              {CERTIFICATIONS.map((cert) => (
                <option key={cert.value} value={cert.value}>
                  {cert.label}
                </option>
              ))}
            </select>
          </div>

          {/* Difficulty Selection */}
          <div>
            <label className="block text-sm font-medium text-secondary-700 mb-2">
              Difficulty Level
            </label>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {DIFFICULTIES.map((diff) => (
                <label
                  key={diff.value}
                  className={`
                    relative flex cursor-pointer rounded-lg border p-4 focus:outline-none
                    ${difficulty === diff.value
                      ? 'border-primary-600 bg-primary-50 ring-2 ring-primary-600'
                      : 'border-secondary-300 bg-white hover:bg-secondary-50'
                    }
                  `}
                >
                  <input
                    type="radio"
                    name="difficulty"
                    value={diff.value}
                    checked={difficulty === diff.value}
                    onChange={(e) => setDifficulty(e.target.value)}
                    className="sr-only"
                  />
                  <div className="flex flex-col">
                    <span className="block text-sm font-medium text-secondary-900">
                      {diff.label}
                    </span>
                    <span className="block text-sm text-secondary-500">
                      {diff.description}
                    </span>
                  </div>
                  {difficulty === diff.value && (
                    <div className="absolute top-4 right-4">
                      <div className="h-2 w-2 rounded-full bg-primary-600" />
                    </div>
                  )}
                </label>
              ))}
            </div>
          </div>

          {/* Question Count Selection */}
          <div>
            <label className="block text-sm font-medium text-secondary-700 mb-2">
              Number of Questions
            </label>
            <div className="flex flex-wrap gap-2">
              {QUESTION_COUNTS.map((num) => (
                <button
                  key={num}
                  type="button"
                  onClick={() => setCount(num)}
                  className={`
                    px-4 py-2 rounded-md text-sm font-medium transition-colors
                    ${count === num
                      ? 'bg-primary-600 text-white'
                      : 'bg-secondary-100 text-secondary-700 hover:bg-secondary-200'
                    }
                  `}
                >
                  {num}
                </button>
              ))}
            </div>
            <p className="mt-2 text-sm text-secondary-500">
              Estimated time: {Math.ceil(count * 1.5)} minutes
            </p>
          </div>

          {error && (
            <div className="p-4 bg-error-50 border border-error-200 rounded-md">
              <p className="text-error-700">{error}</p>
            </div>
          )}

          <div className="flex justify-end">
            <Button
              type="submit"
              loading={loading}
              disabled={loading}
              size="lg"
            >
              Start Quiz
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  )
}