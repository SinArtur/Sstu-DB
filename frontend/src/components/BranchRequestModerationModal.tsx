import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import toast from 'react-hot-toast'
import { X, Check } from 'lucide-react'
import { formatDate } from '@/lib/utils'

interface BranchRequestModerationModalProps {
  request: any
  onClose: () => void
  onSuccess: () => void
}

export default function BranchRequestModerationModal({
  request,
  onClose,
  onSuccess,
}: BranchRequestModerationModalProps) {
  const [comment, setComment] = useState('')
  const queryClient = useQueryClient()

  const approveMutation = useMutation({
    mutationFn: async () => {
      const res = await api.post(`/branches/requests/${request.id}/approve/`, { comment })
      return res.data
    },
    onSuccess: () => {
      toast.success('Запрос одобрен')
      queryClient.invalidateQueries({ queryKey: ['moderation-pending'] })
      queryClient.invalidateQueries({ queryKey: ['branches-tree'] })
      queryClient.invalidateQueries({ queryKey: ['branches-for-request'] })
      onSuccess()
      onClose()
    },
    onError: (error: any) => {
      const errorMessage = error.response?.data?.error || 'Ошибка одобрения запроса'
      toast.error(errorMessage)
    },
  })

  const rejectMutation = useMutation({
    mutationFn: async () => {
      if (!comment.trim()) {
        toast.error('Введите комментарий отклонения')
        return
      }
      const res = await api.post(`/branches/requests/${request.id}/reject/`, { comment })
      return res.data
    },
    onSuccess: () => {
      toast.success('Запрос отклонен')
      queryClient.invalidateQueries({ queryKey: ['moderation-pending'] })
      onSuccess()
      onClose()
    },
    onError: (error: any) => {
      const errorMessage = error.response?.data?.error || 'Ошибка отклонения запроса'
      toast.error(errorMessage)
    },
  })

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-card border rounded-lg max-w-2xl w-full">
        <div className="p-6 border-b flex items-center justify-between">
          <h2 className="text-xl font-semibold">Модерация запроса на ветку</h2>
          <button onClick={onClose} className="p-1 hover:bg-accent rounded">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Request Info */}
          <div>
            <h3 className="font-semibold mb-2">Информация о запросе</h3>
            <div className="bg-muted rounded-lg p-4 space-y-2">
              <p>
                <span className="font-medium">Название новой ветки:</span> {request.name}
              </p>
              <p>
                <span className="font-medium">Родительская ветка:</span> {request.parent_path}
              </p>
              <p>
                <span className="font-medium">Запросил:</span> {request.requester_email}
              </p>
              <p>
                <span className="font-medium">Дата запроса:</span> {formatDate(request.created_at)}
              </p>
            </div>
          </div>

          {/* Comment */}
          <div>
            <label className="block text-sm font-medium mb-2">
              Комментарий модератора
            </label>
            <textarea
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder="Введите комментарий (опционально для одобрения, обязательно для отклонения)"
              className="w-full px-3 py-2 border rounded-lg bg-background min-h-[100px]"
            />
          </div>

          {/* Actions */}
          <div className="flex gap-2 justify-end pt-4 border-t">
            <button
              onClick={onClose}
              className="px-4 py-2 border rounded-lg hover:bg-accent"
            >
              Отмена
            </button>
            <button
              onClick={() => rejectMutation.mutate()}
              disabled={rejectMutation.isPending || !comment.trim()}
              className="flex items-center gap-2 px-4 py-2 bg-destructive text-destructive-foreground rounded-lg hover:bg-destructive/90 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <X className="h-4 w-4" />
              {rejectMutation.isPending ? 'Отклонение...' : 'Отклонить'}
            </button>
            <button
              onClick={() => approveMutation.mutate()}
              disabled={approveMutation.isPending}
              className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Check className="h-4 w-4" />
              {approveMutation.isPending ? 'Одобрение...' : 'Одобрить'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
