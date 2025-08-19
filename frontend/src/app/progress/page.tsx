import { Metadata } from 'next'
import { ProgressDashboard } from '@/components/progress'

export const metadata: Metadata = {
  title: 'Progress - ProCert Learning Platform',
  description: 'Track your learning progress and performance',
}

export default function ProgressPage() {
  return <ProgressDashboard />
}