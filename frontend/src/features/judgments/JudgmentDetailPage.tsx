import { useQuery } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'
import { fetchJudgment } from '@/api/documents'
import { Card, CardBody } from '@/components/ui/Card'

export function JudgmentDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { data, isLoading } = useQuery({ queryKey: ['judgment', id], queryFn: () => fetchJudgment(id!), enabled: !!id })

  if (isLoading) return <p className="text-sm text-ink-500">Loading…</p>
  if (!data) return <p className="text-sm text-ink-500">Judgment not found.</p>

  return (
    <Card>
      <CardBody className="space-y-2">
        <h1 className="font-serif-display text-2xl font-semibold text-ink-950">{data.document?.title}</h1>
        <dl className="grid grid-cols-2 gap-2 text-sm text-ink-700 sm:grid-cols-3">
          <div><dt className="text-ink-500">Case number</dt><dd>{data.case_number ?? 'Unknown'}</dd></div>
          <div><dt className="text-ink-500">Decision date</dt><dd>{data.decision_date ?? 'Unknown'}</dd></div>
          <div><dt className="text-ink-500">Citation</dt><dd>{data.citation ?? 'Unknown'}</dd></div>
        </dl>
        {data.headnote && <p className="text-sm text-ink-800">{data.headnote}</p>}
        {data.document?.source_url && (
          <a href={data.document.source_url} target="_blank" rel="noreferrer" className="inline-block text-sm text-brand-700 hover:underline">
            View original source ↗
          </a>
        )}
      </CardBody>
    </Card>
  )
}
