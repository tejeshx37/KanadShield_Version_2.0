import { useState } from 'react'
import { SUPPORTED_LANGUAGES } from '@/lib/env'
import { Card, CardBody } from '@/components/ui/Card'
import { useOfflineSync } from '@/lib/useOfflineSync'

export function SettingsPage() {
  const [uiLanguage, setUiLanguage] = useState(localStorage.getItem('kanadshield-ui-language') ?? 'en')
  const { status, pendingCount } = useOfflineSync()

  function changeLanguage(lang: string) {
    setUiLanguage(lang)
    localStorage.setItem('kanadshield-ui-language', lang)
  }

  return (
    <div className="mx-auto max-w-xl space-y-6">
      <h1 className="font-serif-display text-2xl font-semibold text-ink-950">Settings</h1>

      <Card>
        <CardBody className="space-y-2">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-ink-500">Interface language</h2>
          <p className="text-xs text-ink-500">
            This controls the app&apos;s UI chrome only — document content translation is a separate toggle shown on
            each document page.
          </p>
          <div className="flex gap-2">
            {SUPPORTED_LANGUAGES.map((lang) => (
              <button
                key={lang}
                onClick={() => changeLanguage(lang)}
                className={`rounded-md px-3 py-1.5 text-sm ${uiLanguage === lang ? 'bg-brand-700 text-white' : 'bg-ink-100 text-ink-700'}`}
              >
                {lang.toUpperCase()}
              </button>
            ))}
          </div>
        </CardBody>
      </Card>

      <Card>
        <CardBody className="space-y-2">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-ink-500">Offline sync status</h2>
          <p className="text-sm text-ink-700">
            {status === 'syncing' && 'Syncing queued offline actions…'}
            {status === 'synced' && 'All offline actions are synced.'}
            {status === 'idle' && (pendingCount > 0 ? `${pendingCount} action(s) waiting to sync.` : 'Nothing queued.')}
          </p>
        </CardBody>
      </Card>
    </div>
  )
}
