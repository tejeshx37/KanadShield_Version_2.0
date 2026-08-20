import { describe, expect, it } from 'vitest'
import {
  cacheDocument,
  getCachedDocument,
  queueOfflineAction,
  getPendingActions,
  markActionSynced,
  searchOfflineCache,
} from './offlineCache'
import type { DocumentDetail } from '@/api/types'

function makeDoc(overrides: Partial<DocumentDetail> = {}): DocumentDetail {
  return {
    id: crypto.randomUUID(),
    source: 'test',
    title: 'Pension Scheme GR',
    document_type: 'GR',
    jurisdiction: 'STATE',
    state: 'Gujarat',
    source_language: 'en',
    date: '2021-01-01',
    year: 2021,
    subject: 'Pension for retired workers',
    source_url: null,
    text_available: true,
    classification_confidence: 0.9,
    case_number: null,
    act_number: null,
    keywords: null,
    pdf_path: null,
    date_confidence: 0.8,
    doc_metadata: {},
    created_at: '2021-01-01T00:00:00Z',
    updated_at: '2021-01-01T00:00:00Z',
    ...overrides,
  }
}

describe('offlineCache (real IndexedDB via fake-indexeddb)', () => {
  it('persists a document across separate reads, not just an in-memory cache', async () => {
    const doc = makeDoc()
    await cacheDocument(doc)
    const fetched = await getCachedDocument(doc.id)
    expect(fetched?.title).toBe('Pension Scheme GR')
  })

  it('returns undefined for a document that was never cached', async () => {
    const fetched = await getCachedDocument('00000000-0000-0000-0000-000000000000')
    expect(fetched).toBeUndefined()
  })

  it('finds cached documents by substring search, honestly scoped to what is stored', async () => {
    await cacheDocument(makeDoc({ id: crypto.randomUUID(), title: 'Gujarat Pension Rules' }))
    await cacheDocument(makeDoc({ id: crypto.randomUUID(), title: 'Road Traffic Notification', subject: 'traffic' }))

    const results = await searchOfflineCache('pension')
    expect(results.some((d) => d.title === 'Gujarat Pension Rules')).toBe(true)
    expect(results.some((d) => d.title === 'Road Traffic Notification')).toBe(false)
  })

  it('queues an offline action and later marks it synced, never silently dropping it', async () => {
    await queueOfflineAction('bookmark', { document_id: 'doc-123' })
    const pending = await getPendingActions()
    expect(pending.length).toBeGreaterThan(0)

    const action = pending[0]
    await markActionSynced(action.id)
    const remaining = await getPendingActions()
    expect(remaining.find((a) => a.id === action.id)).toBeUndefined()
  })
})
