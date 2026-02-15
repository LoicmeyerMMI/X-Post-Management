import { createContext, useContext, useState, useCallback, type ReactNode } from 'react'

interface ComposerState {
  text: string
  setText: (text: string) => void
  scheduledAt: string
  setScheduledAt: (date: string) => void
  imageFile: File | null
  setImageFile: (file: File | null) => void
  imagePreview: string | null
  setImagePreview: (preview: string | null) => void
  resetComposer: () => void
}

const ComposerContext = createContext<ComposerState | null>(null)

export function ComposerProvider({ children }: { children: ReactNode }) {
  const [text, setTextRaw] = useState(() => localStorage.getItem('composer_text') || '')
  const [scheduledAt, setScheduledAtRaw] = useState(() => localStorage.getItem('composer_scheduled') || '')
  const [imageFile, setImageFile] = useState<File | null>(null)
  const [imagePreview, setImagePreview] = useState<string | null>(null)

  const setText = useCallback((v: string) => {
    setTextRaw(v)
    localStorage.setItem('composer_text', v)
  }, [])

  const setScheduledAt = useCallback((v: string) => {
    setScheduledAtRaw(v)
    localStorage.setItem('composer_scheduled', v)
  }, [])

  const resetComposer = useCallback(() => {
    setTextRaw('')
    setScheduledAtRaw('')
    setImageFile(null)
    setImagePreview(null)
    localStorage.removeItem('composer_text')
    localStorage.removeItem('composer_scheduled')
  }, [])

  return (
    <ComposerContext.Provider value={{
      text, setText,
      scheduledAt, setScheduledAt,
      imageFile, setImageFile,
      imagePreview, setImagePreview,
      resetComposer,
    }}>
      {children}
    </ComposerContext.Provider>
  )
}

export function useComposer() {
  const ctx = useContext(ComposerContext)
  if (!ctx) throw new Error('useComposer must be used within ComposerProvider')
  return ctx
}
