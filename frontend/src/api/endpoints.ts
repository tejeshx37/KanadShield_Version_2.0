import { apiFetch } from './client';
import type {
  ActivityItem,
  AlertItem,
  AutocompleteSuggestion,
  ChangeRadarItem,
  CrossLink,
  DashboardSummary,
  Department,
  DocumentDetail,
  DocumentGraph,
  DocumentType,
  Jurisdiction,
  Language,
  Paginated,
  DocumentSummary,
  SearchResponse,
} from './types';

export const referenceApi = {
  departments: () => apiFetch<Department[]>('/reference/departments'),
  documentTypes: () => apiFetch<DocumentType[]>('/reference/document-types'),
  jurisdictions: () => apiFetch<Jurisdiction[]>('/reference/jurisdictions'),
  languages: () => apiFetch<Language[]>('/reference/languages'),
};

export const dashboardApi = {
  summary: (departmentId?: string) =>
    apiFetch<DashboardSummary>('/dashboard/summary', { params: { department: departmentId } }),
  activity: (limit = 20) => apiFetch<ActivityItem[]>('/users/me/activity', { params: { limit } }),
  alerts: () => apiFetch<AlertItem[]>('/users/me/alerts', { params: { status: 'active' } }),
};

export interface SearchParams {
  q: string;
  department?: string;
  type?: string;
  jurisdiction?: string;
  dateFrom?: string;
  dateTo?: string;
  page?: number;
  pageSize?: number;
}

export const researchApi = {
  search: (params: SearchParams) => apiFetch<SearchResponse>('/search', { params: { ...params } }),
  autocomplete: (q: string) =>
    apiFetch<{ suggestions: AutocompleteSuggestion[] }>('/search/autocomplete', { params: { q } }),
};

export interface ArchivesParams {
  department?: string;
  type?: string;
  jurisdiction?: string;
  dateFrom?: string;
  dateTo?: string;
  page?: number;
  pageSize?: number;
}

export const archivesApi = {
  list: (params: ArchivesParams) =>
    apiFetch<Paginated<DocumentSummary> & { facets: SearchResponse['facets'] }>('/documents', {
      params: { ...params },
    }),
  detail: (id: string) => apiFetch<DocumentDetail>(`/documents/${id}`),
  crossLinks: (id: string) => apiFetch<CrossLink[]>(`/documents/${id}/cross-links`),
  graph: (id: string) => apiFetch<DocumentGraph>(`/documents/${id}/graph`),
};

export const insightsApi = {
  changeRadar: (params: { department?: string; severity?: string; page?: number; pageSize?: number }) =>
    apiFetch<Paginated<ChangeRadarItem>>('/insights/change-radar', { params }),
};
