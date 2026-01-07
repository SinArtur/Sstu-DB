import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import toast from 'react-hot-toast'
import { X, Star, Download, Eye, MessageSquare, Send } from 'lucide-react'
import { formatDate, formatFileSize } from '@/lib/utils'

interface MaterialViewModalProps {
  material: any
  onClose: () => void
}

export default function MaterialViewModal({ material, onClose }: MaterialViewModalProps) {
  const [commentText, setCommentText] = useState('')
  const queryClient = useQueryClient()

  const { data: materialDetails, isLoading } = useQuery({
    queryKey: ['material', material.id],
    queryFn: async () => {
      const res = await api.get(`/materials/${material.id}/`)
      return res.data
    },
    enabled: !!material.id,
  })

  const { data: comments } = useQuery({
    queryKey: ['material-comments', material.id],
    queryFn: async () => {
      const res = await api.get(`/materials/${material.id}/comments/`)
      return res.data || []
    },
    enabled: !!material.id,
  })

  const commentMutation = useMutation({
    mutationFn: async (text: string) => {
      const res = await api.post('/materials/comments/', {
        material: material.id,
        text: text,
      })
      return res.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['material-comments', material.id] })
      queryClient.invalidateQueries({ queryKey: ['material', material.id] })
      setCommentText('')
      toast.success('Комментарий добавлен')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error || 'Ошибка добавления комментария')
    },
  })

  const rateMutation = useMutation({
    mutationFn: async (value: number) => {
      const res = await api.post(`/materials/${material.id}/rate/`, { value })
      return res.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['material', material.id] })
      queryClient.invalidateQueries({ queryKey: ['materials'] })
      toast.success('Оценка сохранена')
    },
  })

  const handleDownload = async (fileName: string, fileId: number) => {
    try {
      // Increment download count first
      await api.post(`/materials/${material.id}/download/`)

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


  const handleSubmitComment = (e: React.FormEvent) => {
    e.preventDefault()
    if (!commentText.trim()) {
      toast.error('Введите текст комментария')
      return
    }
    commentMutation.mutate(commentText.trim())
  }

  const safeNumber = (value: any): number => {
    if (typeof value === 'number' && !isNaN(value)) return value
    const parsed = parseFloat(value)
    return isNaN(parsed) ? 0 : parsed
  }

  const materialData = materialDetails || material
  const averageRating = safeNumber(materialData?.average_rating)
  const userRating = materialData?.user_rating
  const currentRating = userRating || 0

  if (isLoading) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-card border rounded-lg p-6">
          <p>Загрузка...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 overflow-y-auto">
      <div className="bg-card border rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto my-4">
        <div className="sticky top-0 bg-card border-b p-6 flex items-center justify-between">
          <h2 className="text-xl font-semibold">
            {materialData?.branch_path || materialData?.branch_name || 'Материал'}
          </h2>
          <button onClick={onClose} className="p-1 hover:bg-accent rounded">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Material Info */}
          <div>
            <div className="flex items-start justify-between mb-4">
              <div className="flex-1">
                <h3 className="text-lg font-semibold mb-2">
                  {materialData?.branch_path || materialData?.branch_name}
                </h3>
                {materialData?.description && (
                  <p className="text-muted-foreground mb-4">{materialData.description}</p>
                )}
                <div className="flex items-center gap-4 text-sm text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <Eye className="h-4 w-4" />
                    {safeNumber(materialData?.views_count)}
                  </span>
                  <span className="flex items-center gap-1">
                    <Download className="h-4 w-4" />
                    {safeNumber(materialData?.downloads_count)}
                  </span>
                  <span className="flex items-center gap-1">
                    <MessageSquare className="h-4 w-4" />
                    {safeNumber(materialData?.comments_count)}
                  </span>
                  {materialData?.created_at && (
                    <span>{formatDate(materialData.created_at)}</span>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <div className="flex items-center gap-1">
                  <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                  <span className="text-sm font-medium">
                    {isNaN(averageRating) ? '0.0' : averageRating.toFixed(1)}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    ({safeNumber(materialData?.ratings_count)})
                  </span>
                </div>
              </div>
            </div>

            {/* Rating */}
            <div className="mb-4">
              <p className="text-sm font-medium mb-2">Оценить материал:</p>
              <div className="flex items-center gap-1">
                {[1, 2, 3, 4, 5].map((value) => (
                  <button
                    key={value}
                    onClick={() => rateMutation.mutate(value)}
                    className={`p-1 transition-colors ${
                      value <= currentRating
                        ? 'text-yellow-400'
                        : 'text-muted-foreground hover:text-yellow-400'
                    }`}
                    disabled={rateMutation.isPending}
                  >
                    <Star className={`h-5 w-5 ${value <= currentRating ? 'fill-current' : ''}`} />
                  </button>
                ))}
              </div>
            </div>

            {/* Files */}
            {materialData?.files && materialData.files.length > 0 && (
              <div className="mb-4">
                <p className="text-sm font-medium mb-2">Файлы:</p>
                <div className="space-y-2">
                  {materialData.files.map((file: any) => (
                    <div
                      key={file.id}
                      className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/50"
                    >
                      <div className="flex-1">
                        <p className="font-medium">{file.original_name}</p>
                        <p className="text-sm text-muted-foreground">
                          {formatFileSize(safeNumber(file.file_size))} • {file.file_type?.toUpperCase()}
                        </p>
                        {file.comment && (
                          <p className="text-sm text-muted-foreground mt-1">{file.comment}</p>
                        )}
                      </div>
                      <div className="flex gap-2 ml-4">
                        <button
                          onClick={() => handleDownload(file.original_name, file.id)}
                          className="p-2 hover:bg-accent rounded"
                          title="Скачать файл"
                        >
                          <Download className="h-5 w-5" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Tags */}
            {materialData?.tags && materialData.tags.length > 0 && (
              <div className="mb-4">
                <p className="text-sm font-medium mb-2">Теги:</p>
                <div className="flex flex-wrap gap-2">
                  {materialData.tags.map((tag: any) => (
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
          </div>

          {/* Comments Section */}
          <div className="border-t pt-6">
            <h3 className="text-lg font-semibold mb-4">Комментарии</h3>

            {/* Add Comment Form */}
            <form onSubmit={handleSubmitComment} className="mb-6">
              <div className="flex gap-2">
                <textarea
                  value={commentText}
                  onChange={(e) => setCommentText(e.target.value)}
                  placeholder="Написать комментарий..."
                  className="flex-1 px-3 py-2 border rounded-lg bg-background min-h-[80px]"
                  rows={3}
                />
                <button
                  type="submit"
                  disabled={commentMutation.isPending || !commentText.trim()}
                  className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed self-end"
                >
                  <Send className="h-4 w-4" />
                </button>
              </div>
            </form>

            {/* Comments List */}
            <div className="space-y-4">
              {comments && comments.length > 0 ? (
                comments.map((comment: any) => (
                  <div key={comment.id} className="border rounded-lg p-4">
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <p className="font-medium">{comment.author_name || comment.author_email}</p>
                        <p className="text-xs text-muted-foreground">
                          {formatDate(comment.created_at)}
                        </p>
                      </div>
                    </div>
                    <p className="text-sm">{comment.text}</p>
                    {comment.replies && comment.replies.length > 0 && (
                      <div className="mt-3 ml-4 space-y-2 border-l-2 pl-4">
                        {comment.replies.map((reply: any) => (
                          <div key={reply.id} className="text-sm">
                            <p className="font-medium">{reply.author_name || reply.author_email}</p>
                            <p className="text-muted-foreground">{reply.text}</p>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))
              ) : (
                <p className="text-muted-foreground text-center py-8">
                  Комментариев пока нет. Будьте первым!
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
