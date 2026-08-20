import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { fetchEntityGraph } from '@/api/documents'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { Card, CardBody, CardHeader } from '@/components/ui/Card'

export function GraphPage() {
  const [entityId, setEntityId] = useState('')
  const [activeId, setActiveId] = useState('')

  const { data, isFetching, isError } = useQuery({
    queryKey: ['graph', activeId],
    queryFn: () => fetchEntityGraph(activeId),
    enabled: !!activeId,
  })

  return (
    <div className="space-y-4">
      <div>
        <h1 className="font-serif-display text-2xl font-semibold text-ink-950">Legal Relationship Graph</h1>
        <p className="text-sm text-ink-700">
          Enter a legal entity ID (found on a document&apos;s detail page once linked) to view its amendments,
          repeals, citations, and related departments.
        </p>
      </div>
      <form
        className="flex gap-2"
        onSubmit={(e) => {
          e.preventDefault()
          setActiveId(entityId)
        }}
      >
        <Input value={entityId} onChange={(e) => setEntityId(e.target.value)} placeholder="Entity UUID" />
        <Button type="submit">Load graph</Button>
      </form>

      {isFetching && <p className="text-sm text-ink-500">Loading graph…</p>}
      {isError && <p className="text-sm text-red-700">Could not load graph for this entity.</p>}

      {data && (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <Card>
            <CardHeader className="text-sm font-semibold text-ink-500">Nodes ({data.nodes.length})</CardHeader>
            <CardBody className="space-y-1 text-sm">
              {data.nodes.map((n) => (
                <div key={n.id} className="flex justify-between border-b border-ink-100 py-1">
                  <span>{n.name}</span>
                  <span className="text-ink-500">{n.type}</span>
                </div>
              ))}
            </CardBody>
          </Card>
          <Card>
            <CardHeader className="text-sm font-semibold text-ink-500">Relationships ({data.edges.length})</CardHeader>
            <CardBody className="space-y-2 text-sm">
              {data.edges.map((e, i) => (
                <div key={i} className="border-b border-ink-100 pb-2">
                  <span className="font-medium text-ink-900">{e.type}</span>
                  {e.confidence != null && <span className="ml-2 text-xs text-ink-500">confidence {Math.round(e.confidence * 100)}%</span>}
                  {e.evidence_text && <p className="mt-0.5 text-xs text-ink-500">{e.evidence_text}</p>}
                </div>
              ))}
            </CardBody>
          </Card>
        </div>
      )}
    </div>
  )
}
