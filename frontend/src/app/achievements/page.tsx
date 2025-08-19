import { Metadata } from 'next'
import { AchievementsPage } from '@/components/achievements'

export const metadata: Metadata = {
  title: 'Achievements - ProCert Learning Platform',
  description: 'View your learning achievements and progress milestones',
}

export default function Achievements() {
  return <AchievementsPage />
}