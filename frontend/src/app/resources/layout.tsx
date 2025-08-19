import { AppLayout } from '@/components/layout/app-layout'

export default function ResourcesLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return <AppLayout>{children}</AppLayout>
}