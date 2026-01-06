import { useState } from 'react'
import { Star, Download, Eye, MessageSquare } from 'lucide-react'
import { formatDate, formatFileSize } from '@/lib/utils'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import toast from 'react-hot-toast'
import MaterialViewModal from './MaterialViewModal'

interface MaterialCardProps {
  material: any
}

export default function MaterialCard({ material }: MaterialCardProps) {
  const queryClient = useQueryClient()
  const [showModal, setShowModal] = useState(false)

  // Safety checks
  if (!material) {
    console.warn('MaterialCard: material is null or undefined')
    return null
  }

  console.log('MaterialCard rendering material:', material.id, 'files:', material.files?.length || 0)

  const rateMutation = useMutation({
    mutationFn: async (value: number) => {
      const res = await api.post(`/materials/${material.id}/rate/`, { value })
      return res.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['materials'] })
      toast.success('Оценка сохранена')
    },
  })

  const handleRate = (value: number) => {
    rateMutation.mutate(value)
  }

  const handleDownload = async (fileName: string, fileId: number, e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
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

  // Ensure numeric values - convert to number safely
  const safeNumber = (value: any): number => {
    if (typeof value === 'number' && !isNaN(value)) return value
    const parsed = parseFloat(value)
    return isNaN(parsed) ? 0 : parsed
  }
  
  const averageRating = safeNumber(material.average_rating)
  const ratingsCount = safeNumber(material.ratings_count)
  const viewsCount = safeNumber(material.views_count)
  const downloadsCount = safeNumber(material.downloads_count)
  const commentsCount = safeNumber(material.comments_count)

  return (
    <div className="bg-card border rounded-lg p-4 md:p-6 hover:shadow-lg transition-shadow">
      <div className="flex flex-col md:flex-row md:items-start md:justify-between mb-3 md:mb-4 gap-2">
        <div className="flex-1 min-w-0">
          <button
            onClick={() => setShowModal(true)}
            className="text-base md:text-lg font-semibold hover:text-primary text-left break-words"
          >
            {material.branch_path || material.branch_name || 'Без названия'}
          </button>
          {material.description && (
            <p className="text-xs md:text-sm text-muted-foreground mt-1 line-clamp-2">{material.description}</p>
          )}
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <div className="flex items-center gap-1">
            <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
            <span className="text-sm font-medium">
              {isNaN(averageRating) ? '0.0' : averageRating.toFixed(1)}
            </span>
            <span className="text-xs text-muted-foreground hidden sm:inline">({ratingsCount})</span>
          </div>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2 md:gap-4 text-xs md:text-sm text-muted-foreground mb-3 md:mb-4">
        <span className="flex items-center gap-1">
          <Eye className="h-3 w-3 md:h-4 md:w-4" />
          {viewsCount}
        </span>
        <span className="flex items-center gap-1">
          <Download className="h-3 w-3 md:h-4 md:w-4" />
          {downloadsCount}
        </span>
        <span className="flex items-center gap-1">
          <MessageSquare className="h-3 w-3 md:h-4 md:w-4" />
          {commentsCount}
        </span>
        {material.created_at && (
          <span className="hidden sm:inline">{formatDate(material.created_at)}</span>
        )}
      </div>

      {material.files && material.files.length > 0 && (
        <div className="mb-3 md:mb-4">
          <p className="text-xs md:text-sm font-medium mb-2">Файлы:</p>
          <div className="flex flex-col sm:flex-row sm:flex-wrap gap-2">
            {material.files.map((file: any) => (
              <button
                key={file.id}
                onClick={(e) => handleDownload(file.original_name, file.id, e)}
                className="text-xs md:text-sm text-primary hover:underline text-left break-all"
              >
                {file.original_name} ({formatFileSize(Number(file.file_size) || 0)})
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="flex flex-col sm:flex-row sm:items-center gap-2">
        <span className="text-xs md:text-sm text-muted-foreground">Оценить:</span>
        <div className="flex items-center gap-1">
          {[1, 2, 3, 4, 5].map((value) => {
            const userRating = safeNumber(material.user_rating)
            const isFilled = value <= userRating
            return (
              <button
                key={value}
                onClick={() => handleRate(value)}
                className={`p-1 transition-colors touch-manipulation ${
                  isFilled
                    ? 'text-yellow-400'
                    : 'text-muted-foreground hover:text-yellow-400'
                }`}
              >
                <Star className={`h-4 w-4 md:h-5 md:w-5 ${isFilled ? 'fill-current' : ''}`} />
              </button>
            )
          })}
        </div>
      </div>

      {showModal && (
        <MaterialViewModal
          material={material}
          onClose={() => setShowModal(false)}
        />
      )}
    </div>
  )
}

