import { useAuthStore } from '@/store/authStore'
import { Link } from 'react-router-dom'
import { BookOpen, Upload } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import api from '@/lib/api'
import { getUserDisplayName } from '@/lib/utils'

export default function DashboardPage() {
  const { user } = useAuthStore()

  const { data: stats } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: async () => {
      const [materialsRes] = await Promise.all([
        api.get('/materials/?my_materials=true'),
      ])
      
      let pendingRequests = 0
      try {
        const branchesRes = await api.get('/branches/requests/?status=pending')
        pendingRequests = branchesRes.data.count || branchesRes.data.results?.length || 0
      } catch (error) {
        // Ignore if user doesn't have access
      }
      
      return {
        myMaterials: materialsRes.data.count || materialsRes.data.results?.length || 0,
        pendingRequests: pendingRequests,
      }
    },
  })

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">
          Добро пожаловать, {getUserDisplayName(user)}!
        </h1>
        <p className="text-muted-foreground">
          Студенческая база знаний - делитесь материалами и находите нужное
        </p>
      </div>

      {/* Quick Start Guide */}
      <div className="bg-card border rounded-lg p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Быстрый старт</h2>
        <ol className="space-y-3 list-decimal list-inside">
          <li>Перейдите в раздел "База знаний" для просмотра доступных материалов</li>
          <li>Выберите нужную ветку (Институт → Направление → Предмет → Преподаватель)</li>
          <li>Загрузите материалы, перетащив файлы в область загрузки</li>
          <li>Оцените полезные материалы и оставьте комментарии</li>
        </ol>
      </div>

      {/* Quick Actions */}
      <div className="grid md:grid-cols-2 gap-4 mb-6">
        <Link
          to="/branches"
          className="p-6 bg-card border rounded-lg hover:border-primary transition-colors"
        >
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold mb-2">Перейти в базу знаний</h3>
              <p className="text-sm text-muted-foreground">
                Просмотр и поиск материалов
              </p>
            </div>
            <BookOpen className="h-8 w-8 text-primary" />
          </div>
        </Link>

        <Link
          to="/profile"
          className="p-6 bg-card border rounded-lg hover:border-primary transition-colors"
        >
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold mb-2">Мои загрузки</h3>
              <p className="text-sm text-muted-foreground">
                {stats?.myMaterials || 0} материалов
              </p>
            </div>
            <Upload className="h-8 w-8 text-primary" />
          </div>
        </Link>
      </div>

      {/* Stats */}
      {stats && (
        <div className="bg-card border rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Статистика</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-muted-foreground">Мои материалы</p>
              <p className="text-2xl font-bold">{stats.myMaterials}</p>
            </div>
            {(user?.role === 'moderator' || user?.role === 'admin') && (
              <div>
                <p className="text-sm text-muted-foreground">На модерации</p>
                <p className="text-2xl font-bold">{stats.pendingRequests}</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

