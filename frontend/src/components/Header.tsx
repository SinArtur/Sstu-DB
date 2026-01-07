import { useAuthStore } from '@/store/authStore'
import { Bell, User, LogOut, Menu } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useState, useEffect, useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import api from '@/lib/api'
import { getUserDisplayName } from '@/lib/utils'

interface HeaderProps {
  onMenuClick?: () => void
}

export default function Header({ onMenuClick }: HeaderProps) {
  const { user, logout } = useAuthStore()
  const [showUserMenu, setShowUserMenu] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)

  const { data: unreadCount } = useQuery({
    queryKey: ['notifications', 'unread-count'],
    queryFn: async () => {
      const res = await api.get('/notifications/unread_count/')
      return res.data.count
    },
  })

  // Close user menu when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setShowUserMenu(false)
      }
    }

    if (showUserMenu) {
      document.addEventListener('mousedown', handleClickOutside)
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [showUserMenu])

  return (
    <header className="h-16 border-b bg-card flex items-center justify-between px-4 md:px-6 relative z-20 md:z-auto">
      <div className="flex items-center gap-4">
        {/* Mobile menu button */}
        {onMenuClick && (
          <button
            onClick={(e) => {
              e.preventDefault()
              e.stopPropagation()
              onMenuClick()
            }}
            onTouchEnd={(e) => {
              e.preventDefault()
              e.stopPropagation()
              onMenuClick()
            }}
            className="md:hidden p-2 hover:bg-accent active:bg-accent/80 rounded-lg relative z-50"
            aria-label="Открыть меню"
            type="button"
            style={{
              touchAction: 'manipulation',
            }}
          >
            <Menu className="h-5 w-5" />
          </button>
        )}
      </div>

      <div className="flex items-center gap-2 md:gap-4">
        <Link
          to="/profile"
          className="relative p-2 text-muted-foreground hover:text-foreground"
        >
          <Bell className="h-5 w-5" />
          {unreadCount && unreadCount > 0 && (
            <span className="absolute top-0 right-0 h-4 w-4 bg-destructive text-destructive-foreground text-xs rounded-full flex items-center justify-center">
              {unreadCount}
            </span>
          )}
        </Link>

        <div className="relative" ref={menuRef}>
          <button
            onClick={() => setShowUserMenu(!showUserMenu)}
            className="flex items-center gap-2 p-2 rounded-lg hover:bg-accent"
          >
            <User className="h-5 w-5" />
            <span className="hidden md:inline">{getUserDisplayName(user)}</span>
          </button>

          {showUserMenu && (
            <div className="absolute right-0 mt-2 w-48 bg-card border rounded-lg shadow-lg z-50">
              <Link
                to="/profile"
                className="block px-4 py-2 hover:bg-accent"
                onClick={() => setShowUserMenu(false)}
              >
                Профиль
              </Link>
              {user?.role === 'moderator' || user?.role === 'admin' ? (
                <Link
                  to="/moderation"
                  className="block px-4 py-2 hover:bg-accent"
                  onClick={() => setShowUserMenu(false)}
                >
                  Модерация
                </Link>
              ) : null}
              {(user?.role === 'admin' || (user?.role === 'moderator' && user?.can_access_admin_panel)) ? (
                <Link
                  to="/admin"
                  className="block px-4 py-2 hover:bg-accent"
                  onClick={() => setShowUserMenu(false)}
                >
                  Админ-панель
                </Link>
              ) : null}
              <button
                onClick={() => {
                  logout()
                  setShowUserMenu(false)
                }}
                className="w-full text-left px-4 py-2 hover:bg-accent flex items-center gap-2"
              >
                <LogOut className="h-4 w-4" />
                Выйти
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
