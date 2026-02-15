import { createContext, useContext, useState, useCallback, type ReactNode } from 'react'
import { AlertTriangle } from 'lucide-react'
import { useSettings } from '@/contexts/SettingsContext'

interface ConfirmOptions {
  message: string
  confirmText?: string
  cancelText?: string
  danger?: boolean
}

interface ConfirmContextType {
  confirm: (options: ConfirmOptions) => Promise<boolean>
}

const ConfirmContext = createContext<ConfirmContextType | null>(null)

export function ConfirmProvider({ children }: { children: ReactNode }) {
  const { t } = useSettings()
  const [state, setState] = useState<{
    open: boolean
    options: ConfirmOptions
    resolve: ((value: boolean) => void) | null
  }>({
    open: false,
    options: { message: '' },
    resolve: null,
  })

  const confirm = useCallback((options: ConfirmOptions): Promise<boolean> => {
    return new Promise((resolve) => {
      setState({ open: true, options, resolve })
    })
  }, [])

  const handleClose = (result: boolean) => {
    state.resolve?.(result)
    setState({ open: false, options: { message: '' }, resolve: null })
  }

  return (
    <ConfirmContext.Provider value={{ confirm }}>
      {children}
      {state.open && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <div className="w-full max-w-sm mx-4 bg-bg border border-border rounded-xl shadow-2xl overflow-hidden">
            <div className="p-5">
              <div className="flex items-start gap-3">
                <div className={`p-2 rounded-full ${state.options.danger ? 'bg-error-light' : 'bg-warning-light'}`}>
                  <AlertTriangle size={20} className={state.options.danger ? 'text-error' : 'text-warning'} />
                </div>
                <p className="text-sm text-text leading-relaxed pt-1">{state.options.message}</p>
              </div>
            </div>
            <div className="flex gap-2 px-5 py-3 bg-bg-secondary border-t border-border">
              <button
                onClick={() => handleClose(false)}
                className="flex-1 px-4 py-2 text-sm font-medium text-text-secondary border border-border rounded-lg hover:bg-bg-hover transition-colors"
              >
                {state.options.cancelText || t('common.cancel')}
              </button>
              <button
                onClick={() => handleClose(true)}
                className={`flex-1 px-4 py-2 text-sm font-medium text-white rounded-lg transition-colors ${
                  state.options.danger ? 'bg-error hover:bg-red-700' : 'bg-accent hover:bg-accent-hover'
                }`}
              >
                {state.options.confirmText || t('common.confirm')}
              </button>
            </div>
          </div>
        </div>
      )}
    </ConfirmContext.Provider>
  )
}

export function useConfirm() {
  const ctx = useContext(ConfirmContext)
  if (!ctx) throw new Error('useConfirm must be used within ConfirmProvider')
  return ctx.confirm
}
