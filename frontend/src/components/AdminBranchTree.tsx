import { useState } from 'react'
import { ChevronRight, ChevronDown, Folder, FileText, Trash2 } from 'lucide-react'
import { cn } from '@/lib/utils'

interface Branch {
  id: number
  type: string
  name: string
  status: string
  children?: Branch[]
  materials_count?: number
}

interface AdminBranchTreeProps {
  branches: Branch[]
  selectedBranches: Set<number>
  onSelectBranch: (id: number, selected: boolean) => void
  onDeleteBranch: (id: number) => void
  level?: number
}

export default function AdminBranchTree({
  branches,
  selectedBranches,
  onSelectBranch,
  onDeleteBranch,
  level = 0,
}: AdminBranchTreeProps) {
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

  const handleCheckboxChange = (branchId: number, checked: boolean) => {
    onSelectBranch(branchId, checked)
  }

  const handleDelete = (e: React.MouseEvent, branchId: number) => {
    e.stopPropagation()
    if (confirm('Вы уверены, что хотите удалить эту ветку? Это действие нельзя отменить.')) {
      onDeleteBranch(branchId)
    }
  }

  return (
    <div className="space-y-1">
      {branches.map((branch) => {
        const hasChildren = branch.children && branch.children.length > 0
        const isExpanded = expanded.has(branch.id)
        const isSelected = selectedBranches.has(branch.id)
        const isLeaf = branch.type === 'teacher' || branch.type === 'course'

        return (
          <div key={branch.id}>
            <div
              className={cn(
                'flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-accent transition-colors group',
                isSelected && 'bg-primary/10 border border-primary'
              )}
              style={{ paddingLeft: `${level * 1.5 + 0.75}rem` }}
            >
              {/* Checkbox */}
              <input
                id={`branch-checkbox-${branch.id}`}
                name={`branch-checkbox-${branch.id}`}
                type="checkbox"
                checked={isSelected}
                onChange={(e) => handleCheckboxChange(branch.id, e.target.checked)}
                onClick={(e) => e.stopPropagation()}
                className="w-4 h-4 rounded border-border bg-background text-primary focus:ring-primary focus:ring-2 cursor-pointer"
              />

              {/* Expand/Collapse button */}
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

              {/* Icon */}
              {isLeaf ? (
                <FileText className="h-4 w-4 text-muted-foreground" />
              ) : (
                <Folder className="h-4 w-4 text-muted-foreground" />
              )}

              {/* Branch name */}
              <div className="flex-1 flex items-center justify-between min-w-0">
                <span className="font-medium truncate">{branch.name}</span>
                {branch.materials_count !== undefined && branch.materials_count > 0 && (
                  <span className="text-sm text-muted-foreground ml-2">
                    {branch.materials_count}
                  </span>
                )}
              </div>

              {/* Delete button */}
              <button
                onClick={(e) => handleDelete(e, branch.id)}
                className="p-1.5 text-destructive hover:bg-destructive/10 rounded opacity-0 group-hover:opacity-100 transition-opacity"
                title="Удалить ветку"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>

            {/* Children */}
            {hasChildren && isExpanded && (
              <AdminBranchTree
                branches={branch.children!}
                selectedBranches={selectedBranches}
                onSelectBranch={onSelectBranch}
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

