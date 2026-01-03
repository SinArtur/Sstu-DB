import { useState } from 'react'
import { useNavigate, useSearchParams, Link } from 'react-router-dom'
import api from '@/lib/api'
import toast from 'react-hot-toast'
import { CheckCircle, XCircle, Loader } from 'lucide-react'

export default function PasswordResetConfirmPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const token = searchParams.get('token')
  const [formData, setFormData] = useState({
    password: '',
    password_confirm: '',
  })
  const [loading, setLoading] = useState(false)
  const [status, setStatus] = useState<'form' | 'success' | 'error'>('form')
  const [message, setMessage] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (formData.password !== formData.password_confirm) {
      toast.error('Пароли не совпадают')
      return
    }

    if (formData.password.length < 8) {
      toast.error('Пароль должен содержать минимум 8 символов')
      return
    }

    if (!token) {
      toast.error('Токен не найден')
      return
    }

    setLoading(true)

    try {
      const response = await api.post('/auth/password-reset-confirm/', {
        token,
        password: formData.password,
        password_confirm: formData.password_confirm,
      })
      setStatus('success')
      setMessage(response.data.message || 'Пароль успешно изменен')
      toast.success('Пароль успешно изменен')
      setTimeout(() => {
        navigate('/login')
      }, 2000)
    } catch (error: any) {
      setStatus('error')
      const errorMessage = error.response?.data?.error || 'Ошибка сброса пароля'
      setMessage(errorMessage)
      toast.error(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  if (!token) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="w-full max-w-md p-8 bg-card border rounded-lg shadow-lg text-center">
          <XCircle className="w-16 h-16 mx-auto mb-4 text-red-500" />
          <h1 className="text-2xl font-bold mb-4">Ошибка</h1>
          <p className="text-muted-foreground mb-6">
            Токен сброса пароля не найден. Пожалуйста, запросите новую ссылку для сброса пароля.
          </p>
          <Link
            to="/password-reset-request"
            className="text-primary hover:underline"
          >
            Запросить сброс пароля
          </Link>
        </div>
      </div>
    )
  }

  if (status === 'success') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="w-full max-w-md p-8 bg-card border rounded-lg shadow-lg text-center">
          <CheckCircle className="w-16 h-16 mx-auto mb-4 text-green-500" />
          <h1 className="text-2xl font-bold mb-4">Успешно!</h1>
          <p className="text-muted-foreground mb-6">{message}</p>
          <p className="text-sm text-muted-foreground">
            Перенаправление на страницу входа...
          </p>
        </div>
      </div>
    )
  }

  if (status === 'error') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="w-full max-w-md p-8 bg-card border rounded-lg shadow-lg text-center">
          <XCircle className="w-16 h-16 mx-auto mb-4 text-red-500" />
          <h1 className="text-2xl font-bold mb-4">Ошибка</h1>
          <p className="text-muted-foreground mb-6">{message}</p>
          <Link
            to="/password-reset-request"
            className="text-primary hover:underline"
          >
            Запросить новую ссылку
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="w-full max-w-md p-8 bg-card border rounded-lg shadow-lg">
        <h1 className="text-2xl font-bold mb-6 text-center">Новый пароль</h1>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="password" className="block text-sm font-medium mb-2">
              Новый пароль
            </label>
            <input
              id="password"
              type="password"
              required
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              minLength={8}
            />
            <p className="text-xs text-muted-foreground mt-1">
              Минимум 8 символов
            </p>
          </div>

          <div>
            <label htmlFor="password_confirm" className="block text-sm font-medium mb-2">
              Подтвердите пароль
            </label>
            <input
              id="password_confirm"
              type="password"
              required
              value={formData.password_confirm}
              onChange={(e) => setFormData({ ...formData, password_confirm: e.target.value })}
              className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              minLength={8}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 flex items-center justify-center"
          >
            {loading ? (
              <>
                <Loader className="w-4 h-4 mr-2 animate-spin" />
                Сохранение...
              </>
            ) : (
              'Изменить пароль'
            )}
          </button>
        </form>

        <p className="mt-4 text-center text-sm text-muted-foreground">
          <Link to="/login" className="text-primary hover:underline">
            Вернуться на страницу входа
          </Link>
        </p>
      </div>
    </div>
  )
}

