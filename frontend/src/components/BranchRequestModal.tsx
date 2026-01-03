import { useState, useEffect, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import toast from 'react-hot-toast'
import { X, Info } from 'lucide-react'

interface Branch {
  id: number
  type: string
  name: string
  status: string
  full_path?: string
  get_full_path?: string
}

interface BranchRequestModalProps {
  onClose: () => void
  onSuccess: () => void
  preselectedParentId?: number | null
}

const TYPE_LABELS: Record<string, string> = {
  institute: 'Институт',
  department: 'Кафедра',
  direction: 'Направление',
  course: 'Курс',
  teacher: 'Преподаватель',
}

const NEXT_TYPE_MAP: Record<string, string> = {
  institute: 'department',
  department: 'direction',
  direction: 'course',
  course: 'teacher',
}

export default function BranchRequestModal({
  onClose,
  onSuccess,
  preselectedParentId = null,
}: BranchRequestModalProps) {
  const [formData, setFormData] = useState({
    parent: preselectedParentId?.toString() || '',
    name: '',
  })
  const queryClient = useQueryClient()

  // Get list of branches that can have children (all except teacher)
  const { data: availableBranches, isLoading: branchesLoading } = useQuery({
    queryKey: ['branches-for-request'],
    queryFn: async () => {
      // Fetch all pages to get all branches
      let allBranches: Branch[] = []
      let page = 1
      let hasMore = true
      
      while (hasMore) {
        const res = await api.get(`/branches/?status=approved&page=${page}`)
        
        // Handle paginated response
        if (res.data.results && Array.isArray(res.data.results)) {
          const branches = res.data.results
          allBranches = [...allBranches, ...branches]
          // Check if there are more pages (next URL exists)
          hasMore = !!res.data.next && branches.length === 20
          page++
        } else if (Array.isArray(res.data)) {
          // Non-paginated response
          allBranches = res.data
          hasMore = false
        } else {
          // Single object or empty
          hasMore = false
        }
      }
      
      // Filter only branches that can have children (not teacher)
      return allBranches.filter((b: Branch) => b.type !== 'teacher')
    },
  })

  // Find selected parent branch
  const selectedParent = useMemo(() => {
    if (!formData.parent || !availableBranches) return null
    return availableBranches.find(
      (b: Branch) => b.id.toString() === formData.parent
    )
  }, [formData.parent, availableBranches])

  // Determine next branch type based on selected parent
  const nextBranchType = useMemo(() => {
    if (!selectedParent) return null
    return NEXT_TYPE_MAP[selectedParent.type] || null
  }, [selectedParent])

  // Create branch request mutation
  const mutation = useMutation({
    mutationFn: async (data: { parent: number; name: string }) => {
      const res = await api.post('/branches/requests/', data)
      return res.data
    },
    onSuccess: () => {
      toast.success('Запрос на создание ветки отправлен')
      queryClient.invalidateQueries({ queryKey: ['branches-for-request'] })
      queryClient.invalidateQueries({ queryKey: ['branches-tree'] })
      onSuccess()
      onClose()
    },
    onError: (error: any) => {
      const errorMessage =
        error.response?.data?.parent?.[0] ||
        error.response?.data?.name?.[0] ||
        error.response?.data?.error ||
        'Ошибка при создании запроса'
      toast.error(errorMessage)
    },
  })

  // Set preselected parent when component mounts
  useEffect(() => {
    if (preselectedParentId) {
      setFormData((prev: { parent: string; name: string }) => ({
        ...prev,
        parent: preselectedParentId.toString(),
      }))
    }
  }, [preselectedParentId])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.parent || !formData.name.trim()) {
      toast.error('Заполните все поля')
      return
    }
    mutation.mutate({
      parent: parseInt(formData.parent, 10),
      name: formData.name.trim(),
    })
  }

  const handleClose = () => {
    setFormData({ parent: '', name: '' })
    onClose()
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-card border rounded-lg p-6 max-w-md w-full mx-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">Запросить новую ветку</h2>
          <button
            onClick={handleClose}
            className="p-1 hover:bg-accent rounded"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">
              Родительская ветка *
            </label>
            {branchesLoading ? (
              <div className="text-sm text-muted-foreground">Загрузка...</div>
            ) : (
              <select
                value={formData.parent}
                onChange={(e) =>
                  setFormData({ ...formData, parent: e.target.value })
                }
                className="w-full px-3 py-2 border rounded-lg bg-background"
                required
              >
                <option value="">Выберите родительскую ветку</option>
                {availableBranches?.map((branch: Branch) => (
                  <option key={branch.id} value={branch.id}>
                    {(branch.full_path || branch.get_full_path || branch.name)} ({TYPE_LABELS[branch.type] || branch.type})
                  </option>
                ))}
              </select>
            )}
          </div>

          {selectedParent && nextBranchType && (
            <div className="flex items-start gap-2 p-3 bg-muted rounded-lg">
              <Info className="h-5 w-5 text-primary mt-0.5 flex-shrink-0" />
              <div className="text-sm">
                <p className="font-medium mb-1">
                  Будет создана ветка типа: {TYPE_LABELS[nextBranchType] || nextBranchType}
                </p>
                <p className="text-muted-foreground">
                  Родитель: {selectedParent.full_path || selectedParent.get_full_path || selectedParent.name}
                </p>
              </div>
            </div>
          )}

          <div>
            <label className="block text-sm font-medium mb-2">
              Название новой ветки *
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) =>
                setFormData({ ...formData, name: e.target.value })
              }
              placeholder={
                nextBranchType
                  ? `Введите название ${TYPE_LABELS[nextBranchType].toLowerCase()}а`
                  : 'Введите название'
              }
              className="w-full px-3 py-2 border rounded-lg bg-background"
              required
              minLength={2}
              maxLength={200}
            />
          </div>

          <div className="flex gap-2 justify-end pt-4">
            <button
              type="button"
              onClick={handleClose}
              className="px-4 py-2 border rounded-lg hover:bg-accent"
            >
              Отмена
            </button>
            <button
              type="submit"
              disabled={mutation.isPending || !formData.parent || !formData.name.trim()}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {mutation.isPending ? 'Отправка...' : 'Отправить запрос'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
