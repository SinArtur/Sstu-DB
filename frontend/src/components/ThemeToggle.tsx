import { Moon, Sun } from 'lucide-react'
import { useThemeStore } from '@/store/themeStore'

export default function ThemeToggle() {
  const { theme, toggleTheme } = useThemeStore()

  return (
    <button
      onClick={toggleTheme}
      className="fixed bottom-4 right-4 md:bottom-6 md:left-64 md:right-auto z-50 flex items-center justify-center w-12 h-12 md:w-14 md:h-14 rounded-full bg-card border border-border shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-110 group backdrop-blur-sm dark:bg-card/90 dark:border-border/50"
      title={theme === 'dark' ? 'Переключить на светлую тему' : 'Переключить на темную тему'}
    >
      {theme === 'dark' ? (
        <Sun className="h-5 w-5 md:h-6 md:w-6 text-yellow-400 group-hover:rotate-180 transition-transform duration-500" />
      ) : (
        <Moon className="h-5 w-5 md:h-6 md:w-6 text-foreground group-hover:rotate-12 transition-transform duration-300" />
      )}
    </button>
  )
}

