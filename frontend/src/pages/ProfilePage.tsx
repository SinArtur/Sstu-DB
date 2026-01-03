import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuthStore } from '@/store/authStore'
import api from '@/lib/api'
import toast from 'react-hot-toast'
import { Mail, CheckCircle, XCircle } from 'lucide-react'
import InviteTokens from '@/components/InviteTokens'

export default function ProfilePage() {
  const { user } = useAuthStore()
  const queryClient = useQueryClient()

  const { data: myMaterials } = useQuery({
    queryKey: ['my-materials'],
    queryFn: async () => {
      const res = await api.get('/materials/?my_materials=true')
      return res.data.results || res.data
    },
  })

  const resendVerificationMutation = useMutation({
    mutationFn: async () => {
      const res = await api.post('/auth/resend-verification/')
      return res.data
    },
    onSuccess: (data: any) => {
      toast.success(data.message || 'Письмо отправлено на ваш email')
      toast('⚠️ Не забудьте проверить папку "Спам", если письмо не пришло', {
        icon: '📧',
        duration: 6000,
      })
      if (data.verification_url) {
        console.log('Verification URL (for development):', data.verification_url)
      }
      // Refresh user data
      queryClient.invalidateQueries({ queryKey: ['profile'] })
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error || 'Ошибка отправки письма')
    },
  })

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">Профиль</h1>

      <div className="grid md:grid-cols-2 gap-6">
        <div className="bg-card border rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Информация</h2>
          <div className="space-y-2">
            <p>
              <span className="text-muted-foreground">Email:</span> {user?.email}
            </p>
            <p>
              <span className="text-muted-foreground">Имя пользователя:</span> {user?.username}
            </p>
            <p>
              <span className="text-muted-foreground">Роль:</span> {user?.role_display}
            </p>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-muted-foreground">Email подтвержден:</span>
                {user?.is_email_verified ? (
                  <div className="flex items-center gap-1 text-green-600">
                    <CheckCircle className="h-4 w-4" />
                    <span>Да</span>
                  </div>
                ) : (
                  <div className="flex items-center gap-1 text-yellow-600">
                    <XCircle className="h-4 w-4" />
                    <span>Нет</span>
                  </div>
                )}
              </div>
              {!user?.is_email_verified && (
                <button
                  onClick={() => resendVerificationMutation.mutate()}
                  disabled={resendVerificationMutation.isPending}
                  className="flex items-center gap-2 px-3 py-1 text-sm bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50"
                >
                  <Mail className="h-4 w-4" />
                  {resendVerificationMutation.isPending ? 'Отправка...' : 'Отправить письмо'}
                </button>
              )}
            </div>
          </div>
        </div>

        <div className="bg-card border rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Статистика</h2>
          <div className="space-y-2">
            <p>
              <span className="text-muted-foreground">Загружено материалов:</span>{' '}
              {myMaterials?.length || 0}
            </p>
          </div>
        </div>
      </div>

      <div className="mt-6">
        <InviteTokens />
      </div>

      <div className="mt-6 bg-card border rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Мои материалы</h2>
        {myMaterials && myMaterials.length > 0 ? (
          <div className="space-y-2">
            {myMaterials.map((material: any) => (
              <div key={material.id} className="p-4 border rounded-lg">
                <p className="font-medium">{material.branch_path}</p>
                <p className="text-sm text-muted-foreground">{material.description}</p>
                <p className="text-xs text-muted-foreground mt-2">
                  Статус: {material.status_display}
                </p>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-muted-foreground">Материалы не загружены</p>
        )}
      </div>
    </div>
  )
}

