import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { createAlert, deleteAlert, listAlerts } from '@/api/personalization'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { Card, CardBody } from '@/components/ui/Card'

export function AlertsPage() {
  const [topic, setTopic] = useState('')
  const queryClient = useQueryClient()
  const { data } = useQuery({ queryKey: ['alerts'], queryFn: listAlerts })

  const createMutation = useMutation({
    mutationFn: () => createAlert('topic', { topic }),
    onSuccess: () => {
      setTopic('')
      void queryClient.invalidateQueries({ queryKey: ['alerts'] })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteAlert(id),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ['alerts'] }),
  })

  return (
    <div className="mx-auto max-w-xl space-y-6">
      <h1 className="font-serif-display text-2xl font-semibold text-ink-950">Alerts</h1>
      <form
        className="flex gap-2"
        onSubmit={(e) => {
          e.preventDefault()
          if (topic.trim()) createMutation.mutate()
        }}
      >
        <Input value={topic} onChange={(e) => setTopic(e.target.value)} placeholder="Topic to watch, e.g. 'pension'" />
        <Button type="submit" disabled={createMutation.isPending}>Add alert</Button>
      </form>
      <div className="space-y-2">
        {data?.items.map((alert) => (
          <Card key={alert.id}>
            <CardBody className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-ink-900">{alert.alert_type}: {JSON.stringify(alert.target)}</p>
                <p className="text-xs text-ink-500">
                  {alert.frequency} · last checked {alert.last_checked_at ?? 'never'}
                </p>
              </div>
              <Button variant="ghost" size="sm" onClick={() => deleteMutation.mutate(alert.id)}>Remove</Button>
            </CardBody>
          </Card>
        ))}
        {data?.items.length === 0 && <p className="text-sm text-ink-500">No alerts configured yet.</p>}
      </div>
    </div>
  )
}
