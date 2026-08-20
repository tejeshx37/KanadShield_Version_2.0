import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { fetchChangeRadar } from '@/api/personalization'
import { Card, CardBody } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'

const IMPACT_TONE: Record<string, string> = {
  CRITICAL: 'bg-red-100 text-red-800',
  HIGH: 'bg-orange-100 text-orange-800',
  MEDIUM: 'bg-amber-100 text-amber-800',
  LOW: 'bg-ink-100 text-ink-700',
}

export function ChangeRadarPage() {
  const [impactFilter, setImpactFilter] = useState('')
  const { data, isLoading } = useQuery({ queryKey: ['change-radar', impactFilter], queryFn: () => fetchChangeRadar(impactFilter || undefined) })

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="font-serif-display text-2xl font-semibold text-ink-950">Legal Change &amp; Impact Radar</h1>
        <select className="rounded-md border border-ink-300 px-2 py-1 text-sm" value={impactFilter} onChange={(e) => setImpactFilter(e.target.value)}>
          <option value="">All impact levels</option>
          <option value="CRITICAL">Critical</option>
          <option value="HIGH">High</option>
          <option value="MEDIUM">Medium</option>
          <option value="LOW">Low</option>
        </select>
      </div>

      {isLoading && <p className="text-sm text-ink-500">Loading…</p>}

      <div className="space-y-3">
        {data?.items.map((report) => (
          <Card key={report.id}>
            <CardBody>
              <div className="flex items-center gap-2">
                <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${IMPACT_TONE[report.impact_level]}`}>
                  {report.impact_level} — potential impact
                </span>
                <Badge>{report.change_type}</Badge>
              </div>
              <Link to={`/documents/${report.document_id}`} className="mt-2 block text-sm font-medium text-brand-700 hover:underline">
                View changed document
              </Link>
              {Object.entries(report.affected_entities).length > 0 && (
                <p className="mt-1 text-xs text-ink-500">
                  Affects: {Object.entries(report.affected_entities).map(([type, names]) => `${type} (${names.length})`).join(', ')}
                </p>
              )}
            </CardBody>
          </Card>
        ))}
        {data?.items.length === 0 && <p className="text-sm text-ink-500">No changes detected yet.</p>}
      </div>
    </div>
  )
}
