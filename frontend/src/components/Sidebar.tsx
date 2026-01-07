import { Link, useLocation } from 'react-router-dom'
import { Home, BookOpen, Settings, Calendar, X } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useEffect } from 'react'

const navItems = [
  { path: '/', label: 'Главная', icon: Home },
  { path: '/branches', label: 'База знаний', icon: BookOpen },
  { path: '/schedule', label: 'Расписание', icon: Calendar },
  { path: '/profile', label: 'Профиль', icon: Settings },
]

interface SidebarProps {
  isOpen?: boolean
  onClose?: () => void
}

export default function Sidebar({ isOpen = true, onClose }: SidebarProps) {
  const location = useLocation()

  // Close sidebar when route changes on mobile
  useEffect(() => {
    if (onClose) {
      onClose()
    }
  }, [location.pathname, onClose])

  return (
    <>
      {/* Backdrop for mobile */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 md:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed md:static inset-y-0 left-0 z-50 w-64 border-r bg-card flex flex-col transform transition-transform duration-300 ease-in-out',
          isOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
        )}
      >
        <div className="p-4 md:p-6 border-b flex items-center justify-between">
          <h1 className="text-xl font-bold">База знаний</h1>
          {onClose && (
            <button
              onClick={onClose}
              className="md:hidden p-2 hover:bg-accent rounded-lg"
              aria-label="Закрыть меню"
            >
              <X className="h-5 w-5" />
            </button>
          )}
        </div>
        
        <nav className="flex-1 p-4 space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive = location.pathname === item.path
            
            return (
              <Link
                key={item.path}
                to={item.path}
                onClick={onClose}
                className={cn(
                  'flex items-center gap-3 px-4 py-3 rounded-lg transition-colors',
                  isActive
                    ? 'bg-primary text-primary-foreground'
                    : 'hover:bg-accent text-muted-foreground hover:text-foreground'
                )}
              >
                <Icon className="h-5 w-5 flex-shrink-0" />
                <span>{item.label}</span>
              </Link>
            )
          })}
        </nav>
      </aside>
    </>
  )
}
