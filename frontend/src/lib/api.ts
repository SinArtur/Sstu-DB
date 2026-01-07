import axios from 'axios'
import { useAuthStore } from '@/store/authStore'

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    const { accessToken } = useAuthStore.getState()
    if (accessToken) {
      config.headers.Authorization = `Bearer ${accessToken}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        const { refreshToken } = useAuthStore.getState()
        if (!refreshToken) {
          throw new Error('No refresh token')
        }

        const response = await axios.post('/api/auth/token/refresh/', {
          refresh: refreshToken,
        })

        const { access } = response.data
        const { setAuth } = useAuthStore.getState()
        const { user } = useAuthStore.getState()
        
        if (user) {
          setAuth(user, access, refreshToken)
        }

        originalRequest.headers.Authorization = `Bearer ${access}`
        return api(originalRequest)
      } catch (refreshError) {
        useAuthStore.getState().logout()
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  }
)

export default api

// Schedule API
export const scheduleApi = {
  // Get all institutes
  getInstitutes: () => api.get('/schedule/institutes/'),
  
  // Get all groups
  getGroups: (params?: any) => api.get('/schedule/groups/', { params }),
  
  // Get group details
  getGroup: (id: number) => api.get(`/schedule/groups/${id}/`),
  
  // Get user's group
  getMyGroup: () => api.get('/schedule/groups/my_group/'),
  
  // Get all teachers
  getTeachers: (params?: any) => api.get('/schedule/teachers/', { params }),
  
  // Get all subjects
  getSubjects: (params?: any) => api.get('/schedule/subjects/', { params }),
  
  // Get lessons
  getLessons: (params?: any) => api.get('/schedule/lessons/', { params }),
  
  // Get user's schedule
  getMySchedule: (params?: any) => api.get('/schedule/lessons/my_schedule/', { params }),
  
  // Get weekly schedule
  getWeeklySchedule: (groupId: number) => api.get('/schedule/lessons/weekly/', { params: { group: groupId } }),
  
  // Get schedule updates
  getUpdates: () => api.get('/schedule/updates/'),
  
  // Get latest update
  getLatestUpdate: () => api.get('/schedule/updates/latest/'),
  
  // Trigger sync (moderators/admins only)
  triggerSync: () => api.post('/schedule/updates/trigger_sync/'),
}

