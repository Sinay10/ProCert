import { AppLayout } from '@/components/layout/app-layout'

export default function ProgressLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return <AppLayout>{children}</AppLayout>
}