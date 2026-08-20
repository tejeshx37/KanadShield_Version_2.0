import { apiClient } from './client'
import type { DocumentDetail, DocumentSummaryAI } from './types'

export interface OfflineBundle {
  generated_at: string
  items: { document: DocumentDetail & { extracted_text: string | null }; summary: DocumentSummaryAI | null }[]
}

export async function requestOfflineBundle(documentIds: string[]): Promise<OfflineBundle> {
  const { data } = await apiClient.post<OfflineBundle>('/offline/bundle', { document_ids: documentIds })
  return data
}

export async function fetchTranslation(documentId: string, language: string) {
  const { data } = await apiClient.get(`/documents/${documentId}/translations/${language}`)
  return data as { language: string; translated_text: string; generated_by: string; generated_at: string | null }
}
