import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function getUserDisplayName(user: { first_name?: string; last_name?: string; username?: string; email?: string } | null | undefined): string {
  if (!user) return 'Пользователь'
  
  // Если есть имя и фамилия - объединить их
  if (user.first_name && user.last_name) {
    return `${user.first_name} ${user.last_name}`
  }
  
  // Если есть только имя или только фамилия
  if (user.first_name) {
    return user.first_name
  }
  
  if (user.last_name) {
    return user.last_name
  }
  
  // Если есть username - использовать его
  if (user.username) {
    return user.username
  }
  
  // Fallback на email
  return user.email || 'Пользователь'
}

export function formatDate(date: string | Date): string {
  return new Date(date).toLocaleDateString('ru-RU', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

export function formatDateTime(date: string | Date): string {
  return new Date(date).toLocaleString('ru-RU', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

