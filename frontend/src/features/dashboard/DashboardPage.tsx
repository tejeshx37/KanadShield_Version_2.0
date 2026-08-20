import { useQuery } from '@tanstack/react-query'
import { fetchDashboard } from '@/api/personalization'
import { Card, CardBody, CardHeader } from '@/components/ui/Card'

export function DashboardPage() {
  const { data, isLoading } = useQuery({ queryKey: ['dashboard'], queryFn: fetchDashboard })

  if (isLoading || !data) return <p className="text-sm text-ink-500">Loading…</p>

  return (
    <div className="space-y-6">
      <h1 className="font-serif-display text-2xl font-semibold text-ink-950">Dashboard</h1>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <StatCard label="Total documents" value={data.corpus.total_documents} />
        <StatCard label="High-confidence classification" value={data.corpus.classification_confidence_distribution.high ?? 0} />
        <StatCard label="Low-confidence classification" value={data.corpus.classification_confidence_distribution.low ?? 0} />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader className="text-sm font-semibold text-ink-500">Trending searches (last window)</CardHeader>
          <CardBody className="space-y-1 text-sm">
            {data.trending.map((t) => (
              <div key={t.query} className="flex justify-between border-b border-ink-100 py-1">
                <span>{t.query}</span>
                <span className="text-ink-500">{t.count}</span>
              </div>
            ))}
            {data.trending.length === 0 && <p className="text-ink-500">No search activity yet.</p>}
          </CardBody>
        </Card>

        <Card>
          <CardHeader className="text-sm font-semibold text-ink-500">Frequently accessed documents</CardHeader>
          <CardBody className="space-y-1 text-sm">
            {data.frequent.map((f) => (
              <div key={f.document_id} className="flex justify-between border-b border-ink-100 py-1">
                <span className="truncate">{f.title}</span>
                <span className="text-ink-500">{f.views}</span>
              </div>
            ))}
            {data.frequent.length === 0 && <p className="text-ink-500">No view activity yet.</p>}
          </CardBody>
        </Card>

        <Card>
          <CardHeader className="text-sm font-semibold text-ink-500">Department insights</CardHeader>
          <CardBody className="space-y-1 text-sm">
            {data.departments.map((d) => (
              <div key={d.department_id} className="flex justify-between border-b border-ink-100 py-1">
                <span>{d.name}</span>
                <span className="text-ink-500">{d.document_count} docs</span>
              </div>
            ))}
            {data.departments.length === 0 && <p className="text-ink-500">No department data yet.</p>}
          </CardBody>
        </Card>

        <Card>
          <CardHeader className="text-sm font-semibold text-ink-500">Ingestion volume by month</CardHeader>
          <CardBody className="space-y-1 text-sm">
            {data.corpus.ingestion_volume_by_month.map((m) => (
              <div key={m.month} className="flex justify-between border-b border-ink-100 py-1">
                <span>{m.month}</span>
                <span className="text-ink-500">{m.count}</span>
              </div>
            ))}
            {data.corpus.ingestion_volume_by_month.length === 0 && <p className="text-ink-500">No ingestion history yet.</p>}
          </CardBody>
        </Card>
      </div>
    </div>
  )
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <Card>
      <CardBody>
        <p className="text-xs font-medium uppercase tracking-wide text-ink-500">{label}</p>
        <p className="mt-1 text-3xl font-semibold text-ink-950">{value}</p>
      </CardBody>
    </Card>
  )
}
