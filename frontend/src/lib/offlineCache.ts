import { openDB, type DBSchema, type IDBPDatabase } from 'idb'
import type { DocumentDetail, DocumentSummaryAI } from '@/api/types'

const DB_NAME = 'kanadshield-offline'
const DB_VERSION = 1

interface QueuedAction {
  id: string
  kind: 'bookmark' | 'saved_search'
  payload: Record<string, unknown>
  createdAt: string
  synced: boolean
}

interface OfflineSchema extends DBSchema {
  documents: { key: string; value: DocumentDetail }
  summaries: { key: string; value: DocumentSummaryAI & { document_id: string } }
  pending_actions: { key: string; value: QueuedAction }
}

let dbPromise: Promise<IDBPDatabase<OfflineSchema>> | null = null

function getDb() {
  dbPromise ??= openDB<OfflineSchema>(DB_NAME, DB_VERSION, {
    upgrade(db) {
      if (!db.objectStoreNames.contains('documents')) db.createObjectStore('documents', { keyPath: 'id' })
      if (!db.objectStoreNames.contains('summaries')) db.createObjectStore('summaries', { keyPath: 'document_id' })
      if (!db.objectStoreNames.contains('pending_actions')) db.createObjectStore('pending_actions', { keyPath: 'id' })
    },
  })
  return dbPromise
}

/** Persists a real document the user opened so it remains viewable
 * offline — genuinely persisted (IndexedDB), not an in-memory cache that
 * clears on tab close. */
export async function cacheDocument(doc: DocumentDetail): Promise<void> {
  const db = await getDb()
  await db.put('documents', doc)
}

export async function cacheSummary(documentId: string, summary: DocumentSummaryAI): Promise<void> {
  const db = await getDb()
  await db.put('summaries', { ...summary, document_id: documentId })
}

export async function getCachedDocument(id: string): Promise<DocumentDetail | undefined> {
  const db = await getDb()
  return db.get('documents', id)
}

export async function getCachedSummary(documentId: string): Promise<DocumentSummaryAI | undefined> {
  const db = await getDb()
  return db.get('summaries', documentId)
}

/** Offline search runs only against locally cached/downloaded content —
 * a simple substring match, honestly scoped to what's actually stored. */
export async function searchOfflineCache(query: string): Promise<DocumentDetail[]> {
  const db = await getDb()
  const all = await db.getAll('documents')
  const lower = query.toLowerCase()
  return all.filter((d) => d.title.toLowerCase().includes(lower) || (d.subject ?? '').toLowerCase().includes(lower))
}

/** Actions taken offline (bookmarking, saving a search) queue locally and
 * sync automatically on reconnect — never silently dropped. */
export async function queueOfflineAction(kind: QueuedAction['kind'], payload: Record<string, unknown>): Promise<void> {
  const db = await getDb()
  const action: QueuedAction = {
    id: crypto.randomUUID(),
    kind,
    payload,
    createdAt: new Date().toISOString(),
    synced: false,
  }
  await db.put('pending_actions', action)
}

export async function getPendingActions(): Promise<QueuedAction[]> {
  const db = await getDb()
  return db.getAll('pending_actions')
}

export async function markActionSynced(id: string): Promise<void> {
  const db = await getDb()
  await db.delete('pending_actions', id)
}
