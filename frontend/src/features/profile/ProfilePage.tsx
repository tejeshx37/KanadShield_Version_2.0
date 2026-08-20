import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { deleteCitizenProfile, fetchCitizenProfile, revokeCitizenConsent, upsertCitizenProfile } from '@/api/personalization'
import { useAuthStore } from '@/store/authStore'
import { Card, CardBody } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'

export function ProfilePage() {
  const user = useAuthStore((s) => s.user)
  const [ageRange, setAgeRange] = useState('')
  const [state, setState] = useState('')

  const profileQuery = useQuery({ queryKey: ['citizen-profile'], queryFn: fetchCitizenProfile, retry: false })

  const saveMutation = useMutation({
    mutationFn: () => upsertCitizenProfile({ age_range: ageRange || undefined, state: state || undefined }),
  })
  const revokeMutation = useMutation({ mutationFn: revokeCitizenConsent })
  const deleteMutation = useMutation({ mutationFn: deleteCitizenProfile })

  return (
    <div className="mx-auto max-w-xl space-y-6">
      <h1 className="font-serif-display text-2xl font-semibold text-ink-950">Profile</h1>
      <Card>
        <CardBody>
          <p className="text-sm text-ink-700">Email: {user?.email}</p>
          <p className="text-sm text-ink-700">Role: {user?.role}</p>
        </CardBody>
      </Card>

      <Card>
        <CardBody className="space-y-3">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-ink-500">Citizen Profile (for scheme matching)</h2>
          <p className="text-xs text-ink-500">
            Only derived attributes are stored — never raw identity documents. You can revoke consent or delete this
            profile at any time.
          </p>
          {profileQuery.data && (
            <p className="text-sm text-ink-700">Current: {JSON.stringify(profileQuery.data.derived_attributes)}</p>
          )}
          <label className="block text-sm text-ink-700">
            Age range
            <Input value={ageRange} onChange={(e) => setAgeRange(e.target.value)} placeholder="e.g. 60_plus" className="mt-1" />
          </label>
          <label className="block text-sm text-ink-700">
            State
            <Input value={state} onChange={(e) => setState(e.target.value)} className="mt-1" />
          </label>
          <div className="flex gap-2">
            <Button onClick={() => saveMutation.mutate()} disabled={saveMutation.isPending}>Save</Button>
            <Button variant="outline" onClick={() => revokeMutation.mutate()} disabled={revokeMutation.isPending}>Revoke consent</Button>
            <Button variant="outline" onClick={() => deleteMutation.mutate()} disabled={deleteMutation.isPending}>Delete profile</Button>
          </div>
        </CardBody>
      </Card>
    </div>
  )
}
