import { useState } from 'react'
import { Link } from 'react-router-dom'
import { ChevronRight, ChevronDown, Folder, FileText, Plus, Trash2 } from 'lucide-react'
import { cn } from '@/lib/utils'

interface Branch {
  id: number
  type: string
  name: string
  status: string
  children?: Branch[]
  materials_count?: number
}

interface BranchTreeProps {
  branches: Branch[]
  selectedBranch: number | null
  onSelectBranch: (id: number | null) => void
  onRequestBranch?: (parentId: number) => void
  onDeleteBranch?: (id: number) => void
  level?: number
}

export default function BranchTree({
  branches,
  selectedBranch,
  onSelectBranch,
  onRequestBranch,
  onDeleteBranch,
  level = 0,
}: BranchTreeProps) {
  const [expanded, setExpanded] = useState<Set<number>>(new Set())

  const toggleExpand = (id: number) => {
    const newExpanded = new Set(expanded)
    if (newExpanded.has(id)) {
      newExpanded.delete(id)
    } else {
      newExpanded.add(id)
    }
    setExpanded(newExpanded)
  }

  const canHaveChildren = (branch: Branch) => {
    return branch.type !== 'teacher'
  }

  return (
    <div className="space-y-1">
      {branches.map((branch) => {
        const hasChildren = branch.children && branch.children.length > 0
        const isExpanded = expanded.has(branch.id)
        const isSelected = selectedBranch === branch.id
        const isLeaf = branch.type === 'teacher' || branch.type === 'course'

        return (
          <div key={branch.id}>
            <div
              className={cn(
                'group flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer hover:bg-accent',
                isSelected && 'bg-primary text-primary-foreground'
              )}
              style={{ paddingLeft: `${level * 1.5 + 0.75}rem` }}
            >
              {hasChildren ? (
                <button
                  onClick={() => toggleExpand(branch.id)}
                  className="p-1 hover:bg-accent rounded"
                >
                  {isExpanded ? (
                    <ChevronDown className="h-4 w-4" />
                  ) : (
                    <ChevronRight className="h-4 w-4" />
                  )}
                </button>
              ) : (
                <div className="w-6" />
              )}

              {isLeaf ? (
                <FileText className="h-4 w-4" />
              ) : (
                <Folder className="h-4 w-4" />
              )}

              <Link
                to={`/branches/${branch.id}`}
                className="flex-1 flex items-center justify-between min-w-0"
                onClick={(e) => {
                  if (hasChildren) {
                    e.preventDefault()
                    toggleExpand(branch.id)
                  }
                  onSelectBranch(branch.id)
                }}
              >
                <span className="font-medium truncate">{branch.name}</span>
                <div className="flex items-center gap-2 ml-2">
                  {branch.materials_count !== undefined && branch.materials_count > 0 && (
                    <span className="text-sm text-muted-foreground whitespace-nowrap">
                      {branch.materials_count}
                    </span>
                  )}
                  {canHaveChildren(branch) && onRequestBranch && (
                    <button
                      onClick={(e) => {
                        e.preventDefault()
                        e.stopPropagation()
                        onRequestBranch(branch.id)
                      }}
                      className="p-1 hover:bg-accent rounded opacity-0 group-hover:opacity-100 transition-opacity"
                      title="Запросить дочернюю ветку"
                    >
                      <Plus className="h-4 w-4" />
                    </button>
                  )}
                </div>
              </Link>
              
              {/* Delete button */}
              {onDeleteBranch && (
                <button
                  onClick={(e) => {
                    e.preventDefault()
                    e.stopPropagation()
                    if (window.confirm('Вы уверены, что хотите удалить эту ветку? Это действие нельзя отменить.')) {
                      onDeleteBranch(branch.id)
                    }
                  }}
                  className="p-1.5 text-destructive hover:bg-destructive/10 rounded opacity-0 group-hover:opacity-100 transition-opacity ml-1"
                  title="Удалить ветку"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              )}
            </div>

            {hasChildren && isExpanded && (
              <BranchTree
                branches={branch.children!}
                selectedBranch={selectedBranch}
                onSelectBranch={onSelectBranch}
                onRequestBranch={onRequestBranch}
                onDeleteBranch={onDeleteBranch}
                level={level + 1}
              />
            )}
          </div>
        )
      })}
    </div>
  )
}

