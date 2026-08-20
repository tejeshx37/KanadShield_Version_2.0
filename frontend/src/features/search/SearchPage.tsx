import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link, useSearchParams } from 'react-router-dom'
import { searchDocuments } from '@/api/search'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { Card, CardBody } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { useOnlineStatus } from '@/lib/useOnlineStatus'
import { searchOfflineCache } from '@/lib/offlineCache'

const DOCUMENT_TYPES = [
  'ACT', 'RULE', 'REGULATION', 'GR', 'NOTIFICATION', 'CIRCULAR', 'ORDER', 'GAZETTE',
  'JUDGMENT', 'SCHEME', 'ORDINANCE', 'STATUTE', 'GUIDELINE', 'OTHER',
]

export function SearchPage() {
  const [params, setParams] = useSearchParams()
  const [query, setQuery] = useState(params.get('q') ?? '')
  const documentType = params.get('document_type') ?? ''
  const jurisdiction = params.get('jurisdiction') ?? ''
  const isOnline = useOnlineStatus()

  const activeQuery = params.get('q') ?? ''

  const onlineResults = useQuery({
    queryKey: ['search', activeQuery, documentType, jurisdiction],
    queryFn: () =>
      searchDocuments({
        q: activeQuery,
        document_type: documentType || undefined,
        jurisdiction: jurisdiction || undefined,
      }),
    enabled: isOnline && activeQuery.length > 0,
  })

  const offlineResults = useQuery({
    queryKey: ['offline-search', activeQuery],
    queryFn: () => searchOfflineCache(activeQuery),
    enabled: !isOnline && activeQuery.length > 0,
  })

  function submit(e: React.FormEvent) {
    e.preventDefault()
    setParams({ q: query, ...(documentType ? { document_type: documentType } : {}), ...(jurisdiction ? { jurisdiction } : {}) })
  }

  return (
    <div className="space-y-6">
      <form onSubmit={submit} className="flex gap-2">
        <Input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search Acts, GRs, judgments, gazettes..." />
        <Button type="submit">Search</Button>
      </form>

      <div className="flex flex-wrap gap-2 text-sm">
        <select
          className="rounded-md border border-ink-300 px-2 py-1"
          value={documentType}
          onChange={(e) => setParams({ q: activeQuery, document_type: e.target.value })}
        >
          <option value="">All document types</option>
          {DOCUMENT_TYPES.map((t) => (
            <option key={t} value={t}>{t}</option>
          ))}
        </select>
        <select
          className="rounded-md border border-ink-300 px-2 py-1"
          value={jurisdiction}
          onChange={(e) => setParams({ q: activeQuery, jurisdiction: e.target.value })}
        >
          <option value="">All jurisdictions</option>
          <option value="CENTRAL">Central</option>
          <option value="STATE">State</option>
        </select>
      </div>

      {!isOnline && (
        <p className="text-sm text-amber-700">
          Offline — showing results from your downloaded documents only. Connect to search the full database.
        </p>
      )}

      {isOnline && onlineResults.data && (
        <p className="text-sm text-ink-500">
          {onlineResults.data.total} results in {onlineResults.data.search_time_ms}ms
        </p>
      )}

      <div className="space-y-3">
        {isOnline &&
          onlineResults.data?.items.map((item) => (
            <Card key={item.document_id}>
              <CardBody>
                <div className="mb-1 flex items-center gap-2">
                  <Badge tone={item.jurisdiction}>{item.jurisdiction}</Badge>
                  <Badge>{item.document_type}</Badge>
                  {item.date && <span className="text-xs text-ink-500">{item.date}</span>}
                </div>
                <Link to={`/documents/${item.document_id}`} className="text-base font-semibold text-brand-700 hover:underline">
                  {item.title}
                </Link>
                <p className="mt-1 line-clamp-2 text-sm text-ink-700">{item.snippet}</p>
              </CardBody>
            </Card>
          ))}

        {!isOnline &&
          offlineResults.data?.map((item) => (
            <Card key={item.id}>
              <CardBody>
                <Link to={`/documents/${item.id}`} className="text-base font-semibold text-brand-700 hover:underline">
                  {item.title}
                </Link>
                <p className="mt-1 text-xs text-ink-500">Available offline</p>
              </CardBody>
            </Card>
          ))}

        {isOnline && activeQuery && onlineResults.data?.items.length === 0 && (
          <p className="text-sm text-ink-500">No results found.</p>
        )}
      </div>
    </div>
  )
}
