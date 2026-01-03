import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import toast from 'react-hot-toast'
import { Copy, Plus, Trash2, CheckCircle2, XCircle } from 'lucide-react'
import { useAuthStore } from '@/store/authStore'

export default function InviteTokens() {
  const queryClient = useQueryClient()
  const { user } = useAuthStore()

  const { data: tokens } = useQuery({
    queryKey: ['invite-tokens'],
    queryFn: async () => {
      const res = await api.get('/auth/invite/my/')
      return res.data
    },
  })

  const generateMutation = useMutation({
    mutationFn: async (count: number) => {
      const res = await api.post('/auth/invite/generate/', { count })
      return res.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invite-tokens'] })
      toast.success('Токены созданы')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error || 'Ошибка создания токенов')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: async (tokenId: number) => {
      await api.delete(`/auth/invite/${tokenId}/delete/`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invite-tokens'] })
      toast.success('Токен удален')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error || 'Ошибка удаления токена')
    },
  })

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    toast.success('Токен скопирован')
  }

  const handleDelete = (tokenId: number) => {
    if (confirm('Вы уверены, что хотите удалить этот токен?')) {
      deleteMutation.mutate(tokenId)
    }
  }

  return (
    <div className="bg-card border rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-xl font-semibold">Мои инвайт-токены</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Используйте токены для приглашения друзей в систему
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => {
              const count = prompt('Сколько токенов создать?', '1')
              if (count) {
                generateMutation.mutate(parseInt(count) || 1)
              }
            }}
            disabled={generateMutation.isPending}
            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50"
          >
            <Plus className="h-4 w-4" />
            Создать токены
          </button>
        </div>
      </div>

      {tokens && tokens.length > 0 ? (
        <div className="space-y-6">
          {/* Активные токены */}
          {tokens.filter((t: any) => !t.used).length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-3">
                <CheckCircle2 className="h-5 w-5 text-green-500" />
                <h3 className="font-semibold text-green-600 dark:text-green-400">
                  Активные токены ({tokens.filter((t: any) => !t.used).length})
                </h3>
              </div>
              <div className="space-y-2">
                {tokens
                  .filter((token: any) => !token.used)
                  .map((token: any) => (
                    <div
                      key={token.id}
                      className="flex items-center justify-between p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg hover:bg-green-100 dark:hover:bg-green-900/30 transition-colors"
                    >
                      <div className="flex items-center gap-3 flex-1">
                        <CheckCircle2 className="h-5 w-5 text-green-500 flex-shrink-0" />
                        <div className="flex-1 min-w-0">
                          <code className="text-sm font-mono break-all">{token.code}</code>
                          <p className="text-xs text-muted-foreground mt-1">
                            Создан {new Date(token.created_at).toLocaleDateString('ru-RU')}
                          </p>
                        </div>
                      </div>
                      <div className="flex gap-2 ml-2">
                        <button
                          onClick={() => copyToClipboard(token.code)}
                          className="p-2 hover:bg-green-200 dark:hover:bg-green-800 rounded"
                          title="Скопировать токен"
                        >
                          <Copy className="h-4 w-4" />
                        </button>
                        {user?.role === 'admin' && (
                          <button
                            onClick={() => handleDelete(token.id)}
                            className="p-2 hover:bg-destructive/10 text-destructive rounded"
                            title="Удалить токен"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          )}

          {/* Использованные токены */}
          {tokens.filter((t: any) => t.used).length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-3">
                <XCircle className="h-5 w-5 text-gray-400" />
                <h3 className="font-semibold text-gray-500 dark:text-gray-400">
                  Использованные токены ({tokens.filter((t: any) => t.used).length})
                </h3>
              </div>
              <div className="space-y-2">
                {tokens
                  .filter((token: any) => token.used)
                  .map((token: any) => (
                    <div
                      key={token.id}
                      className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700 rounded-lg opacity-75"
                    >
                      <div className="flex items-center gap-3 flex-1">
                        <XCircle className="h-5 w-5 text-gray-400 flex-shrink-0" />
                        <div className="flex-1 min-w-0">
                          <code className="text-sm font-mono break-all text-gray-500 dark:text-gray-400 line-through">
                            {token.code}
                          </code>
                          <p className="text-xs text-muted-foreground mt-1">
                            {token.used_by_email && (
                              <>Использован пользователем {token.used_by_email}</>
                            )}
                            {token.used_at && (
                              <> • {new Date(token.used_at).toLocaleDateString('ru-RU')}</>
                            )}
                          </p>
                        </div>
                      </div>
                      <div className="flex gap-2 ml-2">
                        <button
                          onClick={() => copyToClipboard(token.code)}
                          className="p-2 hover:bg-gray-200 dark:hover:bg-gray-700 rounded opacity-50"
                          title="Скопировать токен (неактивен)"
                          disabled
                        >
                          <Copy className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          )}

          {tokens.filter((t: any) => !t.used).length === 0 && (
            <div className="text-center py-8">
              <p className="text-muted-foreground mb-4">Нет активных токенов</p>
              <p className="text-sm text-muted-foreground">
                Создайте токены, чтобы пригласить друзей в систему
              </p>
            </div>
          )}
        </div>
      ) : (
        <div className="text-center py-8">
          <p className="text-muted-foreground mb-4">Нет токенов</p>
          <p className="text-sm text-muted-foreground">
            Создайте токены, чтобы пригласить друзей в систему
          </p>
        </div>
      )}
    </div>
  )
}

