import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuthStore } from '@/store/authStore'
import api, { scheduleApi } from '@/lib/api'
import toast from 'react-hot-toast'
import { Mail, CheckCircle, XCircle, Calendar } from 'lucide-react'
import InviteTokens from '@/components/InviteTokens'
import { useState } from 'react'

export default function ProfilePage() {
  const { user, setAuth } = useAuthStore()
  const queryClient = useQueryClient()
  const [selectedInstitute, setSelectedInstitute] = useState<number | null>(null)
  const [selectedGroup, setSelectedGroup] = useState<number | null>(user?.group || null)

  const { data: myMaterials } = useQuery({
    queryKey: ['my-materials'],
    queryFn: async () => {
      const res = await api.get('/materials/?my_materials=true')
      return res.data.results || res.data
    },
  })

  const { data: institutes } = useQuery({
    queryKey: ['institutes'],
    queryFn: async () => {
      const res = await scheduleApi.getInstitutes()
      return res.data.results || res.data
    },
  })

  const { data: groups } = useQuery({
    queryKey: ['groups', selectedInstitute],
    queryFn: async () => {
      if (!selectedInstitute) return []
      const res = await scheduleApi.getGroups({ institute: selectedInstitute })
      return res.data.results || res.data
    },
    enabled: !!selectedInstitute,
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

  const updateGroupMutation = useMutation({
    mutationFn: async (groupId: number | null) => {
      const res = await api.patch('/auth/profile/', { group: groupId })
      return res.data
    },
    onSuccess: (data: any) => {
      toast.success('Группа успешно обновлена')
      // Update auth store
      if (user) {
        setAuth(data, useAuthStore.getState().accessToken!, useAuthStore.getState().refreshToken!)
      }
      queryClient.invalidateQueries({ queryKey: ['profile'] })
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error || 'Ошибка обновления группы')
    },
  })

  const handleUpdateGroup = () => {
    if (selectedGroup) {
      updateGroupMutation.mutate(selectedGroup)
    }
  }

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
            <p>
              <span className="text-muted-foreground">Группа:</span> {user?.group_name || 'Не указана'}
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

      <div className="mt-6 bg-card border rounded-lg p-6">
        <div className="flex items-center gap-2 mb-4">
          <Calendar className="h-5 w-5 text-primary" />
          <h2 className="text-xl font-semibold">Моя группа</h2>
        </div>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">Институт</label>
            <select
              value={selectedInstitute || ''}
              onChange={(e) => {
                setSelectedInstitute(e.target.value ? Number(e.target.value) : null)
                setSelectedGroup(null)
              }}
              className="w-full px-3 py-2 bg-background border rounded-lg focus:ring-2 focus:ring-primary"
            >
              <option value="">Выберите институт</option>
              {institutes?.map((institute: any) => (
                <option key={institute.id} value={institute.id}>
                  {institute.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Группа</label>
            <select
              value={selectedGroup || ''}
              onChange={(e) => setSelectedGroup(e.target.value ? Number(e.target.value) : null)}
              className="w-full px-3 py-2 bg-background border rounded-lg focus:ring-2 focus:ring-primary"
              disabled={!selectedInstitute}
            >
              <option value="">Выберите группу</option>
              {groups?.map((group: any) => (
                <option key={group.id} value={group.id}>
                  {group.name}
                </option>
              ))}
            </select>
          </div>
          <button
            onClick={handleUpdateGroup}
            disabled={!selectedGroup || updateGroupMutation.isPending}
            className="w-full px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 transition-colors"
          >
            {updateGroupMutation.isPending ? 'Сохранение...' : 'Сохранить группу'}
          </button>
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

