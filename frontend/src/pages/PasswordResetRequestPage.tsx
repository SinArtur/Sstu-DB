import { useState } from 'react'
import { Link } from 'react-router-dom'
import api from '@/lib/api'
import toast from 'react-hot-toast'
import { Mail } from 'lucide-react'

export default function PasswordResetRequestPage() {
  const [formData, setFormData] = useState({
    email: '',
  })
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      const response = await api.post('/auth/password-reset-request/', formData)
      toast.success(response.data.message || 'Письмо отправлено на ваш email')
      toast('⚠️ Не забудьте проверить папку "Спам", если письмо не пришло', {
        icon: '📧',
        duration: 6000,
      })
      setSuccess(true)
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Ошибка отправки запроса')
    } finally {
      setLoading(false)
    }
  }

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="w-full max-w-md p-8 bg-card border rounded-lg shadow-lg text-center">
          <Mail className="w-16 h-16 mx-auto mb-4 text-green-500" />
          <h1 className="text-2xl font-bold mb-4">Письмо отправлено</h1>
          <p className="text-muted-foreground mb-4">
            Если указанный email зарегистрирован и подтвержден, письмо с инструкциями отправлено.
          </p>
          <p className="text-sm text-muted-foreground mb-6">
            ⚠️ Не забудьте проверить папку "Спам", если письмо не пришло в течение нескольких минут.
          </p>
          <Link
            to="/login"
            className="text-primary hover:underline"
          >
            Вернуться на страницу входа
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="w-full max-w-md p-8 bg-card border rounded-lg shadow-lg">
        <h1 className="text-2xl font-bold mb-6 text-center">Восстановление пароля</h1>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="email" className="block text-sm font-medium mb-2">
              Email
            </label>
            <input
              id="email"
              type="email"
              required
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="your@email.com"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50"
          >
            {loading ? 'Отправка...' : 'Отправить инструкции'}
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

