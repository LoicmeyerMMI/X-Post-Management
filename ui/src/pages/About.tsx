import { Info, HelpCircle, ChevronDown } from 'lucide-react'
import { useState } from 'react'
import { PageHeader } from '@/components/PageHeader'
import { useSettings } from '@/contexts/SettingsContext'
import { cn } from '@/lib/utils'
import type { TranslationKey } from '@/lib/i18n'

interface FaqItem {
  questionKey: TranslationKey
  answerKey: TranslationKey
}

const faqItems: FaqItem[] = [
  { questionKey: 'about.faq1Question', answerKey: 'about.faq1Answer' },
  { questionKey: 'about.faq3Question', answerKey: 'about.faq3Answer' },
  { questionKey: 'about.faq4Question', answerKey: 'about.faq4Answer' },
  { questionKey: 'about.faq5Question', answerKey: 'about.faq5Answer' },
  { questionKey: 'about.faq6Question', answerKey: 'about.faq6Answer' },
  { questionKey: 'about.faq7Question', answerKey: 'about.faq7Answer' },
]

export function About() {
  const { t } = useSettings()
  const [openFaq, setOpenFaq] = useState<number | null>(null)

  return (
    <div>
      <PageHeader title={t('about.title')} description={t('about.desc')} />

      {/* Description */}
      <div className="px-6 py-5 border-b border-border">
        <div className="flex items-start gap-4 p-5 bg-bg-secondary/50 rounded-xl border border-border">
          <div className="w-12 h-12 rounded-lg bg-accent-light flex items-center justify-center shrink-0">
            <Info size={24} className="text-accent" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-text mb-2">{t('about.whatIs')}</h3>
            <p className="text-sm text-text-secondary leading-relaxed">
              {t('about.description')}
            </p>
            <ul className="mt-3 space-y-1.5 text-sm text-text-secondary">
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-accent shrink-0" />
                {t('about.feature1')}
              </li>
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-accent shrink-0" />
                {t('about.feature2')}
              </li>
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-accent shrink-0" />
                {t('about.feature3')}
              </li>
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-accent shrink-0" />
                {t('about.feature4')}
              </li>
            </ul>
          </div>
        </div>
      </div>

      {/* FAQ */}
      <div className="px-6 py-5">
        <div className="flex items-center gap-2 mb-4">
          <HelpCircle size={22} className="text-accent" />
          <h3 className="text-sm font-semibold text-text">{t('about.faqTitle')}</h3>
        </div>

        <div className="space-y-2">
          {faqItems.map((item, index) => (
            <div
              key={index}
              className="border border-border rounded-lg overflow-hidden"
            >
              <button
                onClick={() => setOpenFaq(openFaq === index ? null : index)}
                className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-bg-hover transition-colors"
              >
                <span className="text-sm font-medium text-text">{t(item.questionKey)}</span>
                <ChevronDown
                  size={16}
                  className={cn(
                    'text-text-muted transition-transform',
                    openFaq === index && 'rotate-180'
                  )}
                />
              </button>
              <div
                className={cn(
                  'grid transition-all duration-200 ease-in-out',
                  openFaq === index ? 'grid-rows-[1fr] opacity-100' : 'grid-rows-[0fr] opacity-0'
                )}
              >
                <div className="overflow-hidden">
                  <div className="px-4 pb-3 text-sm text-text-secondary leading-relaxed">
                    {t(item.answerKey)}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
