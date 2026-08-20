import { useQuery } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'
import { fetchAct } from '@/api/documents'
import { Card, CardBody, CardHeader } from '@/components/ui/Card'

export function ActDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { data, isLoading } = useQuery({ queryKey: ['act', id], queryFn: () => fetchAct(id!), enabled: !!id })

  if (isLoading) return <p className="text-sm text-ink-500">Loading…</p>
  if (!data) return <p className="text-sm text-ink-500">Act not found.</p>

  return (
    <div className="space-y-4">
      <div>
        <h1 className="font-serif-display text-2xl font-semibold text-ink-950">{data.short_title || data.document?.title}</h1>
        {data.long_title && <p className="text-sm text-ink-700">{data.long_title}</p>}
        {data.document?.source_url && (
          <a href={data.document.source_url} target="_blank" rel="noreferrer" className="text-sm text-brand-700 hover:underline">
            View original source ↗
          </a>
        )}
      </div>
      <div className="space-y-2">
        {data.sections?.map((section: { id: string; section_number: string; heading: string | null; text: string }) => (
          <Card key={section.id}>
            <CardHeader className="text-sm font-semibold text-ink-900">
              Section {section.section_number}{section.heading ? ` — ${section.heading}` : ''}
            </CardHeader>
            <CardBody className="text-sm text-ink-800">{section.text}</CardBody>
          </Card>
        ))}
        {(!data.sections || data.sections.length === 0) && <p className="text-sm text-ink-500">No sections indexed yet.</p>}
      </div>
    </div>
  )
}
