import { apiClient } from './client'
import type { SearchResponse } from './types'

export interface SearchParams {
  q: string
  source?: string
  document_type?: string
  jurisdiction?: string
  year_from?: number
  year_to?: number
  language?: string
  page?: number
  page_size?: number
}

export async function searchDocuments(params: SearchParams): Promise<SearchResponse> {
  const { data } = await apiClient.get<SearchResponse>('/search', { params })
  return data
}

export async function fetchSuggestions(q: string): Promise<string[]> {
  if (!q.trim()) return []
  const { data } = await apiClient.get<{ suggestions: string[] }>('/search/suggestions', { params: { q } })
  return data.suggestions
}
