import { apiFetch } from './client';
import type {
  AlertItem,
  Court,
  Department,
  DocumentDetail,
  DocumentGraph,
  DocumentSummary,
  FrequentDocument,
  CorpusHealth,
  DepartmentInsight,
  JobAccepted,
  JobStatus,
  Ministry,
  Paginated,
  SearchHistoryItem,
  SearchResponse,
  TrendingSearch,
} from './types';

export const referenceApi = {
  departments: () => apiFetch<Department[]>('/departments'),
  ministries: () => apiFetch<Ministry[]>('/ministries'),
  courts: () => apiFetch<Court[]>('/courts'),
};

export const dashboardApi = {
  trendingSearches: () => apiFetch<{ items: TrendingSearch[] }>('/dashboard/trending-searches'),
  frequentDocuments: () => apiFetch<{ items: FrequentDocument[] }>('/dashboard/frequently-accessed-documents'),
  departmentInsights: () => apiFetch<{ items: DepartmentInsight[] }>('/dashboard/department-insights'),
  corpusHealth: () => apiFetch<CorpusHealth>('/dashboard/corpus-health'),
  searchHistory: () => apiFetch<{ items: SearchHistoryItem[] }>('/search-history'),
  alerts: () => apiFetch<{ items: AlertItem[] }>('/alerts'),
};

export interface SearchParams {
  q: string;
  document_type?: string;
  jurisdiction?: string;
  department?: string;
  ministry?: string;
  court?: string;
  year_from?: number;
  year_to?: number;
  page?: number;
  page_size?: number;
}

export const researchApi = {
  search: (params: SearchParams) => apiFetch<SearchResponse>('/search', { params: { ...params } }),
  suggestions: (q: string) => apiFetch<{ suggestions: string[] }>('/search/suggestions', { params: { q } }),
};

export interface ArchivesParams {
  document_type?: string;
  jurisdiction?: string;
  state?: string;
  year_from?: number;
  year_to?: number;
  page?: number;
  page_size?: number;
}

export const archivesApi = {
  list: (params: ArchivesParams) => apiFetch<Paginated<DocumentSummary>>('/documents', { params: { ...params } }),
  detail: (id: string) => apiFetch<DocumentDetail>(`/documents/${id}`),
  graph: (documentId: string) => apiFetch<DocumentGraph>(`/graph/documents/${documentId}`),
};

export const aiApi = {
  requestSummary: (documentId: string) =>
    apiFetch<JobAccepted>(`/ai/summarize/${documentId}`, { method: 'POST' }),
  jobStatus: (jobId: string) => apiFetch<JobStatus>(`/ai/jobs/${jobId}`),
  ask: (question: string, documentId?: string) =>
    apiFetch<JobAccepted>('/ai/ask', { method: 'POST', body: { question, document_id: documentId } }),
};
