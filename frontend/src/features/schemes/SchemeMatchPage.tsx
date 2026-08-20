import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { matchSchemes } from '@/api/personalization'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { Card, CardBody } from '@/components/ui/Card'
import { useOnlineStatus } from '@/lib/useOnlineStatus'

export function SchemeMatchPage() {
  const [age, setAge] = useState('')
  const [state, setState] = useState('Gujarat')
  const [incomeAnnual, setIncomeAnnual] = useState('')
  const isOnline = useOnlineStatus()

  const mutation = useMutation({
    mutationFn: () =>
      matchSchemes({
        age: age ? Number(age) : undefined,
        state: state || undefined,
        income_annual: incomeAnnual ? Number(incomeAnnual) : undefined,
      }),
  })

  if (!isOnline) {
    return <p className="text-sm text-ink-500">Scheme matching is disabled offline — connect to check eligibility.</p>
  }

  return (
    <div className="mx-auto max-w-xl space-y-6">
      <h1 className="font-serif-display text-2xl font-semibold text-ink-950">Check Scheme Eligibility</h1>
      <form
        className="space-y-3"
        onSubmit={(e) => {
          e.preventDefault()
          mutation.mutate()
        }}
      >
        <label className="block text-sm text-ink-700">
          Age
          <Input type="number" value={age} onChange={(e) => setAge(e.target.value)} className="mt-1" />
        </label>
        <label className="block text-sm text-ink-700">
          State
          <Input value={state} onChange={(e) => setState(e.target.value)} className="mt-1" />
        </label>
        <label className="block text-sm text-ink-700">
          Annual income (INR)
          <Input type="number" value={incomeAnnual} onChange={(e) => setIncomeAnnual(e.target.value)} className="mt-1" />
        </label>
        <Button type="submit" className="w-full" disabled={mutation.isPending}>
          {mutation.isPending ? 'Checking…' : 'Check eligibility'}
        </Button>
      </form>

      {mutation.data && (
        <div className="space-y-3">
          {mutation.data.results.map((r) => (
            <Card key={r.scheme_id}>
              <CardBody>
                <div className="flex items-center justify-between">
                  <h2 className="font-medium text-ink-900">{r.scheme_name}</h2>
                  {r.is_potentially_eligible && (
                    <span className="rounded-full bg-brand-100 px-2 py-0.5 text-xs font-semibold text-brand-700">
                      Appears potentially eligible
                    </span>
                  )}
                </div>
                <p className="mt-1 text-sm text-ink-700">{r.explanation}</p>
                {r.missing_conditions.length > 0 && (
                  <p className="mt-1 text-xs text-ink-500">Missing: {r.missing_conditions.join('; ')}</p>
                )}
                {r.required_documents.length > 0 && (
                  <p className="mt-1 text-xs text-ink-500">Required documents: {r.required_documents.join(', ')}</p>
                )}
                {r.official_source && (
                  <a href={r.official_source} target="_blank" rel="noreferrer" className="mt-1 inline-block text-xs text-brand-700 hover:underline">
                    Official source ↗
                  </a>
                )}
              </CardBody>
            </Card>
          ))}
          {mutation.data.results.length === 0 && <p className="text-sm text-ink-500">No schemes configured yet.</p>}
        </div>
      )}
    </div>
  )
}
