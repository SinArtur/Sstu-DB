import { useAuthStore } from '@/store/authStore'
import { Bell, User, LogOut } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import api from '@/lib/api'
import { getUserDisplayName } from '@/lib/utils'

export default function Header() {
  const { user, logout } = useAuthStore()
  const [showUserMenu, setShowUserMenu] = useState(false)

  const { data: unreadCount } = useQuery({
    queryKey: ['notifications', 'unread-count'],
    queryFn: async () => {
      const res = await api.get('/notifications/unread_count/')
      return res.data.count
    },
  })

  return (
    <header className="h-16 border-b bg-card flex items-center justify-between px-6">
      <div className="flex items-center gap-4">
        {/* Search removed - now shown only on branches page */}
      </div>

      <div className="flex items-center gap-4">
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

        <div className="relative">
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

