import { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'

interface ProtectedRouteProps {
  children: ReactNode
  requireModerator?: boolean
  requireAdmin?: boolean
}

export default function ProtectedRoute({ 
  children, 
  requireModerator = false,
  requireAdmin = false 
}: ProtectedRouteProps) {
  const { isAuthenticated, user } = useAuthStore()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (requireAdmin && user?.role !== 'admin') {
    return <Navigate to="/" replace />
  }

  if (requireModerator && !['moderator', 'admin'].includes(user?.role || '')) {
    return <Navigate to="/" replace />
  }

  return <>{children}</>
}

