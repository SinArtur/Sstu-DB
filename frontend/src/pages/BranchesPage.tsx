import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import api from '@/lib/api'
import { Plus, Search, X, Folder, FileText, File } from 'lucide-react'
import BranchTree from '@/components/BranchTree'
import BranchRequestModal from '@/components/BranchRequestModal'
import { useNavigate } from 'react-router-dom'

export default function BranchesPage() {
  const [selectedBranch, setSelectedBranch] = useState<number | null>(null)
  const [showRequestModal, setShowRequestModal] = useState(false)
  const [preselectedParentId, setPreselectedParentId] = useState<number | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const navigate = useNavigate()

  const { data: tree, isLoading } = useQuery({
    queryKey: ['branches-tree'],
    queryFn: async () => {
      const res = await api.get('/branches/tree/')
      return res.data
    },
  })

  const { data: searchResults, isLoading: isSearching } = useQuery({
    queryKey: ['branches-search', searchQuery],
    queryFn: async () => {
      if (!searchQuery.trim()) return { branches: [], materials: [], files: [] }
      const res = await api.get(`/branches/search/?q=${encodeURIComponent(searchQuery)}`)
      return res.data
    },
    enabled: searchQuery.trim().length > 0,
  })

  if (isLoading) {
    return <div className="text-center py-12">Загрузка...</div>
  }

  const handleRequestBranch = (parentId: number) => {
    setPreselectedParentId(parentId)
    setShowRequestModal(true)
  }

  const handleCloseModal = () => {
    setShowRequestModal(false)
    setPreselectedParentId(null)
  }

  const handleBranchClick = (branchId: number) => {
    navigate(`/branches/${branchId}`)
    setSearchQuery('')
  }

  const handleMaterialClick = (materialId: number) => {
    navigate(`/materials/${materialId}`)
    setSearchQuery('')
  }

  const handleFileClick = (branchId: number, materialId: number) => {
    navigate(`/branches/${branchId}`)
    setSearchQuery('')
    // Scroll to material after navigation
    setTimeout(() => {
      const element = document.getElementById(`material-${materialId}`)
      if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'center' })
      }
    }, 100)
  }

  return (
    <div className="max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold">База знаний</h1>
        <button
          onClick={() => {
            setPreselectedParentId(null)
            setShowRequestModal(true)
          }}
          className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90"
        >
          <Plus className="h-4 w-4" />
          Запросить ветку
        </button>
      </div>

      {/* Search */}
      <div className="relative mb-6">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-muted-foreground" />
          <input
            type="text"
            placeholder="Поиск по веткам, материалам и файлам..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-10 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-3 top-1/2 transform -translate-y-1/2 text-muted-foreground hover:text-foreground"
            >
              <X className="h-5 w-5" />
            </button>
          )}
        </div>

        {/* Search Results */}
        {searchQuery.trim() && (
          <div className="absolute z-10 w-full mt-2 bg-card border rounded-lg shadow-lg max-h-[600px] overflow-y-auto">
            {isSearching ? (
              <div className="p-4 text-center text-muted-foreground">Поиск...</div>
            ) : (
              <>
                {/* Branches */}
                {searchResults?.branches && searchResults.branches.length > 0 && (
                  <div className="border-b">
                    <div className="px-4 py-2 bg-muted/50 text-sm font-semibold flex items-center gap-2">
                      <Folder className="h-4 w-4" />
                      Ветки ({searchResults.branches.length})
                    </div>
                    <div className="py-1">
                      {searchResults.branches.map((branch: any) => (
                        <button
                          key={`branch-${branch.id}`}
                          onClick={() => handleBranchClick(branch.id)}
                          className="w-full text-left px-4 py-2 hover:bg-accent transition-colors flex items-start gap-3"
                        >
                          <Folder className="h-5 w-5 text-blue-500 mt-0.5 flex-shrink-0" />
                          <div className="flex-1 min-w-0">
                            <div className="font-medium">{branch.name}</div>
                            {branch.full_path && (
                              <div className="text-sm text-muted-foreground truncate">
                                {branch.full_path}
                              </div>
                            )}
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Materials */}
                {searchResults?.materials && searchResults.materials.length > 0 && (
                  <div className="border-b">
                    <div className="px-4 py-2 bg-muted/50 text-sm font-semibold flex items-center gap-2">
                      <FileText className="h-4 w-4" />
                      Материалы ({searchResults.materials.length})
                    </div>
                    <div className="py-1">
                      {searchResults.materials.map((material: any) => (
                        <button
                          key={`material-${material.id}`}
                          onClick={() => handleMaterialClick(material.id)}
                          className="w-full text-left px-4 py-2 hover:bg-accent transition-colors"
                        >
                          <div className="font-medium line-clamp-2">{material.description || 'Без описания'}</div>
                          {material.branch_path && (
                            <div className="text-sm text-muted-foreground truncate">
                              {material.branch_path}
                            </div>
                          )}
                          {material.files && material.files.length > 0 && (
                            <div className="text-xs text-muted-foreground mt-1">
                              {material.files.length} файл(ов)
                            </div>
                          )}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Files */}
                {searchResults?.files && searchResults.files.length > 0 && (
                  <div>
                    <div className="px-4 py-2 bg-muted/50 text-sm font-semibold flex items-center gap-2">
                      <File className="h-4 w-4" />
                      Файлы ({searchResults.files.length})
                    </div>
                    <div className="py-1">
                      {searchResults.files.map((file: any, index: number) => (
                        <button
                          key={`file-${file.id || index}`}
                          onClick={() => handleFileClick(file.branch_id, file.material_id)}
                          className="w-full text-left px-4 py-2 hover:bg-accent transition-colors flex items-start gap-3"
                        >
                          <File className="h-5 w-5 text-green-500 mt-0.5 flex-shrink-0" />
                          <div className="flex-1 min-w-0">
                            <div className="font-medium truncate">{file.original_name}</div>
                            {file.branch_path && (
                              <div className="text-sm text-muted-foreground truncate">
                                {file.branch_path}
                              </div>
                            )}
                            {file.material_description && (
                              <div className="text-xs text-muted-foreground mt-1 line-clamp-1">
                                {file.material_description}
                              </div>
                            )}
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* No results */}
                {(!searchResults?.branches || searchResults.branches.length === 0) &&
                 (!searchResults?.materials || searchResults.materials.length === 0) &&
                 (!searchResults?.files || searchResults.files.length === 0) && (
                  <div className="p-4 text-center text-muted-foreground">
                    Ничего не найдено
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </div>

      {/* Tree View (hidden when searching) */}
      {!searchQuery.trim() && (
        <>
          {tree && tree.length > 0 ? (
            <BranchTree
              branches={tree}
              selectedBranch={selectedBranch}
              onSelectBranch={setSelectedBranch}
              onRequestBranch={handleRequestBranch}
            />
          ) : (
            <div className="text-center py-12 bg-card border rounded-lg">
              <p className="text-muted-foreground mb-4">Ветки еще не созданы</p>
              <button
                onClick={() => {
                  setPreselectedParentId(null)
                  setShowRequestModal(true)
                }}
                className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90"
              >
                Создать первую ветку
              </button>
            </div>
          )}
        </>
      )}

      {showRequestModal && (
        <BranchRequestModal
          onClose={handleCloseModal}
          onSuccess={() => {
            // Tree will be refreshed automatically via query invalidation
          }}
          preselectedParentId={preselectedParentId}
        />
      )}
    </div>
  )
}

