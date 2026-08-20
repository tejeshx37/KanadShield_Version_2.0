import { useEffect, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { fetchDocument, summarizeDocument } from '@/api/documents'
import { createBookmark } from '@/api/personalization'
import { Card, CardBody, CardHeader } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { useOnlineStatus } from '@/lib/useOnlineStatus'
import { cacheDocument, cacheSummary, getCachedDocument, getCachedSummary, queueOfflineAction } from '@/lib/offlineCache'
import { extractErrorMessage } from '@/api/client'

export function DocumentDetailPage() {
  const { id } = useParams<{ id: string }>()
  const isOnline = useOnlineStatus()
  const [offlineDoc, setOfflineDoc] = useState<Awaited<ReturnType<typeof getCachedDocument>>>()

  const documentQuery = useQuery({
    queryKey: ['document', id],
    queryFn: () => fetchDocument(id!),
    enabled: isOnline && !!id,
  })

  useEffect(() => {
    if (documentQuery.data) void cacheDocument(documentQuery.data)
  }, [documentQuery.data])

  useEffect(() => {
    if (!isOnline && id) void getCachedDocument(id).then(setOfflineDoc)
  }, [isOnline, id])

  const doc = documentQuery.data ?? offlineDoc

  const summaryMutation = useMutation({
    mutationFn: () => summarizeDocument(id!),
    onSuccess: (data) => {
      if (id) void cacheSummary(id, data)
    },
  })

  const bookmarkMutation = useMutation({
    mutationFn: async () => {
      if (!id) return
      if (isOnline) {
        await createBookmark(id)
      } else {
        await queueOfflineAction('bookmark', { document_id: id })
      }
    },
  })

  if (!doc) {
    return <p className="text-sm text-ink-500">{isOnline ? 'Loading…' : 'Not available offline — connect to view this document.'}</p>
  }

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
      <div className="space-y-4 lg:col-span-2">
        <Card>
          <CardHeader className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Badge tone={doc.jurisdiction}>{doc.jurisdiction}</Badge>
              <Badge>{doc.document_type}</Badge>
            </div>
            <div className="flex gap-2">
              <Link to={`/documents/${id}/timeline`}>
                <Button variant="outline" size="sm">Timeline</Button>
              </Link>
              <Button variant="outline" size="sm" onClick={() => bookmarkMutation.mutate()} disabled={bookmarkMutation.isPending}>
                {bookmarkMutation.isSuccess ? 'Bookmarked' : 'Bookmark'}
              </Button>
            </div>
          </CardHeader>
          <CardBody>
            <h1 className="font-serif-display text-2xl font-semibold text-ink-950">{doc.title}</h1>
            <dl className="mt-3 grid grid-cols-2 gap-2 text-sm text-ink-700 sm:grid-cols-4">
              <div><dt className="text-ink-500">Date</dt><dd>{doc.date ?? 'Unknown'}</dd></div>
              <div><dt className="text-ink-500">Source</dt><dd>{doc.source}</dd></div>
              <div><dt className="text-ink-500">Language</dt><dd>{doc.source_language}</dd></div>
              <div><dt className="text-ink-500">Classification confidence</dt><dd>{doc.classification_confidence != null ? `${Math.round(doc.classification_confidence * 100)}%` : 'N/A'}</dd></div>
            </dl>
            {doc.source_url && (
              <a href={doc.source_url} target="_blank" rel="noreferrer" className="mt-3 inline-block text-sm font-medium text-brand-700 hover:underline">
                View original source document ↗
              </a>
            )}
          </CardBody>
        </Card>

        <Card>
          <CardHeader className="flex items-center justify-between">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-ink-500">AI Summary</h2>
            {isOnline && (
              <Button size="sm" onClick={() => summaryMutation.mutate()} disabled={summaryMutation.isPending}>
                {summaryMutation.isPending ? 'Summarizing…' : 'Generate summary'}
              </Button>
            )}
          </CardHeader>
          <CardBody>
            <SummaryBody
              isOnline={isOnline}
              documentId={id!}
              result={summaryMutation.data}
              error={summaryMutation.error}
              isPending={summaryMutation.isPending}
            />
          </CardBody>
        </Card>
      </div>

      <div className="space-y-4">
        <Card>
          <CardHeader><h2 className="text-sm font-semibold uppercase tracking-wide text-ink-500">Explore</h2></CardHeader>
          <CardBody className="space-y-2 text-sm">
            <Link className="block text-brand-700 hover:underline" to={`/graph`}>View legal relationship graph</Link>
            <Link className="block text-brand-700 hover:underline" to={`/documents/${id}/timeline`}>View timeline</Link>
            <Link className="block text-brand-700 hover:underline" to={`/schemes/match`}>Check matched schemes</Link>
          </CardBody>
        </Card>
      </div>
    </div>
  )
}

function SummaryBody({
  isOnline,
  documentId,
  result,
  error,
  isPending,
}: {
  isOnline: boolean
  documentId: string
  result?: Awaited<ReturnType<typeof summarizeDocument>>
  error: unknown
  isPending: boolean
}) {
  const [cached, setCached] = useState<Awaited<ReturnType<typeof getCachedSummary>>>()

  useEffect(() => {
    void getCachedSummary(documentId).then(setCached)
  }, [documentId])

  if (!isOnline) {
    if (cached) return <SummaryView summary={cached} />
    return <p className="text-sm text-ink-500">AI summarization is disabled offline. Connect to generate a summary.</p>
  }

  if (isPending) return <p className="text-sm text-ink-500">Retrieving evidence and generating a grounded summary…</p>
  if (error) return <p className="text-sm text-red-700">{extractErrorMessage(error)}</p>
  if (result) return <SummaryView summary={result} />
  if (cached) return <SummaryView summary={cached} />
  return <p className="text-sm text-ink-500">No summary generated yet.</p>
}

function SummaryView({ summary }: { summary: Awaited<ReturnType<typeof summarizeDocument>> }) {
  return (
    <div className="space-y-3 text-sm">
      <p className="text-ink-800">{summary.summary}</p>
      <SummarySection title="Key provisions" items={summary.key_provisions} />
      <SummarySection title="Eligibility" items={summary.eligibility} />
      <SummarySection title="Conditions" items={summary.conditions} />
      <SummarySection title="Dates" items={summary.dates} />
      <SummarySection title="Limitations" items={summary.limitations} />
      {summary.source_references.length > 0 && (
        <p className="text-xs text-ink-500">Grounded in {summary.source_references.length} retrieved excerpt(s) from this document.</p>
      )}
    </div>
  )
}

function SummarySection({ title, items }: { title: string; items: string[] }) {
  if (items.length === 0) return null
  return (
    <div>
      <h3 className="text-xs font-semibold uppercase tracking-wide text-ink-500">{title}</h3>
      <ul className="mt-1 list-inside list-disc space-y-0.5 text-ink-800">
        {items.map((item, i) => <li key={i}>{item}</li>)}
      </ul>
    </div>
  )
}
