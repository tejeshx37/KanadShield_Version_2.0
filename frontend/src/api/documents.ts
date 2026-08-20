import { apiClient } from './client'
import type { AskAnswer, DocumentDetail, DocumentSummaryAI } from './types'

export async function fetchDocument(id: string): Promise<DocumentDetail> {
  const { data } = await apiClient.get<DocumentDetail>(`/documents/${id}`)
  return data
}

export async function fetchAct(id: string) {
  const { data } = await apiClient.get(`/acts/${id}`)
  return data
}

export async function fetchJudgment(id: string) {
  const { data } = await apiClient.get(`/judgments/${id}`)
  return data
}

export async function summarizeDocument(id: string): Promise<DocumentSummaryAI> {
  const { data } = await apiClient.post<DocumentSummaryAI>(`/ai/summarize/${id}`)
  return data
}

export async function askQuestion(question: string, documentId?: string): Promise<AskAnswer> {
  const { data } = await apiClient.post<AskAnswer>('/ai/ask', { question, document_id: documentId })
  return data
}

export async function fetchTimeline(documentId: string) {
  const { data } = await apiClient.get(`/documents/${documentId}/timeline`)
  return data as { events: { event_type: string; date: string | null; title: string; document_id: string | null; detail: string | null }[] }
}

export async function compareDocuments(documentIdA: string, documentIdB: string, explain = false) {
  const { data } = await apiClient.post('/documents/compare', {
    document_id_a: documentIdA,
    document_id_b: documentIdB,
    explain,
  })
  return data
}

export async function fetchEntityGraph(entityId: string) {
  const { data } = await apiClient.get(`/graph/entities/${entityId}`)
  return data as { nodes: { id: string; type: string; name: string }[]; edges: { source: string; target: string; type: string; confidence: number | null; evidence_text: string | null }[] }
}
