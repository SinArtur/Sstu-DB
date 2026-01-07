import { Outlet } from 'react-router-dom'
import { useState, useEffect } from 'react'
import Sidebar from './Sidebar'
import Header from './Header'
import ThemeToggle from './ThemeToggle'

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  // Prevent body scroll when sidebar is open on mobile
  useEffect(() => {
    if (sidebarOpen) {
      // Check if mobile (screen width < 768px)
      if (window.innerWidth < 768) {
        document.body.style.overflow = 'hidden'
      }
    } else {
      document.body.style.overflow = ''
    }

    return () => {
      document.body.style.overflow = ''
    }
  }, [sidebarOpen])

  return (
    <div className="flex h-screen bg-background">
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="flex-1 flex flex-col overflow-hidden w-full md:w-auto relative z-10">
        <Header 
          onMenuClick={() => {
            // Use requestAnimationFrame to ensure state update happens after current render
            requestAnimationFrame(() => {
              setSidebarOpen(true)
            })
          }} 
        />
        <main className="flex-1 overflow-y-auto p-4 md:p-6">
          <Outlet />
        </main>
      </div>
      <ThemeToggle />
    </div>
  )
}
