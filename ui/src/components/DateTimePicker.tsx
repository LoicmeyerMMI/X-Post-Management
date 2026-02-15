import { useState, useRef, useEffect } from 'react'
import { Clock, Calendar, ChevronLeft, ChevronRight, X } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useSettings } from '@/contexts/SettingsContext'
import { MONTHS_SHORT, DAYS_SHORT } from '@/lib/i18n'

interface DateTimePickerProps {
  value: string // 'YYYY-MM-DDTHH:mm' or ''
  onChange: (value: string) => void
}

const QUICK_TIMES = ['08:00', '09:00', '10:00', '12:00', '14:00', '16:00', '18:00', '20:00']

export function DateTimePicker({ value, onChange }: DateTimePickerProps) {
  const { t, locale } = useSettings()
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  const selectedDate = value ? value.slice(0, 10) : ''
  const selectedTime = value ? value.slice(11, 16) : ''

  const now = new Date()
  const [viewYear, setViewYear] = useState(selectedDate ? parseInt(selectedDate.slice(0, 4)) : now.getFullYear())
  const [viewMonth, setViewMonth] = useState(selectedDate ? parseInt(selectedDate.slice(5, 7)) - 1 : now.getMonth())

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    if (open) document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [open])

  const todayStr = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`

  // Minimum selectable time: now + 5 minutes
  const minDate = new Date(now.getTime() + 5 * 60 * 1000)
  const minTimeStr = `${String(minDate.getHours()).padStart(2, '0')}:${String(minDate.getMinutes()).padStart(2, '0')}`

  const clampTime = (dateStr: string, timeStr: string): string => {
    if (dateStr === todayStr && timeStr < minTimeStr) return minTimeStr
    return timeStr
  }

  const isQuickDisabled = (daysFromNow: number, time: string): boolean => {
    if (daysFromNow > 0) return false
    return time < minTimeStr
  }

  const setDate = (dateStr: string) => {
    const time = clampTime(dateStr, selectedTime || '12:00')
    onChange(`${dateStr}T${time}`)
  }

  const setTime = (timeStr: string) => {
    const date = selectedDate || todayStr
    const clamped = clampTime(date, timeStr)
    onChange(`${date}T${clamped}`)
  }

  const setQuick = (daysFromNow: number, time: string) => {
    const d = new Date()
    d.setDate(d.getDate() + daysFromNow)
    const dateStr = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
    onChange(`${dateStr}T${time}`)
    setOpen(false)
  }

  const clear = () => {
    onChange('')
    setOpen(false)
  }

  const firstDay = new Date(viewYear, viewMonth, 1).getDay()
  const startOffset = firstDay === 0 ? 6 : firstDay - 1
  const daysInMonth = new Date(viewYear, viewMonth + 1, 0).getDate()

  const cells: (number | null)[] = []
  for (let i = 0; i < startOffset; i++) cells.push(null)
  for (let d = 1; d <= daysInMonth; d++) cells.push(d)
  const remaining = cells.length % 7 === 0 ? 0 : 7 - (cells.length % 7)
  for (let i = 0; i < remaining; i++) cells.push(null)

  const prevMonth = () => {
    if (viewMonth === 0) { setViewMonth(11); setViewYear(y => y - 1) }
    else setViewMonth(m => m - 1)
  }
  const nextMonth = () => {
    if (viewMonth === 11) { setViewMonth(0); setViewYear(y => y + 1) }
    else setViewMonth(m => m + 1)
  }

  const formatDisplay = () => {
    if (!value) return ''
    const d = new Date(value)
    const loc = locale === 'fr' ? 'fr-FR' : 'en-US'
    return d.toLocaleDateString(loc, { day: 'numeric', month: 'short' }) + ' ' +
      d.toLocaleTimeString(loc, { hour: '2-digit', minute: '2-digit' })
  }

  return (
    <div className="relative" ref={ref}>
      <div
        className="flex items-center gap-2 px-2.5 py-1.5 text-xs border border-border rounded-md cursor-pointer hover:border-accent bg-bg min-w-[200px]"
        onClick={() => setOpen(!open)}
      >
        <Calendar size={13} className="text-text-muted shrink-0" />
        <span className={value ? 'text-text' : 'text-text-muted'}>
          {value ? formatDisplay() : t('dt.choose')}
        </span>
        {value && (
          <button
            onClick={e => { e.stopPropagation(); clear() }}
            className="ml-auto text-text-muted hover:text-text"
          >
            <X size={12} />
          </button>
        )}
      </div>

      {open && (
        <div className="absolute top-full left-0 mt-1 z-50 bg-bg border border-border rounded-lg shadow-lg w-[300px]">
          {/* Quick shortcuts */}
          <div className="px-3 pt-3 pb-2 border-b border-border">
            <p className="text-[10px] text-text-muted font-medium uppercase tracking-wider mb-2">{t('dt.shortcuts')}</p>
            <div className="flex flex-wrap gap-1.5">
              <button onClick={() => setQuick(0, '18:00')} disabled={isQuickDisabled(0, '18:00')} className="px-2 py-1 text-[11px] rounded-md bg-bg-secondary hover:bg-bg-hover text-text-secondary transition-colors disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-bg-secondary">{t('dt.today18')}</button>
              <button onClick={() => setQuick(1, '09:00')} className="px-2 py-1 text-[11px] rounded-md bg-bg-secondary hover:bg-bg-hover text-text-secondary transition-colors">{t('dt.tomorrow9')}</button>
              <button onClick={() => setQuick(1, '12:00')} className="px-2 py-1 text-[11px] rounded-md bg-bg-secondary hover:bg-bg-hover text-text-secondary transition-colors">{t('dt.tomorrow12')}</button>
              <button onClick={() => setQuick(1, '18:00')} className="px-2 py-1 text-[11px] rounded-md bg-bg-secondary hover:bg-bg-hover text-text-secondary transition-colors">{t('dt.tomorrow18')}</button>
              <button onClick={() => setQuick(7, '09:00')} className="px-2 py-1 text-[11px] rounded-md bg-bg-secondary hover:bg-bg-hover text-text-secondary transition-colors">{t('dt.week9')}</button>
            </div>
          </div>

          {/* Calendar */}
          <div className="px-3 pt-2 pb-1">
            <div className="flex items-center justify-between mb-2">
              <button onClick={prevMonth} className="p-1 rounded hover:bg-bg-hover transition-colors">
                <ChevronLeft size={14} className="text-text-secondary" />
              </button>
              <span className="text-xs font-semibold text-text">{MONTHS_SHORT[locale][viewMonth]} {viewYear}</span>
              <button onClick={nextMonth} className="p-1 rounded hover:bg-bg-hover transition-colors">
                <ChevronRight size={14} className="text-text-secondary" />
              </button>
            </div>

            <div className="grid grid-cols-7 gap-0">
              {DAYS_SHORT[locale].map(d => (
                <div key={d} className="text-center text-[10px] font-medium text-text-muted py-1">{d}</div>
              ))}
              {cells.map((day, i) => {
                if (day === null) return <div key={`e-${i}`} className="h-7" />
                const dateStr = `${viewYear}-${String(viewMonth + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`
                const isSelected = dateStr === selectedDate
                const isToday = dateStr === todayStr
                const isPast = dateStr < todayStr
                return (
                  <button
                    key={dateStr}
                    onClick={() => setDate(dateStr)}
                    disabled={isPast}
                    className={cn(
                      'h-7 text-[11px] rounded-md transition-colors',
                      isPast && 'text-text-muted/40 cursor-not-allowed',
                      !isPast && !isSelected && 'hover:bg-bg-hover text-text',
                      isSelected && 'bg-accent text-white font-semibold',
                      isToday && !isSelected && 'font-bold text-accent'
                    )}
                  >
                    {day}
                  </button>
                )
              })}
            </div>
          </div>

          {/* Time picker */}
          <div className="px-3 pt-1 pb-3 border-t border-border mt-1">
            <div className="flex items-center gap-2 mb-2">
              <Clock size={12} className="text-text-muted" />
              <span className="text-[10px] text-text-muted font-medium uppercase tracking-wider">{t('dt.time')}</span>
            </div>
            <div className="flex items-center gap-2">
              <input
                type="time"
                value={selectedTime}
                onChange={e => setTime(e.target.value)}
                className="px-2 py-1 text-xs font-mono border border-border rounded-md focus:outline-none focus:border-accent bg-bg text-text w-[90px]"
              />
              <div className="flex flex-wrap gap-1 flex-1">
                {QUICK_TIMES.map(qt => {
                  const isDisabled = (selectedDate === todayStr || !selectedDate) && qt < minTimeStr
                  return (
                    <button
                      key={qt}
                      onClick={() => setTime(qt)}
                      disabled={isDisabled}
                      className={cn(
                        'px-1.5 py-0.5 text-[10px] rounded transition-colors',
                        isDisabled && 'opacity-40 cursor-not-allowed',
                        !isDisabled && selectedTime === qt ? 'bg-accent text-white' : !isDisabled ? 'bg-bg-secondary hover:bg-bg-hover text-text-secondary' : 'bg-bg-secondary text-text-secondary'
                      )}
                    >
                      {qt.replace(':00', 'h')}
                    </button>
                  )
                })}
              </div>
              <button
                onClick={() => setOpen(false)}
                disabled={!value}
                className={cn(
                  'px-3 py-1 text-[11px] font-semibold rounded-md transition-colors',
                  value
                    ? 'bg-accent text-white hover:bg-accent/90'
                    : 'bg-bg-secondary text-text-muted cursor-not-allowed'
                )}
              >
                {t('dt.ok')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
