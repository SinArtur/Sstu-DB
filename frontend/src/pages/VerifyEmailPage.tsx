import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { useAuthStore } from '@/store/authStore'
import api from '@/lib/api'
import toast from 'react-hot-toast'
import { CheckCircle, XCircle, Loader } from 'lucide-react'

export default function VerifyEmailPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { setAuth } = useAuthStore()
  const token = searchParams.get('token')
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading')
  const [message, setMessage] = useState('')

  const verifyMutation = useMutation({
    mutationFn: async (token: string) => {
      const res = await api.post('/auth/verify-email/', { token })
      return res.data
    },
    onSuccess: (data) => {
      setStatus('success')
      setMessage(data.message || 'Email успешно подтвержден')
      
      // Update user data in store if user is logged in
      if (data.user) {
        const { accessToken, refreshToken } = useAuthStore.getState()
        if (accessToken && refreshToken) {
          setAuth(data.user, accessToken, refreshToken)
        }
      }
      
      toast.success('Email подтвержден!')
      setTimeout(() => {
        navigate('/profile')
      }, 2000)
    },
    onError: (error: any) => {
      setStatus('error')
      const errorMessage = error.response?.data?.error || 'Ошибка подтверждения email'
      setMessage(errorMessage)
      toast.error(errorMessage)
    },
  })

  useEffect(() => {
    if (token) {
      verifyMutation.mutate(token)
    } else {
      setStatus('error')
      setMessage('Токен подтверждения не найден')
    }
  }, [token])

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="w-full max-w-md p-8 bg-card border rounded-lg shadow-lg text-center">
        {status === 'loading' && (
          <>
            <Loader className="h-16 w-16 mx-auto mb-4 animate-spin text-primary" />
            <h1 className="text-2xl font-bold mb-2">Подтверждение email</h1>
            <p className="text-muted-foreground">Пожалуйста, подождите...</p>
          </>
        )}

        {status === 'success' && (
          <>
            <CheckCircle className="h-16 w-16 mx-auto mb-4 text-green-500" />
            <h1 className="text-2xl font-bold mb-2">Email подтвержден!</h1>
            <p className="text-muted-foreground mb-4">{message}</p>
            <p className="text-sm text-muted-foreground">Перенаправление на страницу профиля...</p>
          </>
        )}

        {status === 'error' && (
          <>
            <XCircle className="h-16 w-16 mx-auto mb-4 text-red-500" />
            <h1 className="text-2xl font-bold mb-2">Ошибка подтверждения</h1>
            <p className="text-muted-foreground mb-4">{message}</p>
            <button
              onClick={() => navigate('/profile')}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90"
            >
              Перейти в профиль
            </button>
          </>
        )}
      </div>
    </div>
  )
}








