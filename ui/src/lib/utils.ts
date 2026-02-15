import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"
import type { Locale } from './i18n'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(isoStr: string, locale: Locale = 'fr'): string {
  if (!isoStr) return ''
  try {
    const d = new Date(isoStr)
    if (isNaN(d.getTime())) return isoStr
    return d.toLocaleString(locale === 'fr' ? 'fr-FR' : 'en-US', {
      day: '2-digit', month: '2-digit', year: 'numeric',
      hour: '2-digit', minute: '2-digit'
    })
  } catch {
    return isoStr
  }
}

export function timeFromNow(isoStr: string, locale: Locale = 'fr'): string {
  const diff = new Date(isoStr).getTime() - Date.now()
  if (diff <= 0) return locale === 'fr' ? 'maintenant' : 'now'
  const mins = Math.round(diff / 60000)
  if (mins < 60) return locale === 'fr' ? `dans ${mins}min` : `in ${mins}min`
  const hours = Math.round(mins / 60)
  if (mins < 1440) return locale === 'fr' ? `dans ${hours}h` : `in ${hours}h`
  const days = Math.round(mins / 1440)
  return locale === 'fr' ? `dans ${days}j` : `in ${days}d`
}
