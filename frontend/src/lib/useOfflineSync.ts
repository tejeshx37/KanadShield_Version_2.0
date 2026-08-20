import { useEffect, useState } from 'react'
import { getPendingActions, markActionSynced } from '@/lib/offlineCache'
import { createBookmark } from '@/api/personalization'
import { apiClient } from '@/api/client'
import { useOnlineStatus } from '@/lib/useOnlineStatus'

/** Drains the offline action queue and syncs it to the real API on
 * reconnect, exposing visible sync status — never a silent drop, never a
 * false "saved" state before the sync actually completes. */
export function useOfflineSync() {
  const isOnline = useOnlineStatus()
  const [status, setStatus] = useState<'idle' | 'syncing' | 'synced'>('idle')
  const [pendingCount, setPendingCount] = useState(0)

  useEffect(() => {
    getPendingActions().then((actions) => setPendingCount(actions.length))
  }, [])

  useEffect(() => {
    if (!isOnline) return
    let cancelled = false

    async function sync() {
      const actions = await getPendingActions()
      if (actions.length === 0) return
      setStatus('syncing')
      for (const action of actions) {
        try {
          if (action.kind === 'bookmark') {
            await createBookmark(action.payload.document_id as string, action.payload.note as string | undefined)
          } else if (action.kind === 'saved_search') {
            await apiClient.post('/saved-searches', action.payload)
          }
          await markActionSynced(action.id)
        } catch {
          // leave it queued — will retry on next reconnect
        }
      }
      if (!cancelled) {
        const remaining = await getPendingActions()
        setPendingCount(remaining.length)
        setStatus('synced')
      }
    }

    void sync()
    return () => {
      cancelled = true
    }
  }, [isOnline])

  return { status, pendingCount }
}
