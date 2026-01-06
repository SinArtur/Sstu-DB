import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import MaterialCard from '@/components/MaterialCard'
import MaterialUpload from '@/components/MaterialUpload'
import { Upload } from 'lucide-react'

export default function MaterialsPage() {
  const { branchId } = useParams()
  const [showUpload, setShowUpload] = useState(false)
  const queryClient = useQueryClient()

  const { data: branch } = useQuery({
    queryKey: ['branch', branchId],
    queryFn: async () => {
      const res = await api.get(`/branches/${branchId}/`)
      return res.data
    },
    enabled: !!branchId,
  })

  const { data: materials, isLoading, error } = useQuery({
    queryKey: ['materials', branchId],
    queryFn: async () => {
      try {
        const res = await api.get(`/materials/?branch=${branchId}&status=approved`)
        console.log('Materials API response:', res.data)
        // Handle both paginated and non-paginated responses
        let materialsList = []
        if (Array.isArray(res.data)) {
          materialsList = res.data
        } else if (res.data && res.data.results && Array.isArray(res.data.results)) {
          materialsList = res.data.results
        }
        console.log('Processed materials list:', materialsList)
        return materialsList
      } catch (err) {
        console.error('Error loading materials:', err)
        return []
      }
    },
    enabled: !!branchId,
  })

  if (!branchId) {
    return <div className="text-center py-12">Выберите ветку для просмотра материалов</div>
  }

  // Only show upload button for teacher-level branches
  const canUpload = branch?.type === 'teacher' || branch?.type === 'course'

  if (isLoading) {
    return <div className="text-center py-12">Загрузка...</div>
  }

  if (error) {
    return (
      <div className="max-w-6xl mx-auto">
        <div className="text-center py-12 bg-destructive/10 border border-destructive rounded-lg">
          <p className="text-destructive mb-4">Ошибка загрузки материалов</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90"
          >
            Обновить страницу
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto">
      <div className="mb-4 md:mb-6">
        <h1 className="text-xl md:text-2xl font-bold mb-2 break-words">{branch?.full_path || branch?.name || 'Ветка'}</h1>
        <p className="text-sm md:text-base text-muted-foreground">
          {Array.isArray(materials) ? materials.length : 0} материалов
        </p>
      </div>

      {canUpload && (
        <div className="mb-4 md:mb-6">
          <button
            onClick={() => setShowUpload(true)}
            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 text-sm md:text-base w-full md:w-auto justify-center md:justify-start"
          >
            <Upload className="h-4 w-4" />
            Загрузить материалы
          </button>
        </div>
      )}

      {Array.isArray(materials) && materials.length > 0 ? (
        <div className="grid gap-4">
          {materials.map((material: any) => {
            if (!material || !material.id) {
              return null
            }
            return <MaterialCard key={material.id} material={material} />
          })}
        </div>
      ) : (
        <div className="text-center py-12 bg-card border rounded-lg">
          <p className="text-muted-foreground mb-4">Материалы еще не загружены</p>
          {canUpload && (
            <button
              onClick={() => setShowUpload(true)}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90"
            >
              Загрузить первый материал
            </button>
          )}
        </div>
      )}

      {showUpload && (
        <MaterialUpload
          branchId={parseInt(branchId!)}
          onClose={() => setShowUpload(false)}
          onSuccess={() => {
            setShowUpload(false)
            queryClient.invalidateQueries({ queryKey: ['materials', branchId] })
          }}
        />
      )}
    </div>
  )
}

