import { useState, useEffect, useRef } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import api from '@/lib/api'
import toast from 'react-hot-toast'

// Custom debounce hook
function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value)
  const timeoutRef = useRef<ReturnType<typeof setTimeout>>()

  useEffect(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }

    timeoutRef.current = setTimeout(() => {
      setDebouncedValue(value)
    }, delay)

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [value, delay])

  return debouncedValue
}

interface FieldErrors {
  invite_token?: string
  email?: string
  username?: string
  password?: string
  password_confirm?: string
}

export default function RegisterPage() {
  const navigate = useNavigate()
  const { setAuth } = useAuthStore()
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    password: '',
    password_confirm: '',
    invite_token: '',
    first_name: '',
    last_name: '',
  })
  const [errors, setErrors] = useState<FieldErrors>({})
  const [loading, setLoading] = useState(false)
  const [checking, setChecking] = useState({
    email: false,
    username: false,
    invite_token: false,
  })

  // Debounced values for API checks
  const debouncedEmail = useDebounce(formData.email, 500)
  const debouncedUsername = useDebounce(formData.username, 500)
  const debouncedInviteToken = useDebounce(formData.invite_token, 500)

  // Validate password strength
  const validatePassword = (password: string): string | undefined => {
    if (!password) return undefined
    
    if (password.length < 8) {
      return 'Пароль должен содержать минимум 8 символов'
    }
    
    if (!/[A-ZА-Я]/.test(password)) {
      return 'Пароль должен содержать хотя бы одну заглавную букву'
    }
    
    if (!/[a-zа-я]/.test(password)) {
      return 'Пароль должен содержать хотя бы одну строчную букву'
    }
    
    if (!/[0-9]/.test(password)) {
      return 'Пароль должен содержать хотя бы одну цифру'
    }
    
    if (!/[^A-Za-zА-Яа-я0-9]/.test(password)) {
      return 'Пароль должен содержать хотя бы один специальный символ (!@#$%^&* и т.д.)'
    }
    
    return undefined
  }

  // Check email availability
  useEffect(() => {
    const checkEmail = async () => {
      if (!debouncedEmail) {
        setErrors(prev => ({ ...prev, email: undefined }))
        return
      }

      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
      if (!emailRegex.test(debouncedEmail)) {
        setErrors(prev => ({ ...prev, email: 'Некорректный формат email' }))
        return
      }

      setChecking(prev => ({ ...prev, email: true }))
      try {
        const response = await api.get(`/auth/check/email/?email=${encodeURIComponent(debouncedEmail)}`)
        if (!response.data.available) {
          setErrors(prev => ({ ...prev, email: 'Этот email уже используется' }))
        } else {
          setErrors(prev => ({ ...prev, email: undefined }))
        }
      } catch (error: any) {
        console.error('Email check error:', error)
      } finally {
        setChecking(prev => ({ ...prev, email: false }))
      }
    }

    checkEmail()
  }, [debouncedEmail])

  // Check username availability
  useEffect(() => {
    const checkUsername = async () => {
      if (!debouncedUsername) {
        setErrors(prev => ({ ...prev, username: undefined }))
        return
      }

      if (debouncedUsername.length < 3) {
        setErrors(prev => ({ ...prev, username: 'Имя пользователя должно содержать минимум 3 символа' }))
        return
      }

      if (!/^[a-zA-Z0-9_]+$/.test(debouncedUsername)) {
        setErrors(prev => ({ ...prev, username: 'Имя пользователя может содержать только буквы, цифры и подчеркивание' }))
        return
      }

      setChecking(prev => ({ ...prev, username: true }))
      try {
        const response = await api.get(`/auth/check/username/?username=${encodeURIComponent(debouncedUsername)}`)
        if (!response.data.available) {
          setErrors(prev => ({ ...prev, username: 'Это имя пользователя уже занято' }))
        } else {
          setErrors(prev => ({ ...prev, username: undefined }))
        }
      } catch (error: any) {
        console.error('Username check error:', error)
      } finally {
        setChecking(prev => ({ ...prev, username: false }))
      }
    }

    checkUsername()
  }, [debouncedUsername])

  // Check invite token validity
  useEffect(() => {
    const checkToken = async () => {
      if (!debouncedInviteToken) {
        setErrors(prev => ({ ...prev, invite_token: undefined }))
        return
      }

      setChecking(prev => ({ ...prev, invite_token: true }))
      try {
        const response = await api.get(`/auth/check/invite-token/?token=${encodeURIComponent(debouncedInviteToken)}`)
        if (!response.data.valid) {
          setErrors(prev => ({ ...prev, invite_token: response.data.error || 'Недействительный или уже использованный токен' }))
        } else {
          setErrors(prev => ({ ...prev, invite_token: undefined }))
        }
      } catch (error: any) {
        console.error('Token check error:', error)
        setErrors(prev => ({ ...prev, invite_token: 'Ошибка проверки токена' }))
      } finally {
        setChecking(prev => ({ ...prev, invite_token: false }))
      }
    }

    checkToken()
  }, [debouncedInviteToken])

  // Validate password on change
  useEffect(() => {
    if (formData.password) {
      const passwordError = validatePassword(formData.password)
      setErrors(prev => ({ ...prev, password: passwordError }))
    } else {
      setErrors(prev => ({ ...prev, password: undefined }))
    }
  }, [formData.password])

  // Validate password confirmation
  useEffect(() => {
    if (formData.password_confirm) {
      if (formData.password !== formData.password_confirm) {
        setErrors(prev => ({ ...prev, password_confirm: 'Пароли не совпадают' }))
      } else {
        setErrors(prev => ({ ...prev, password_confirm: undefined }))
      }
    } else {
      setErrors(prev => ({ ...prev, password_confirm: undefined }))
    }
  }, [formData.password, formData.password_confirm])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    // Final validation
    const hasErrors = Object.values(errors).some(error => error !== undefined)
    if (hasErrors) {
      toast.error('Исправьте ошибки в форме')
      setLoading(false)
      return
    }

    if (formData.password !== formData.password_confirm) {
      setErrors(prev => ({ ...prev, password_confirm: 'Пароли не совпадают' }))
      setLoading(false)
      return
    }

    try {
      const response = await api.post('/auth/register/', formData)
      const { access, refresh, user } = response.data
      
      setAuth(user, access, refresh)
      toast.success('Регистрация успешна! Проверьте email для подтверждения.')
      toast('⚠️ Не забудьте проверить папку "Спам", если письмо не пришло', {
        icon: '📧',
        duration: 6000,
      })
      
      // Redirect to dashboard immediately after registration
      setTimeout(() => {
        navigate('/')
      }, 1000)
    } catch (error: any) {
      console.error('Registration error:', error.response?.data)
      
      // Extract error messages from validation errors
      const errorData = error.response?.data || {}
      const newErrors: FieldErrors = {}
      
      if (errorData.invite_token) {
        newErrors.invite_token = Array.isArray(errorData.invite_token) 
          ? errorData.invite_token[0] 
          : errorData.invite_token
      }
      if (errorData.email) {
        newErrors.email = Array.isArray(errorData.email) 
          ? errorData.email[0] 
          : errorData.email
      }
      if (errorData.password) {
        newErrors.password = Array.isArray(errorData.password) 
          ? errorData.password[0] 
          : errorData.password
      }
      if (errorData.username) {
        newErrors.username = Array.isArray(errorData.username) 
          ? errorData.username[0] 
          : errorData.username
      }
      
      setErrors(newErrors)
      
      const errorMessage = Object.values(newErrors)[0] || errorData.error || 'Ошибка регистрации'
      toast.error(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const getFieldClassName = (fieldError?: string, checking?: boolean) => {
    let baseClass = "w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
    if (fieldError) {
      baseClass += " border-red-500 focus:ring-red-500"
    } else if (checking) {
      baseClass += " border-yellow-500"
    }
    return baseClass
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="w-full max-w-md p-8 bg-card border rounded-lg shadow-lg">
        <h1 className="text-2xl font-bold mb-6 text-center">Регистрация</h1>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="invite_token" className="block text-sm font-medium mb-2">
              Инвайт-токен *
            </label>
            <input
              id="invite_token"
              type="text"
              required
              value={formData.invite_token}
              onChange={(e) => setFormData({ ...formData, invite_token: e.target.value })}
              className={getFieldClassName(errors.invite_token, checking.invite_token)}
              placeholder="Введите инвайт-токен"
            />
            {checking.invite_token && (
              <p className="text-xs text-yellow-600 mt-1">Проверка токена...</p>
            )}
            {errors.invite_token && !checking.invite_token && (
              <p className="text-xs text-red-600 mt-1">{errors.invite_token}</p>
            )}
          </div>

          <div>
            <label htmlFor="email" className="block text-sm font-medium mb-2">
              Email *
            </label>
            <input
              id="email"
              type="email"
              required
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className={getFieldClassName(errors.email, checking.email)}
            />
            {checking.email && (
              <p className="text-xs text-yellow-600 mt-1">Проверка email...</p>
            )}
            {errors.email && !checking.email && (
              <p className="text-xs text-red-600 mt-1">{errors.email}</p>
            )}
          </div>

          <div>
            <label htmlFor="username" className="block text-sm font-medium mb-2">
              Имя пользователя *
            </label>
            <input
              id="username"
              type="text"
              required
              value={formData.username}
              onChange={(e) => setFormData({ ...formData, username: e.target.value })}
              className={getFieldClassName(errors.username, checking.username)}
            />
            {checking.username && (
              <p className="text-xs text-yellow-600 mt-1">Проверка имени пользователя...</p>
            )}
            {errors.username && !checking.username && (
              <p className="text-xs text-red-600 mt-1">{errors.username}</p>
            )}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="first_name" className="block text-sm font-medium mb-2">
                Имя
              </label>
              <input
                id="first_name"
                type="text"
                value={formData.first_name}
                onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>

            <div>
              <label htmlFor="last_name" className="block text-sm font-medium mb-2">
                Фамилия
              </label>
              <input
                id="last_name"
                type="text"
                value={formData.last_name}
                onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium mb-2">
              Пароль *
            </label>
            <input
              id="password"
              type="password"
              required
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              className={getFieldClassName(errors.password)}
            />
            {errors.password && (
              <p className="text-xs text-red-600 mt-1">{errors.password}</p>
            )}
            {!errors.password && formData.password && (
              <p className="text-xs text-green-600 mt-1">✓ Пароль соответствует требованиям</p>
            )}
          </div>

          <div>
            <label htmlFor="password_confirm" className="block text-sm font-medium mb-2">
              Подтверждение пароля *
            </label>
            <input
              id="password_confirm"
              type="password"
              required
              value={formData.password_confirm}
              onChange={(e) => setFormData({ ...formData, password_confirm: e.target.value })}
              className={getFieldClassName(errors.password_confirm)}
            />
            {errors.password_confirm && (
              <p className="text-xs text-red-600 mt-1">{errors.password_confirm}</p>
            )}
            {!errors.password_confirm && formData.password_confirm && formData.password === formData.password_confirm && (
              <p className="text-xs text-green-600 mt-1">✓ Пароли совпадают</p>
            )}
          </div>

          <button
            type="submit"
            disabled={loading || Object.values(errors).some(error => error !== undefined)}
            className="w-full py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Регистрация...' : 'Зарегистрироваться'}
          </button>
        </form>

        <p className="mt-4 text-center text-sm text-muted-foreground">
          Уже есть аккаунт?{' '}
          <Link to="/login" className="text-primary hover:underline">
            Войти
          </Link>
        </p>
      </div>
    </div>
  )
}
