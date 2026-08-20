import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/api/client'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { Card, CardBody } from '@/components/ui/Card'

interface Collection {
  id: string
  name: string
  description: string | null
}

export function ResearchPage() {
  const [name, setName] = useState('')
  const queryClient = useQueryClient()

  const { data } = useQuery<{ items: Collection[] }>({
    queryKey: ['collections'],
    queryFn: async () => (await apiClient.get('/research/collections')).data,
  })

  const createMutation = useMutation({
    mutationFn: () => apiClient.post('/research/collections', { name }),
    onSuccess: () => {
      setName('')
      void queryClient.invalidateQueries({ queryKey: ['collections'] })
    },
  })

  async function exportCollection(id: string, collectionName: string) {
    const resp = await apiClient.get(`/research/collections/${id}/export`, { responseType: 'blob' })
    const url = URL.createObjectURL(resp.data as Blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${collectionName}.md`
    link.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="mx-auto max-w-xl space-y-6">
      <h1 className="font-serif-display text-2xl font-semibold text-ink-950">Research Workspace</h1>
      <form
        className="flex gap-2"
        onSubmit={(e) => {
          e.preventDefault()
          if (name.trim()) createMutation.mutate()
        }}
      >
        <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="New collection name" />
        <Button type="submit" disabled={createMutation.isPending}>Create</Button>
      </form>
      <div className="space-y-2">
        {data?.items.map((c) => (
          <Card key={c.id}>
            <CardBody className="flex items-center justify-between">
              <div>
                <p className="font-medium text-ink-900">{c.name}</p>
                {c.description && <p className="text-sm text-ink-600">{c.description}</p>}
              </div>
              <button className="text-sm text-brand-700 hover:underline" onClick={() => void exportCollection(c.id, c.name)}>
                Export
              </button>
            </CardBody>
          </Card>
        ))}
        {data?.items.length === 0 && <p className="text-sm text-ink-500">No collections yet. Add documents from their detail page.</p>}
      </div>
    </div>
  )
}
