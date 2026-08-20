import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import {
  aiApi,
  archivesApi,
  dashboardApi,
  referenceApi,
  researchApi,
  type ArchivesParams,
  type SearchParams,
} from './endpoints';
import type { JobStatus } from './types';

export function useDepartments() {
  return useQuery({ queryKey: ['reference', 'departments'], queryFn: referenceApi.departments });
}

export function useMinistries() {
  return useQuery({ queryKey: ['reference', 'ministries'], queryFn: referenceApi.ministries });
}

export function useCourts() {
  return useQuery({ queryKey: ['reference', 'courts'], queryFn: referenceApi.courts });
}

export function useTrendingSearches() {
  return useQuery({ queryKey: ['dashboard', 'trending-searches'], queryFn: dashboardApi.trendingSearches });
}

export function useFrequentDocuments() {
  return useQuery({ queryKey: ['dashboard', 'frequent-documents'], queryFn: dashboardApi.frequentDocuments });
}

export function useDepartmentInsights() {
  return useQuery({ queryKey: ['dashboard', 'department-insights'], queryFn: dashboardApi.departmentInsights });
}

export function useCorpusHealth() {
  return useQuery({ queryKey: ['dashboard', 'corpus-health'], queryFn: dashboardApi.corpusHealth });
}

// Requires auth (backend/app/api/v1/bookmarks.py, alerts.py use
// get_current_user, not optional) — there is no login flow built yet, so
// these genuinely 401 until one exists. That 401 is a real, honest error
// state, not a bug in this query.
export function useSearchHistory() {
  return useQuery({ queryKey: ['dashboard', 'search-history'], queryFn: dashboardApi.searchHistory, retry: false });
}

export function useUserAlerts() {
  return useQuery({ queryKey: ['dashboard', 'alerts'], queryFn: dashboardApi.alerts, retry: false });
}

export function useSearch(params: SearchParams) {
  return useQuery({
    queryKey: ['search', params],
    queryFn: () => researchApi.search(params),
    enabled: params.q.trim().length > 0,
  });
}

export function useSearchSuggestions(q: string) {
  return useQuery({
    queryKey: ['search', 'suggestions', q],
    queryFn: () => researchApi.suggestions(q),
    enabled: q.trim().length > 1,
  });
}

export function useArchivesList(params: ArchivesParams) {
  return useQuery({ queryKey: ['archives', 'list', params], queryFn: () => archivesApi.list(params) });
}

export function useDocumentDetail(id: string | undefined) {
  return useQuery({
    queryKey: ['archives', 'document', id],
    queryFn: () => archivesApi.detail(id as string),
    enabled: Boolean(id),
  });
}

export function useDocumentGraph(id: string | undefined) {
  return useQuery({
    queryKey: ['archives', 'document', id, 'graph'],
    queryFn: () => archivesApi.graph(id as string),
    enabled: Boolean(id),
  });
}

const SETTLED_STATUSES = new Set(['success', 'failed', 'insufficient_evidence']);

/** Submits the AI summarize job on demand, then polls until it settles. */
export function useDocumentAiSummary(documentId: string) {
  const [jobId, setJobId] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const requestMutation = useMutation({
    mutationFn: () => aiApi.requestSummary(documentId),
    onSuccess: (data) => setJobId(data.job_id),
  });

  const jobQuery = useQuery<JobStatus>({
    queryKey: ['ai', 'job', jobId],
    queryFn: () => aiApi.jobStatus(jobId as string),
    enabled: Boolean(jobId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status && SETTLED_STATUSES.has(status) ? false : 1500;
    },
  });

  function reset() {
    setJobId(null);
    queryClient.removeQueries({ queryKey: ['ai', 'job'] });
  }

  return { request: requestMutation, jobId, job: jobQuery, reset };
}
