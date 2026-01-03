import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import toast from 'react-hot-toast'
import { X, Check, Download, FileText } from 'lucide-react'
import { formatFileSize, formatDate } from '@/lib/utils'

interface MaterialModerationModalProps {
  material: any
  onClose: () => void
  onSuccess: () => void
}

export default function MaterialModerationModal({
  material,
  onClose,
  onSuccess,
}: MaterialModerationModalProps) {
  const [comment, setComment] = useState('')
  const queryClient = useQueryClient()

  const approveMutation = useMutation({
    mutationFn: async () => {
      const res = await api.post(`/materials/${material.id}/approve/`, { comment })
      return res.data
    },
    onSuccess: () => {
      toast.success('Материал одобрен')
      queryClient.invalidateQueries({ queryKey: ['moderation-pending'] })
      queryClient.invalidateQueries({ queryKey: ['materials'] })
      onSuccess()
      onClose()
    },
    onError: (error: any) => {
      const errorMessage = error.response?.data?.error || 'Ошибка одобрения материала'
      toast.error(errorMessage)
    },
  })

  const rejectMutation = useMutation({
    mutationFn: async () => {
      if (!comment.trim()) {
        toast.error('Введите комментарий отклонения')
        return
      }
      const res = await api.post(`/materials/${material.id}/reject/`, { comment })
      return res.data
    },
    onSuccess: () => {
      toast.success('Материал отклонен')
      queryClient.invalidateQueries({ queryKey: ['moderation-pending'] })
      queryClient.invalidateQueries({ queryKey: ['materials'] })
      onSuccess()
      onClose()
    },
    onError: (error: any) => {
      const errorMessage = error.response?.data?.error || 'Ошибка отклонения материала'
      toast.error(errorMessage)
    },
  })

  const handleDownload = async (fileName: string, fileId: number) => {
    try {
      // Use fetch for blob download to avoid axios issues
      const { useAuthStore } = await import('@/store/authStore')
      const { accessToken } = useAuthStore.getState()
      const response = await fetch(`/api/materials/${material.id}/files/${fileId}/download/`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
        },
      })
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.error || 'Ошибка скачивания файла')
      }
      
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = fileName
      link.style.display = 'none'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      
      toast.success('Файл скачан')
    } catch (error: any) {
      console.error('Download error:', error)
      const errorMessage = error.message || 'Ошибка скачивания файла'
      toast.error(errorMessage)
    }
  }


  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-card border rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-card border-b p-6 flex items-center justify-between">
          <h2 className="text-xl font-semibold">Модерация материала</h2>
          <button onClick={onClose} className="p-1 hover:bg-accent rounded">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Material Info */}
          <div>
            <h3 className="font-semibold mb-2">Информация о материале</h3>
            <div className="bg-muted rounded-lg p-4 space-y-2">
              <p>
                <span className="font-medium">Ветка:</span> {material.branch_path}
              </p>
              <p>
                <span className="font-medium">Автор:</span> {material.author_email}
              </p>
              <p>
                <span className="font-medium">Дата загрузки:</span> {formatDate(material.created_at)}
              </p>
              {material.description && (
                <div>
                  <span className="font-medium">Описание:</span>
                  <div className="mt-2 bg-muted/50 rounded-lg p-3 border-l-4 border-primary">
                    <p className="text-base font-medium text-foreground leading-relaxed">{material.description}</p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Files */}
          {material.files && material.files.length > 0 && (
            <div>
              <h3 className="font-semibold mb-3">Файлы ({material.files.length})</h3>
              <div className="space-y-3">
                {material.files.map((file: any) => (
                  <div
                    key={file.id}
                    className="border rounded-lg p-4 hover:bg-muted/50 transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-3 flex-1">
                        <FileText className="h-5 w-5 text-primary mt-0.5 flex-shrink-0" />
                        <div className="flex-1">
                          <p className="font-medium">{file.original_name}</p>
                          <div className="flex items-center gap-4 text-sm text-muted-foreground mt-1">
                            <span>{formatFileSize(file.file_size)}</span>
                            <span className="uppercase">{file.file_type}</span>
                          </div>
                          {file.comment && (
                            <p className="text-sm text-muted-foreground mt-2">
                              Комментарий: {file.comment}
                            </p>
                          )}
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleDownload(file.original_name, file.id)}
                          className="p-2 hover:bg-accent rounded"
                          title="Скачать файл"
                        >
                          <Download className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Tags */}
          {material.tags && material.tags.length > 0 && (
            <div>
              <h3 className="font-semibold mb-2">Теги</h3>
              <div className="flex flex-wrap gap-2">
                {material.tags.map((tag: any) => (
                  <span
                    key={tag.id}
                    className="px-2 py-1 bg-muted rounded text-sm"
                  >
                    {tag.name}
                  </span>
                ))}
              </div>
            </div>
          )}

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
