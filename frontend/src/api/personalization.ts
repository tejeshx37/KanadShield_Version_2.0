import { apiClient } from './client'
import type { SchemeMatchResult } from './types'

export async function matchSchemes(profile: Record<string, unknown>): Promise<{ results: SchemeMatchResult[] }> {
  const { data } = await apiClient.post('/schemes/match', { profile })
  return data
}

export async function listBookmarks() {
  const { data } = await apiClient.get('/bookmarks')
  return data as { items: { id: string; document_id: string; note: string | null; created_at: string }[] }
}

export async function createBookmark(documentId: string, note?: string) {
  const { data } = await apiClient.post('/bookmarks', { document_id: documentId, note })
  return data
}

export async function deleteBookmark(id: string) {
  await apiClient.delete(`/bookmarks/${id}`)
}

export async function listAlerts() {
  const { data } = await apiClient.get('/alerts')
  return data as {
    items: { id: string; alert_type: string; target: Record<string, unknown>; frequency: string; is_active: boolean; last_checked_at: string | null }[]
  }
}

export async function createAlert(alertType: string, target: Record<string, unknown>, frequency = 'DAILY') {
  const { data } = await apiClient.post('/alerts', { alert_type: alertType, target, frequency })
  return data
}

export async function deleteAlert(id: string) {
  await apiClient.delete(`/alerts/${id}`)
}

export async function fetchDashboard() {
  const [trending, frequent, departments, corpus] = await Promise.all([
    apiClient.get('/dashboard/trending-searches'),
    apiClient.get('/dashboard/frequently-accessed-documents'),
    apiClient.get('/dashboard/department-insights'),
    apiClient.get('/dashboard/corpus-health'),
  ])
  return {
    trending: trending.data.items as { query: string; count: number }[],
    frequent: frequent.data.items as { document_id: string; title: string; views: number }[],
    departments: departments.data.items as { department_id: string; name: string; document_count: number; last_activity: string | null }[],
    corpus: corpus.data as {
      total_documents: number
      ingestion_volume_by_month: { month: string; count: number }[]
      classification_confidence_distribution: Record<string, number>
      date_extraction_confidence_distribution: Record<string, number>
    },
  }
}

export async function fetchChangeRadar(impactLevel?: string) {
  const { data } = await apiClient.get('/change-radar', { params: impactLevel ? { impact_level: impactLevel } : {} })
  return data as {
    items: {
      id: string
      document_id: string
      change_type: string
      impact_level: string
      affected_entities: Record<string, string[]>
      related_judgments: { judgments: string[] }
      evidence: Record<string, unknown>
      created_at: string
    }[]
  }
}

export async function fetchCitizenProfile() {
  const { data } = await apiClient.get('/citizens/profile')
  return data
}

export async function upsertCitizenProfile(derivedAttributes: Record<string, unknown>) {
  const { data } = await apiClient.put('/citizens/profile', { derived_attributes: derivedAttributes })
  return data
}

export async function deleteCitizenProfile() {
  await apiClient.delete('/citizens/profile')
}

export async function revokeCitizenConsent() {
  await apiClient.post('/citizens/profile/revoke-consent')
}
