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

interface JobResult<T> {
  status: 'pending' | 'started' | 'retry' | 'success' | 'insufficient_evidence' | 'failed'
  result?: T
  error?: string
}

async function pollJob<T>(jobId: string, { intervalMs = 800, timeoutMs = 30_000 } = {}): Promise<JobResult<T>> {
  const deadline = Date.now() + timeoutMs
  while (Date.now() < deadline) {
    const { data } = await apiClient.get<JobResult<T>>(`/ai/jobs/${jobId}`)
    if (data.status !== 'pending' && data.status !== 'started' && data.status !== 'retry') return data
    await new Promise((resolve) => setTimeout(resolve, intervalMs))
  }
  return { status: 'failed', error: 'Timed out waiting for the AI job to complete.' }
}

/** Expensive AI processing runs in a Celery worker, never inline in the
 * request — this enqueues the job and polls for the result. */
export async function summarizeDocument(id: string): Promise<DocumentSummaryAI> {
  const { data } = await apiClient.post<{ job_id: string }>(`/ai/summarize/${id}`)
  const job = await pollJob<DocumentSummaryAI>(data.job_id)
  if (job.status === 'success' && job.result) return job.result
  throw new Error(job.error ?? 'Insufficient evidence to summarize this document.')
}

export async function askQuestion(question: string, documentId?: string): Promise<AskAnswer> {
  const { data } = await apiClient.post<{ job_id: string }>('/ai/ask', { question, document_id: documentId })
  const job = await pollJob<AskAnswer>(data.job_id)
  if (job.result) return job.result
  throw new Error(job.error ?? 'The AI job did not return a result.')
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
