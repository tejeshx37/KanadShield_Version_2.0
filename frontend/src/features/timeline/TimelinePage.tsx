import { useQuery } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'
import { fetchTimeline } from '@/api/documents'
import { Card, CardBody } from '@/components/ui/Card'

export function TimelinePage() {
  const { id } = useParams<{ id: string }>()
  const { data, isLoading } = useQuery({ queryKey: ['timeline', id], queryFn: () => fetchTimeline(id!), enabled: !!id })

  if (isLoading) return <p className="text-sm text-ink-500">Loading…</p>

  return (
    <div className="space-y-4">
      <h1 className="font-serif-display text-2xl font-semibold text-ink-950">Timeline</h1>
      <ol className="space-y-3 border-l-2 border-ink-300 pl-4">
        {data?.events.map((event, i) => (
          <li key={i} className="relative">
            <span className="absolute -left-[21px] top-1 h-2.5 w-2.5 rounded-full bg-brand-600" />
            <Card>
              <CardBody>
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase tracking-wide text-brand-700">{event.event_type}</span>
                  <span className="text-xs text-ink-500">{event.date ?? 'Date unknown'}</span>
                </div>
                <p className="mt-1 text-sm font-medium text-ink-900">{event.title}</p>
                {event.detail && <p className="mt-1 text-sm text-ink-700">{event.detail}</p>}
              </CardBody>
            </Card>
          </li>
        ))}
        {data?.events.length === 0 && <p className="text-sm text-ink-500">No timeline events recorded yet.</p>}
      </ol>
    </div>
  )
}
