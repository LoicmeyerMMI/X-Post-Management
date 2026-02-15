import { useState, useRef, useEffect } from 'react'
import { Smile } from 'lucide-react'
import data from '@emoji-mart/data'
import Picker from '@emoji-mart/react'
import i18nFr from '@emoji-mart/data/i18n/fr.json'
import { useSettings } from '@/contexts/SettingsContext'

interface EmojiPickerProps {
  onSelect: (emoji: string) => void
}

export function EmojiPicker({ onSelect }: EmojiPickerProps) {
  const { theme } = useSettings()
  const [open, setOpen] = useState(false)
  const [openUp, setOpenUp] = useState(true)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    if (open) document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [open])

  const toggle = () => {
    if (!open && ref.current) {
      const rect = ref.current.getBoundingClientRect()
      // 420px = approximate picker height
      setOpenUp(rect.top > 420)
    }
    setOpen(!open)
  }

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        onClick={toggle}
        className="w-8 h-8 flex items-center justify-center rounded-md text-accent hover:bg-accent-light transition-colors"
        title="Ajouter un emoji"
      >
        <Smile size={18} />
      </button>
      {open && (
        <div className={`absolute left-0 z-50 shadow-lg rounded-xl overflow-hidden max-h-[380px] ${openUp ? 'bottom-10' : 'top-10'}`}>
          <Picker
            data={data}
            onEmojiSelect={(emoji: { native: string }) => {
              onSelect(emoji.native)
              setOpen(false)
            }}
            theme={theme === 'dark' ? 'dark' : 'light'}
            locale="fr"
            i18n={i18nFr}
            previewPosition="none"
            skinTonePosition="none"
            searchPosition="top"
            perLine={7}
            maxFrequentRows={1}
            navPosition="bottom"
            dynamicWidth={false}
          />
        </div>
      )}
    </div>
  )
}
