import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import api from '@/lib/api'
import { Eye } from 'lucide-react'
import MaterialModerationModal from '@/components/MaterialModerationModal'
import BranchRequestModerationModal from '@/components/BranchRequestModerationModal'

export default function ModerationPage() {
  const [selectedMaterial, setSelectedMaterial] = useState<any | null>(null)
  const [selectedRequest, setSelectedRequest] = useState<any | null>(null)

  const { data: pending } = useQuery({
    queryKey: ['moderation-pending'],
    queryFn: async () => {
      const [materialsRes, requestsRes] = await Promise.all([
        api.get('/materials/?status=pending'),
        api.get('/branches/requests/?status=pending'),
      ])
      // Handle paginated responses
      const materials = Array.isArray(materialsRes.data)
        ? materialsRes.data
        : materialsRes.data.results || []
      
      const requests = Array.isArray(requestsRes.data)
        ? requestsRes.data
        : requestsRes.data.results || []
      
      return {
        materials,
        requests,
      }
    },
  })


  return (
    <div className="max-w-6xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">Модерация</h1>

      <div className="space-y-6">
        <div>
          <h2 className="text-xl font-semibold mb-4">Запросы на ветки</h2>
          {pending?.requests && pending.requests.length > 0 ? (
            <div className="space-y-4">
              {pending.requests.map((request: any) => (
                <div key={request.id} className="bg-card border rounded-lg p-4">
                  <p className="font-medium">{request.name}</p>
                  <p className="text-sm text-muted-foreground">
                    Родитель: {request.parent_path}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    От: {request.requester_email}
                  </p>
                  <div className="flex gap-2 mt-4">
                    <button
                      onClick={() => setSelectedRequest(request)}
                      className="flex items-center gap-2 px-4 py-2 border rounded-lg hover:bg-accent"
                    >
                      <Eye className="h-4 w-4" />
                      Просмотреть
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-muted-foreground">Нет запросов на модерацию</p>
          )}
        </div>

        <div>
          <h2 className="text-xl font-semibold mb-4">Материалы на модерации</h2>
          {pending?.materials && pending.materials.length > 0 ? (
            <div className="space-y-4">
              {pending.materials.map((material: any) => (
                <div key={material.id} className="bg-card border rounded-lg p-4">
                  <p className="font-medium">{material.branch_path}</p>
                  <p className="text-base text-foreground mt-2 leading-relaxed">
                    {material.description || 'Без описания'}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    От: {material.author_email}
                  </p>
                  {material.files && material.files.length > 0 && (
                    <p className="text-sm text-muted-foreground mt-1">
                      Файлов: {material.files.length}
                    </p>
                  )}
                  <div className="flex gap-2 mt-4">
                    <button
                      onClick={() => setSelectedMaterial(material)}
                      className="flex items-center gap-2 px-4 py-2 border rounded-lg hover:bg-accent"
                    >
                      <Eye className="h-4 w-4" />
                      Просмотреть и проверить
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-muted-foreground">Нет материалов на модерации</p>
          )}
        </div>
      </div>

      {/* Modals */}
      {selectedMaterial && (
        <MaterialModerationModal
          material={selectedMaterial}
          onClose={() => setSelectedMaterial(null)}
          onSuccess={() => setSelectedMaterial(null)}
        />
      )}

      {selectedRequest && (
        <BranchRequestModerationModal
          request={selectedRequest}
          onClose={() => setSelectedRequest(null)}
          onSuccess={() => setSelectedRequest(null)}
        />
      )}
    </div>
  )
}

