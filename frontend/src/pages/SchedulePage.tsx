import { useState, useEffect, useRef } from 'react'
import { scheduleApi } from '@/lib/api'
import { useAuthStore } from '@/store/authStore'
import { Calendar, Clock, MapPin, User, Search, Filter, RefreshCw, Download } from 'lucide-react'
import toast from 'react-hot-toast'

interface Lesson {
  id: number
  group_name: string
  subject_name: string
  teacher_name: string | null
  lesson_type: string
  lesson_type_display: string
  room: string
  weekday: number
  weekday_display: string
  lesson_number: number
  start_time: string
  end_time: string
  specific_date: string | null
  week_number: number | null
}

interface Group {
  id: number
  name: string
  institute_name: string
  education_form: string
  degree_type: string
}

interface Institute {
  id: number
  name: string
}

const WEEKDAYS = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']

const LESSON_TYPE_COLORS: Record<string, string> = {
  'лек': 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  'пр': 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  'лаб': 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
  'экз': 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
  'конс': 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
}

export default function SchedulePage() {
  const { user } = useAuthStore()
  const teacherSearchRef = useRef<HTMLDivElement>(null)
  const [lessons, setLessons] = useState<Lesson[]>([])
  const [groups, setGroups] = useState<Group[]>([])
  const [institutes, setInstitutes] = useState<Institute[]>([])
  const [teachers, setTeachers] = useState<any[]>([])
  const [selectedGroup, setSelectedGroup] = useState<number | null>(null)
  const [selectedInstitute, setSelectedInstitute] = useState<number | null>(null)
  const [selectedWeekday, setSelectedWeekday] = useState<number | null>(null)
  const [selectedTeacher, setSelectedTeacher] = useState<number | null>(null)
  const [selectedTeacherName, setSelectedTeacherName] = useState('')
  const [teacherSearchQuery, setTeacherSearchQuery] = useState('')
  const [showTeacherSuggestions, setShowTeacherSuggestions] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [loading, setLoading] = useState(true)
  const [showFilters, setShowFilters] = useState(false)
  const [viewMode, setViewMode] = useState<'group' | 'teacher'>('group')
  const [syncing, setSyncing] = useState(false)

  useEffect(() => {
    loadInitialData()
  }, [])

  // Close teacher suggestions when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (teacherSearchRef.current && !teacherSearchRef.current.contains(event.target as Node)) {
        setShowTeacherSuggestions(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [])

  useEffect(() => {
    if (selectedGroup || selectedTeacher) {
      loadLessons()
    } else {
      setLessons([])
    }
  }, [selectedGroup, selectedTeacher])

  const loadInitialData = async () => {
    try {
      setLoading(true)
      
      // Load institutes
      const institutesRes = await scheduleApi.getInstitutes()
      setInstitutes(institutesRes.data.results || institutesRes.data)

      // Try to load user's group
      if (user?.group) {
        try {
          const myGroupRes = await scheduleApi.getMyGroup()
          setSelectedGroup(myGroupRes.data.id)
          
          // Load groups from same institute
          if (myGroupRes.data.institute) {
            const groupsRes = await scheduleApi.getGroups({ institute: myGroupRes.data.institute })
            setGroups(groupsRes.data.results || groupsRes.data)
            setSelectedInstitute(myGroupRes.data.institute)
          }
        } catch (error) {
          console.error('Error loading user group:', error)
        }
      }
    } catch (error) {
      console.error('Error loading initial data:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadLessons = async () => {
    if (!selectedGroup && !selectedTeacher) return

    try {
      setLoading(true)
      const params: any = {}
      
      if (viewMode === 'group' && selectedGroup) {
        params.group = selectedGroup
      } else if (viewMode === 'teacher' && selectedTeacher) {
        params.teacher = selectedTeacher
      }
      
      if (selectedWeekday) {
        params.weekday = selectedWeekday
      }
      
      const response = await scheduleApi.getLessons(params)
      setLessons(response.data.results || response.data)
    } catch (error) {
      console.error('Error loading lessons:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadTeachers = async (search?: string) => {
    if (!search || search.length < 2) {
      setTeachers([])
      setShowTeacherSuggestions(false)
      return
    }
    
    try {
      const params: any = { search }
      const response = await scheduleApi.getTeachers(params)
      const teachersList = response.data.results || response.data
      setTeachers(teachersList)
      setShowTeacherSuggestions(teachersList.length > 0)
    } catch (error) {
      console.error('Error loading teachers:', error)
      setTeachers([])
      setShowTeacherSuggestions(false)
    }
  }

  const handleTeacherSelect = (teacher: any) => {
    setSelectedTeacher(teacher.id)
    setSelectedTeacherName(teacher.full_name)
    setTeacherSearchQuery(teacher.full_name)
    setShowTeacherSuggestions(false)
  }

  const handleTeacherSearchChange = (value: string) => {
    setTeacherSearchQuery(value)
    
    if (value !== selectedTeacherName) {
      setSelectedTeacher(null)
      setSelectedTeacherName('')
      setLessons([])
    }
    
    loadTeachers(value)
  }

  const handleInstituteChange = async (instituteId: number | null) => {
    setSelectedInstitute(instituteId)
    setSelectedGroup(null)
    setLessons([])

    if (instituteId) {
      try {
        const response = await scheduleApi.getGroups({ institute: instituteId })
        setGroups(response.data.results || response.data)
      } catch (error) {
        console.error('Error loading groups:', error)
      }
    } else {
      setGroups([])
    }
  }

  const handleGroupChange = (groupId: number | null) => {
    setSelectedGroup(groupId)
  }

  // Фильтруем занятия
  const filteredLessons = lessons.filter(lesson => {
    // Фильтр по дню недели
    if (selectedWeekday && lesson.weekday !== selectedWeekday) {
      return false
    }
    
    // Фильтр по поисковому запросу
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      if (
        !lesson.subject_name.toLowerCase().includes(query) &&
        !lesson.teacher_name?.toLowerCase().includes(query) &&
        !lesson.room.toLowerCase().includes(query)
      ) {
        return false
      }
    }
    
    return true
  })

  // Группируем занятия по датам
  const lessonsByDate = filteredLessons.reduce((acc, lesson) => {
    // Используем specific_date, если есть, иначе вычисляем дату на основе weekday
    let lessonDate: string
    
    if (lesson.specific_date) {
      lessonDate = lesson.specific_date
    } else {
      // Если нет даты, пропускаем это занятие (не должно быть таких, но на всякий случай)
      return acc
    }
    
    if (!acc[lessonDate]) {
      acc[lessonDate] = []
    }
    acc[lessonDate].push(lesson)
    return acc
  }, {} as Record<string, Lesson[]>)

  // Сортируем даты
  const sortedDates = Object.keys(lessonsByDate).sort((a, b) => {
    return new Date(a).getTime() - new Date(b).getTime()
  })

  // Группируем занятия по времени для одного дня
  const groupLessonsByTime = (lessons: Lesson[]) => {
    const grouped: Record<string, Lesson[]> = {}
    lessons.forEach(lesson => {
      const timeKey = `${lesson.lesson_number}-${lesson.start_time}-${lesson.end_time}`
      if (!grouped[timeKey]) {
        grouped[timeKey] = []
      }
      grouped[timeKey].push(lesson)
    })
    return grouped
  }

  const getLessonTypeColor = (type: string) => {
    return LESSON_TYPE_COLORS[type] || 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200'
  }

  const formatDateDisplay = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('ru-RU', { 
      weekday: 'long', 
      day: 'numeric', 
      month: 'long',
      year: 'numeric'
    })
  }

  const handleSyncSchedule = async () => {
    if (!user || user.role !== 'admin') {
      toast.error('У вас нет прав для синхронизации расписания')
      return
    }

    try {
      setSyncing(true)
      toast.loading('Синхронизация расписания...', { id: 'sync' })
      
      const response = await scheduleApi.triggerSyncSync()
      
      toast.success(
        `Синхронизация завершена! Обновлено групп: ${response.data.groups_updated}, Добавлено занятий: ${response.data.lessons_added}`,
        { id: 'sync', duration: 5000 }
      )
      
      // Перезагружаем данные
      await loadInitialData()
      if (selectedGroup || selectedTeacher) {
        await loadLessons()
      }
    } catch (error: any) {
      const errorMessage = error.response?.data?.error || 'Ошибка при синхронизации расписания'
      toast.error(errorMessage, { id: 'sync', duration: 5000 })
    } finally {
      setSyncing(false)
    }
  }

  if (loading && lessons.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <RefreshCw className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Расписание занятий</h1>
          <p className="text-muted-foreground mt-1">
            Просматривайте расписание пар и экзаменов
          </p>
        </div>
        <div className="flex items-center gap-2">
          {user?.role === 'admin' && (
            <button
              onClick={handleSyncSchedule}
              disabled={syncing}
              className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Download className={`h-5 w-5 ${syncing ? 'animate-spin' : ''}`} />
              {syncing ? 'Синхронизация...' : 'Обновить расписание'}
            </button>
          )}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
          >
            <Filter className="h-5 w-5" />
            Фильтры
          </button>
        </div>
      </div>

      {/* Filters */}
      {showFilters && (
        <div className="bg-card border rounded-lg p-6 space-y-4">
          {/* View Mode Tabs */}
          <div className="flex gap-2 mb-4">
            <button
              onClick={() => {
                setViewMode('group')
                setSelectedTeacher(null)
                setLessons([])
              }}
              className={`px-4 py-2 rounded-lg transition-colors ${
                viewMode === 'group'
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-accent hover:bg-accent/80'
              }`}
            >
              По группам
            </button>
            <button
              onClick={() => {
                setViewMode('teacher')
                setSelectedGroup(null)
                setLessons([])
              }}
              className={`px-4 py-2 rounded-lg transition-colors ${
                viewMode === 'teacher'
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-accent hover:bg-accent/80'
              }`}
            >
              По преподавателям
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {viewMode === 'group' ? (
              <>
                {/* Institute filter */}
                <div>
                  <label className="block text-sm font-medium mb-2">Институт</label>
                  <select
                    value={selectedInstitute || ''}
                    onChange={(e) => handleInstituteChange(e.target.value ? Number(e.target.value) : null)}
                    className="w-full px-3 py-2 bg-background border rounded-lg focus:ring-2 focus:ring-primary"
                  >
                    <option value="">Выберите институт</option>
                    {institutes.map((institute) => (
                      <option key={institute.id} value={institute.id}>
                        {institute.name}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Group filter */}
                <div>
                  <label className="block text-sm font-medium mb-2">Группа</label>
                  <select
                    value={selectedGroup || ''}
                    onChange={(e) => handleGroupChange(e.target.value ? Number(e.target.value) : null)}
                    className="w-full px-3 py-2 bg-background border rounded-lg focus:ring-2 focus:ring-primary"
                    disabled={!selectedInstitute}
                  >
                    <option value="">Выберите группу</option>
                    {groups.map((group) => (
                      <option key={group.id} value={group.id}>
                        {group.name}
                      </option>
                    ))}
                  </select>
                </div>
              </>
            ) : (
              <>
                {/* Teacher autocomplete search */}
                <div className="md:col-span-3" ref={teacherSearchRef}>
                  <label className="block text-sm font-medium mb-2">
                    Поиск преподавателя
                    {selectedTeacherName && (
                      <span className="ml-2 text-xs px-2 py-1 bg-primary/10 text-primary rounded">
                        Выбран: {selectedTeacherName}
                      </span>
                    )}
                  </label>
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-muted-foreground z-10" />
                    <input
                      type="text"
                      placeholder="Начните вводить ФИО преподавателя (минимум 2 символа)..."
                      value={teacherSearchQuery}
                      onChange={(e) => handleTeacherSearchChange(e.target.value)}
                      onFocus={() => {
                        if (teachers.length > 0) {
                          setShowTeacherSuggestions(true)
                        }
                      }}
                      className="w-full pl-10 pr-10 py-3 bg-background border-2 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all"
                    />
                    
                    {(teacherSearchQuery || selectedTeacher) && (
                      <button
                        onClick={() => {
                          setSelectedTeacher(null)
                          setSelectedTeacherName('')
                          setTeacherSearchQuery('')
                          setTeachers([])
                          setLessons([])
                          setShowTeacherSuggestions(false)
                        }}
                        className="absolute right-3 top-1/2 transform -translate-y-1/2 h-6 w-6 flex items-center justify-center rounded-full hover:bg-accent text-muted-foreground hover:text-foreground transition-colors"
                      >
                        ✕
                      </button>
                    )}
                    
                    {showTeacherSuggestions && teachers.length > 0 && (
                      <div className="absolute z-50 w-full mt-1 bg-card border-2 border-primary/20 rounded-lg shadow-xl max-h-80 overflow-y-auto">
                        <div className="p-2 text-xs text-muted-foreground border-b bg-accent/30">
                          Найдено преподавателей: {teachers.length}
                        </div>
                        {teachers.slice(0, 50).map((teacher) => (
                          <button
                            key={teacher.id}
                            onClick={() => handleTeacherSelect(teacher)}
                            className={`w-full px-4 py-3 text-left hover:bg-primary/10 transition-colors border-b last:border-b-0 flex items-center gap-3 ${
                              selectedTeacher === teacher.id ? 'bg-primary/20 border-l-4 border-l-primary' : ''
                            }`}
                          >
                            <User className="h-5 w-5 text-primary flex-shrink-0" />
                            <div>
                              <div className="font-medium">{teacher.full_name}</div>
                              {teacher.sstu_profile_url && (
                                <div className="text-xs text-muted-foreground">
                                  СГТУ ID: {teacher.sstu_id}
                                </div>
                              )}
                            </div>
                          </button>
                        ))}
                        {teachers.length > 50 && (
                          <div className="p-3 text-xs text-center text-muted-foreground bg-accent/30">
                            Показано 50 из {teachers.length}. Уточните запрос для лучших результатов.
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </>
            )}

            {/* Weekday filter */}
            <div>
              <label className="block text-sm font-medium mb-2">День недели</label>
              <select
                value={selectedWeekday || ''}
                onChange={(e) => setSelectedWeekday(e.target.value ? Number(e.target.value) : null)}
                className="w-full px-3 py-2 bg-background border rounded-lg focus:ring-2 focus:ring-primary"
              >
                <option value="">Все дни</option>
                {WEEKDAYS.map((day, index) => (
                  <option key={index + 1} value={index + 1}>
                    {day}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Search - только для режима группы */}
          {viewMode === 'group' && (
            <div>
              <label className="block text-sm font-medium mb-2">Поиск по расписанию</label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-muted-foreground" />
                <input
                  type="text"
                  placeholder="Поиск по предмету, преподавателю или аудитории..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 bg-background border rounded-lg focus:ring-2 focus:ring-primary"
                />
              </div>
            </div>
          )}
        </div>
      )}

      {/* Schedule */}
      {!selectedGroup && !selectedTeacher ? (
        <div className="text-center py-12 bg-card border rounded-lg">
          <Calendar className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
          <h3 className="text-xl font-semibold mb-2">
            {viewMode === 'group' ? 'Выберите группу' : 'Выберите преподавателя'}
          </h3>
          <p className="text-muted-foreground">
            {viewMode === 'group'
              ? 'Выберите институт и группу, чтобы просмотреть расписание'
              : 'Начните вводить ФИО преподавателя для поиска'}
          </p>
        </div>
      ) : filteredLessons.length === 0 ? (
        <div className="text-center py-12 bg-card border rounded-lg">
          <Calendar className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
          <h3 className="text-xl font-semibold mb-2">Расписание не найдено</h3>
          <p className="text-muted-foreground">
            {searchQuery
              ? 'Попробуйте изменить параметры поиска'
              : 'Расписание для выбранной группы еще не загружено'}
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          {sortedDates.map((dateStr) => {
            const dateLessons = lessonsByDate[dateStr]
            const timeGroups = groupLessonsByTime(dateLessons)
            const date = new Date(dateStr)
            const isToday = date.toDateString() === new Date().toDateString()
            const isPast = date < new Date() && !isToday

            return (
              <div
                key={dateStr}
                className={`bg-card border rounded-lg overflow-hidden ${
                  isToday ? 'border-primary border-2' : ''
                } ${isPast ? 'opacity-75' : ''}`}
              >
                <div className={`px-6 py-3 border-b ${isToday ? 'bg-primary/10' : 'bg-accent/10'}`}>
                  <h3 className="font-semibold text-lg flex items-center gap-2">
                    <Calendar className={`h-5 w-5 ${isToday ? 'text-primary' : ''}`} />
                    {formatDateDisplay(dateStr)}
                    {isToday && (
                      <span className="ml-2 text-xs px-2 py-1 bg-primary text-primary-foreground rounded">
                        Сегодня
                      </span>
                    )}
                  </h3>
                </div>
                <div className="divide-y">
                  {Object.entries(timeGroups)
                    .sort(([keyA], [keyB]) => {
                      const numA = parseInt(keyA.split('-')[0])
                      const numB = parseInt(keyB.split('-')[0])
                      return numA - numB
                    })
                    .map(([timeKey, timeLessons]) => {
                      const firstLesson = timeLessons[0]

                      // Если только одно занятие
                      if (timeLessons.length === 1) {
                        const lesson = timeLessons[0]
                        return (
                          <div key={lesson.id} className="p-4 hover:bg-accent/50 transition-colors">
                            <div className="flex items-start gap-4">
                              <div className="flex-shrink-0 text-center min-w-[80px]">
                                <div className="text-2xl font-bold text-primary">
                                  {lesson.lesson_number}
                                </div>
                                <div className="text-sm text-muted-foreground flex items-center gap-1 justify-center mt-1">
                                  <Clock className="h-3 w-3" />
                                  {lesson.start_time.slice(0, 5)} - {lesson.end_time.slice(0, 5)}
                                </div>
                              </div>

                              <div className="flex-1 min-w-0">
                                <div className="flex items-start gap-2 mb-2">
                                  <h4 className="font-semibold text-lg">{lesson.subject_name}</h4>
                                  <span
                                    className={`px-2 py-1 rounded text-xs font-medium ${getLessonTypeColor(
                                      lesson.lesson_type
                                    )}`}
                                  >
                                    {lesson.lesson_type_display}
                                  </span>
                                </div>

                                <div className="space-y-1 text-sm text-muted-foreground">
                                  {viewMode === 'teacher' && lesson.group_name && (
                                    <div className="flex items-center gap-2 font-medium text-primary">
                                      <User className="h-4 w-4" />
                                      <span>Группа: {lesson.group_name}</span>
                                    </div>
                                  )}
                                  {lesson.teacher_name && (
                                    <div className="flex items-center gap-2">
                                      <User className="h-4 w-4" />
                                      <span>{lesson.teacher_name}</span>
                                    </div>
                                  )}
                                  {lesson.room && (
                                    <div className="flex items-center gap-2">
                                      <MapPin className="h-4 w-4" />
                                      <span>Аудитория {lesson.room}</span>
                                    </div>
                                  )}
                                </div>
                              </div>
                            </div>
                          </div>
                        )
                      }

                      // Несколько занятий в одно время (подгруппы)
                      return (
                        <div key={timeKey} className="p-4 hover:bg-accent/50 transition-colors bg-amber-50/50 dark:bg-amber-950/20">
                          <div className="flex items-start gap-4">
                            <div className="flex-shrink-0 text-center min-w-[80px]">
                              <div className="text-2xl font-bold text-primary">
                                {firstLesson.lesson_number}
                              </div>
                              <div className="text-sm text-muted-foreground flex items-center gap-1 justify-center mt-1">
                                <Clock className="h-3 w-3" />
                                {firstLesson.start_time.slice(0, 5)} - {firstLesson.end_time.slice(0, 5)}
                              </div>
                              <div className="mt-2 text-xs bg-amber-200 dark:bg-amber-800 px-2 py-1 rounded">
                                {timeLessons.length} подгр.
                              </div>
                            </div>

                            <div className="flex-1 min-w-0 space-y-3">
                              {timeLessons.map((lesson, idx) => (
                                <div key={lesson.id} className="pb-3 border-b last:border-b-0 last:pb-0">
                                  <div className="flex items-start gap-2 mb-2">
                                    <div className="flex-shrink-0 w-6 h-6 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-xs font-bold">
                                      {idx + 1}
                                    </div>
                                    <div className="flex-1">
                                      <h4 className="font-semibold">{lesson.subject_name}</h4>
                                      <span
                                        className={`inline-block mt-1 px-2 py-1 rounded text-xs font-medium ${getLessonTypeColor(
                                          lesson.lesson_type
                                        )}`}
                                      >
                                        {lesson.lesson_type_display}
                                      </span>
                                    </div>
                                  </div>

                                  <div className="space-y-1 text-sm text-muted-foreground ml-8">
                                    {viewMode === 'teacher' && lesson.group_name && (
                                      <div className="flex items-center gap-2 font-medium text-primary">
                                        <User className="h-4 w-4" />
                                        <span>Группа: {lesson.group_name}</span>
                                      </div>
                                    )}
                                    {lesson.teacher_name && (
                                      <div className="flex items-center gap-2">
                                        <User className="h-4 w-4" />
                                        <span>{lesson.teacher_name}</span>
                                      </div>
                                    )}
                                    {lesson.room && (
                                      <div className="flex items-center gap-2">
                                        <MapPin className="h-4 w-4" />
                                        <span>Аудитория {lesson.room}</span>
                                      </div>
                                    )}
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>
                      )
                    })}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
