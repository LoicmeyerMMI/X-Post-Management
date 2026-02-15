import { Sun, Moon } from 'lucide-react'
import { useSettings } from '@/contexts/SettingsContext'

interface PageHeaderProps {
  title: string
  description?: string
  actions?: React.ReactNode
}

export function PageHeader({ title, description, actions }: PageHeaderProps) {
  const { theme, setTheme } = useSettings()

  return (
    <div className="flex items-center justify-between px-6 py-4 border-b border-border bg-bg sticky top-0 z-10">
      <div>
        <h1 className="text-lg font-semibold text-text">{title}</h1>
        {description && (
          <p className="text-xs text-text-muted mt-0.5">{description}</p>
        )}
      </div>
      <div className="flex items-center gap-2">
        {actions && <>{actions}</>}
        <button
          onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}
          className="flex items-center justify-center w-8 h-8 text-text-secondary border border-border rounded-md hover:bg-bg-hover transition-colors"
          title={theme === 'light' ? 'Dark mode' : 'Light mode'}
        >
          {theme === 'light' ? <Moon size={15} /> : <Sun size={15} />}
        </button>
      </div>
    </div>
  )
}
