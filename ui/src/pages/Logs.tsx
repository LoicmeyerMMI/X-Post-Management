import { useState, useEffect, useRef, useCallback } from 'react'
import { RefreshCw, Copy } from 'lucide-react'
import { toast } from 'sonner'
import { PageHeader } from '@/components/PageHeader'
import { useSettings } from '@/contexts/SettingsContext'
import * as api from '@/lib/api'

export function Logs() {
  const { t } = useSettings()
  const [logs, setLogs] = useState('')
  const [loading, setLoading] = useState(true)
  const [autoRefresh, setAutoRefresh] = useState(true)
  const preRef = useRef<HTMLPreElement>(null)

  const refresh = useCallback(async () => {
    try {
      const data = await api.fetchLogs()
      setLogs(data.logs || t('logs.noLogs'))
      if (preRef.current) {
        preRef.current.scrollTop = preRef.current.scrollHeight
      }
    } catch { /* ignore */ }
    finally { setLoading(false) }
  }, [t])

  useEffect(() => {
    refresh()
  }, [refresh])

  useEffect(() => {
    if (!autoRefresh) return
    const interval = setInterval(refresh, 5000)
    return () => clearInterval(interval)
  }, [autoRefresh, refresh])

  const copyLogs = () => {
    navigator.clipboard.writeText(logs)
    toast.success(t('logs.copied'))
  }

  return (
    <div className="flex flex-col h-full">
      <PageHeader
        title={t('logs.title')}
        description={t('logs.desc')}
        actions={
          <div className="flex items-center gap-2">
            <label className="flex items-center gap-1.5 text-xs text-text-muted cursor-pointer select-none">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={e => setAutoRefresh(e.target.checked)}
                className="accent-accent"
              />
              {t('logs.autoRefresh')}
            </label>
            <button
              onClick={copyLogs}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-text-secondary border border-border rounded-md hover:bg-bg-hover transition-colors"
            >
              <Copy size={13} /> {t('common.copy')}
            </button>
            <button
              onClick={refresh}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-text-secondary border border-border rounded-md hover:bg-bg-hover transition-colors"
            >
              <RefreshCw size={13} /> {t('common.refresh')}
            </button>
          </div>
        }
      />

      <pre
        ref={preRef}
        className="flex-1 m-3 p-4 bg-[#111827] text-[#e5e7eb] font-mono text-xs leading-relaxed rounded-lg overflow-y-auto whitespace-pre-wrap break-all select-text"
      >
        {loading ? t('common.loading') : logs}
      </pre>
    </div>
  )
}
