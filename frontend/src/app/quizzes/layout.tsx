import { AppLayout } from '@/components/layout/app-layout'

export default function QuizzesLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return <AppLayout>{children}</AppLayout>
}