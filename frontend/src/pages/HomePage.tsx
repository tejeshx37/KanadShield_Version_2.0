import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'

export function HomePage() {
  const [query, setQuery] = useState('')
  const navigate = useNavigate()

  function submit(e: React.FormEvent) {
    e.preventDefault()
    navigate(`/search?q=${encodeURIComponent(query)}`)
  }

  return (
    <div className="mx-auto max-w-2xl py-16 text-center">
      <h1 className="font-serif-display text-4xl font-semibold text-ink-950">KanadShield</h1>
      <p className="mt-3 text-ink-700">
        Unified legal &amp; government intelligence — Acts, Gazettes, Government Resolutions, and judgments,
        cross-referenced and grounded in the original source.
      </p>
      <form onSubmit={submit} className="mt-8 flex gap-2">
        <Input
          autoFocus
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Try 'pension' or 'Gujarat Panchayats Act'"
        />
        <Button type="submit">Search</Button>
      </form>
    </div>
  )
}
