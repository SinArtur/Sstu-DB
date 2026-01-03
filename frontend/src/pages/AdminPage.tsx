import { useState, useMemo, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import api from '@/lib/api'
import toast from 'react-hot-toast'
import { Plus, Edit, Trash2, X, Save, Info } from 'lucide-react'
import BranchTree from '@/components/BranchTree'
import { useAuthStore } from '@/store/authStore'

interface Branch {
  id: number
  type: string
  type_display: string
  name: string
  parent: number | null
  full_path: string
  status: string
  status_display: string
  children_count: number
  materials_count: number
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

export default function AdminPage() {
  const { user } = useAuthStore()
  const navigate = useNavigate()
  const [selectedBranch, setSelectedBranch] = useState<number | null>(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [editingBranch, setEditingBranch] = useState<number | null>(null)
  const [editForm, setEditForm] = useState({
    name: '',
    parent: '',
  })
  const queryClient = useQueryClient()

  // Check access
  useEffect(() => {
    const hasAccess = user?.role === 'admin' || (user?.role === 'moderator' && user?.can_access_admin_panel)
    if (!hasAccess) {
      toast.error('У вас нет доступа к админ-панели')
      navigate('/')
    }
  }, [user, navigate])

  const { data: tree } = useQuery({
    queryKey: ['branches-tree'],
    queryFn: async () => {
      const res = await api.get('/branches/tree/')
      return res.data
    },
  })

  const { data: allBranches } = useQuery({
    queryKey: ['admin-all-branches'],
    queryFn: async () => {
      const res = await api.get('/branches/')
      return res.data.results || res.data
    },
  })

  // Get available parent branches for creating/editing (with pagination)
  const { data: parentBranches, isLoading: parentBranchesLoading } = useQuery({
    queryKey: ['admin-parent-branches'],
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
    if (!editForm.parent || !parentBranches) return null
    return parentBranches.find(
      (b: Branch) => b.id.toString() === editForm.parent
    )
  }, [editForm.parent, parentBranches])

  // Determine next branch type based on selected parent
  const nextBranchType = useMemo(() => {
    if (!editForm.parent) return 'institute' // If no parent, it's an institute
    if (!selectedParent) return null
    return NEXT_TYPE_MAP[selectedParent.type] || null
  }, [editForm.parent, selectedParent])

  const createMutation = useMutation({
    mutationFn: async (data: { name: string; type: string; parent: number | null }) => {
      const res = await api.post('/branches/', {
        name: data.name,
        type: data.type,
        parent: data.parent || null,
        status: 'approved',
      })
      return res.data
    },
    onSuccess: () => {
      toast.success('Ветка создана')
      queryClient.invalidateQueries({ queryKey: ['branches-tree'] })
      queryClient.invalidateQueries({ queryKey: ['admin-all-branches'] })
      queryClient.invalidateQueries({ queryKey: ['admin-parent-branches'] })
      setShowCreateModal(false)
      setEditForm({ name: '', parent: '' })
    },
    onError: (error: any) => {
      const errorMessage =
        error.response?.data?.name?.[0] ||
        error.response?.data?.parent?.[0] ||
        error.response?.data?.error ||
        'Ошибка при создании ветки'
      toast.error(errorMessage)
    },
  })

  const updateMutation = useMutation({
    mutationFn: async ({ id, data }: { id: number; data: { name: string; type: string; parent: number | null } }) => {
      const res = await api.patch(`/branches/${id}/`, data)
      return res.data
    },
    onSuccess: () => {
      toast.success('Ветка обновлена')
      queryClient.invalidateQueries({ queryKey: ['branches-tree'] })
      queryClient.invalidateQueries({ queryKey: ['admin-all-branches'] })
      queryClient.invalidateQueries({ queryKey: ['admin-parent-branches'] })
      setEditingBranch(null)
      setEditForm({ name: '', parent: '' })
    },
    onError: (error: any) => {
      const errorMessage =
        error.response?.data?.name?.[0] ||
        error.response?.data?.parent?.[0] ||
        error.response?.data?.error ||
        'Ошибка при обновлении ветки'
      toast.error(errorMessage)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/branches/${id}/`)
    },
    onSuccess: () => {
      toast.success('Ветка удалена')
      queryClient.invalidateQueries({ queryKey: ['branches-tree'] })
      queryClient.invalidateQueries({ queryKey: ['admin-all-branches'] })
      queryClient.invalidateQueries({ queryKey: ['admin-parent-branches'] })
    },
    onError: (error: any) => {
      const errorMessage = error.response?.data?.error || 'Ошибка при удалении ветки'
      toast.error(errorMessage)
    },
  })

  const handleCreate = () => {
    if (!editForm.name.trim()) {
      toast.error('Введите название ветки')
      return
    }
    if (!nextBranchType) {
      toast.error('Выберите родительскую ветку или оставьте пустым для создания института')
      return
    }
    createMutation.mutate({
      name: editForm.name.trim(),
      type: nextBranchType,
      parent: editForm.parent ? parseInt(editForm.parent, 10) : null,
    })
  }

  const handleEdit = (branch: Branch) => {
    setEditingBranch(branch.id)
    setEditForm({
      name: branch.name,
      parent: branch.parent?.toString() || '',
    })
  }

  const handleSave = () => {
    if (!editForm.name.trim()) {
      toast.error('Введите название ветки')
      return
    }
    if (!editingBranch) return
    
    // Find the branch being edited to get its type
    const branchBeingEdited = allBranches?.find((b: Branch) => b.id === editingBranch)
    if (!branchBeingEdited) return
    
    updateMutation.mutate({
      id: editingBranch,
      data: {
        name: editForm.name.trim(),
        type: branchBeingEdited.type, // Keep the same type when editing
        parent: editForm.parent ? parseInt(editForm.parent, 10) : null,
      },
    })
  }

  const handleDelete = (id: number) => {
    if (window.confirm('Вы уверены, что хотите удалить эту ветку? Это действие нельзя отменить.')) {
      deleteMutation.mutate(id)
    }
  }

  const handleCancel = () => {
    setEditingBranch(null)
    setShowCreateModal(false)
    setEditForm({ name: '', parent: '' })
  }

  return (
    <div className="max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold">Админ-панель</h1>
        <button
          onClick={() => {
            setShowCreateModal(true)
            setEditForm({ name: '', parent: '' })
          }}
          className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90"
        >
          <Plus className="h-4 w-4" />
          Создать ветку
        </button>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Tree View */}
        <div className="bg-card border rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Дерево веток</h2>
          {tree && tree.length > 0 ? (
            <BranchTree
              branches={tree}
              selectedBranch={selectedBranch}
              onSelectBranch={setSelectedBranch}
              onDeleteBranch={handleDelete}
            />
          ) : (
            <p className="text-muted-foreground">Ветки еще не созданы</p>
          )}
        </div>

        {/* List View */}
        <div className="bg-card border rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Все ветки</h2>
          <div className="space-y-2 max-h-[600px] overflow-y-auto">
            {allBranches && allBranches.length > 0 ? (
              allBranches.map((branch: Branch) => (
                <div
                  key={branch.id}
                  className={`p-3 border rounded-lg ${
                    editingBranch === branch.id ? 'bg-muted' : ''
                  }`}
                >
                  {editingBranch === branch.id ? (
                    <div className="space-y-2">
                      <input
                        type="text"
                        value={editForm.name}
                        onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                        className="w-full px-2 py-1 border rounded"
                        placeholder="Название"
                      />
                      <div className="flex gap-2">
                        <button
                          onClick={handleSave}
                          className="flex items-center gap-1 px-2 py-1 bg-green-600 text-white rounded text-sm"
                        >
                          <Save className="h-3 w-3" />
                          Сохранить
                        </button>
                        <button
                          onClick={handleCancel}
                          className="flex items-center gap-1 px-2 py-1 border rounded text-sm"
                        >
                          <X className="h-3 w-3" />
                          Отмена
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium">{branch.name}</p>
                        <p className="text-sm text-muted-foreground">
                          {TYPE_LABELS[branch.type] || branch.type} • {branch.status_display}
                        </p>
                        <p className="text-xs text-muted-foreground">{branch.full_path}</p>
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleEdit(branch)}
                          className="p-1 hover:bg-accent rounded"
                          title="Редактировать"
                        >
                          <Edit className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(branch.id)}
                          className="p-1 hover:bg-destructive/10 text-destructive rounded"
                          title="Удалить"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ))
            ) : (
              <p className="text-muted-foreground">Ветки еще не созданы</p>
            )}
          </div>
        </div>
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-card border rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold">Создать ветку</h2>
              <button onClick={handleCancel} className="p-1 hover:bg-accent rounded">
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">
                  Родительская ветка
                </label>
                {parentBranchesLoading ? (
                  <div className="text-sm text-muted-foreground">Загрузка...</div>
                ) : (
                  <select
                    value={editForm.parent}
                    onChange={(e) =>
                      setEditForm({ ...editForm, parent: e.target.value })
                    }
                    className="w-full px-3 py-2 border rounded-lg bg-background"
                  >
                    <option value="">Оставить пустым для создания института</option>
                    {parentBranches?.map((branch: Branch) => (
                      <option key={branch.id} value={branch.id}>
                        {(branch.full_path || branch.name)} ({TYPE_LABELS[branch.type] || branch.type})
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
                      Родитель: {selectedParent.full_path || selectedParent.name}
                    </p>
                  </div>
                </div>
              )}

              {!editForm.parent && (
                <div className="flex items-start gap-2 p-3 bg-muted rounded-lg">
                  <Info className="h-5 w-5 text-primary mt-0.5 flex-shrink-0" />
                  <div className="text-sm">
                    <p className="font-medium mb-1">
                      Будет создана ветка типа: {TYPE_LABELS['institute']}
                    </p>
                    <p className="text-muted-foreground">
                      Институт создается без родительской ветки
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
                  value={editForm.name}
                  onChange={(e) =>
                    setEditForm({ ...editForm, name: e.target.value })
                  }
                  placeholder={
                    nextBranchType
                      ? `Введите название ${TYPE_LABELS[nextBranchType].toLowerCase()}а`
                      : 'Введите название института'
                  }
                  className="w-full px-3 py-2 border rounded-lg bg-background"
                  required
                  minLength={2}
                  maxLength={200}
                />
              </div>

              <div className="flex gap-2 justify-end pt-4">
                <button
                  onClick={handleCancel}
                  className="px-4 py-2 border rounded-lg hover:bg-accent"
                >
                  Отмена
                </button>
                <button
                  onClick={handleCreate}
                  disabled={createMutation.isPending || !editForm.name.trim() || !nextBranchType}
                  className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {createMutation.isPending ? 'Создание...' : 'Создать'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
