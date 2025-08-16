import { Metadata } from 'next'
import { DashboardContent } from '@/components/dashboard/dashboard-content'

export const metadata: Metadata = {
  title: 'Dashboard - ProCert Learning Platform',
  description: 'Your personalized learning dashboard',
}

export default function DashboardPage() {
  return <DashboardContent />
}