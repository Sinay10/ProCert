import { Metadata } from 'next'
import { ResourcesBrowser } from '@/components/resources'

export const metadata: Metadata = {
  title: 'Resources - ProCert Learning Platform',
  description: 'Browse AWS certification documentation and study materials',
}

export default function ResourcesPage() {
  return <ResourcesBrowser />
}