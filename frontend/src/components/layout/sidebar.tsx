'use client'

import { usePathname } from 'next/navigation'
import Link from 'next/link'
import { clsx } from 'clsx'
import { 
  LayoutDashboard, 
  MessageSquare, 
  Brain, 
  TrendingUp, 
  Map, 
  BookOpen,
  Award,
  Settings
} from 'lucide-react'

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'AI Chat', href: '/chat', icon: MessageSquare },
  { name: 'Practice Quizzes', href: '/quizzes', icon: Brain },
  { name: 'Progress', href: '/progress', icon: TrendingUp },
  { name: 'Study Path', href: '/study-path', icon: Map },
  { name: 'Resources', href: '/resources', icon: BookOpen },
  { name: 'Achievements', href: '/achievements', icon: Award },
]

const secondaryNavigation = [
  { name: 'Settings', href: '/settings', icon: Settings },
]

interface SidebarProps {
  className?: string
}

export function Sidebar({ className }: SidebarProps) {
  const pathname = usePathname()

  return (
    <div className={clsx('flex flex-col h-full bg-white border-r border-secondary-200', className)}>
      {/* Primary Navigation */}
      <nav className="flex-1 px-4 py-6 space-y-1">
        {navigation.map((item) => {
          const Icon = item.icon
          const isActive = pathname === item.href
          
          return (
            <Link
              key={item.name}
              href={item.href}
              className={clsx(
                'group flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors',
                isActive
                  ? 'bg-primary-100 text-primary-700'
                  : 'text-secondary-600 hover:text-secondary-900 hover:bg-secondary-50'
              )}
            >
              <Icon
                className={clsx(
                  'mr-3 h-5 w-5 flex-shrink-0',
                  isActive
                    ? 'text-primary-500'
                    : 'text-secondary-400 group-hover:text-secondary-500'
                )}
              />
              {item.name}
            </Link>
          )
        })}
      </nav>

      {/* Secondary Navigation */}
      <div className="px-4 py-4 border-t border-secondary-200">
        {secondaryNavigation.map((item) => {
          const Icon = item.icon
          const isActive = pathname === item.href
          
          return (
            <Link
              key={item.name}
              href={item.href}
              className={clsx(
                'group flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors',
                isActive
                  ? 'bg-primary-100 text-primary-700'
                  : 'text-secondary-600 hover:text-secondary-900 hover:bg-secondary-50'
              )}
            >
              <Icon
                className={clsx(
                  'mr-3 h-5 w-5 flex-shrink-0',
                  isActive
                    ? 'text-primary-500'
                    : 'text-secondary-400 group-hover:text-secondary-500'
                )}
              />
              {item.name}
            </Link>
          )
        })}
      </div>
    </div>
  )
}