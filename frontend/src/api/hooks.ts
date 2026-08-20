import { useQuery } from '@tanstack/react-query';
import { archivesApi, dashboardApi, insightsApi, referenceApi, researchApi, type ArchivesParams, type SearchParams } from './endpoints';

export function useDepartments() {
  return useQuery({ queryKey: ['reference', 'departments'], queryFn: referenceApi.departments });
}

export function useDocumentTypes() {
  return useQuery({ queryKey: ['reference', 'documentTypes'], queryFn: referenceApi.documentTypes });
}

export function useJurisdictions() {
  return useQuery({ queryKey: ['reference', 'jurisdictions'], queryFn: referenceApi.jurisdictions });
}

export function useLanguages() {
  return useQuery({ queryKey: ['reference', 'languages'], queryFn: referenceApi.languages });
}

export function useDashboardSummary(departmentId?: string) {
  return useQuery({
    queryKey: ['dashboard', 'summary', departmentId ?? 'all'],
    queryFn: () => dashboardApi.summary(departmentId),
  });
}

export function useUserActivity(limit = 20) {
  return useQuery({ queryKey: ['dashboard', 'activity', limit], queryFn: () => dashboardApi.activity(limit) });
}

export function useUserAlerts() {
  return useQuery({ queryKey: ['dashboard', 'alerts'], queryFn: dashboardApi.alerts });
}

export function useSearch(params: SearchParams) {
  return useQuery({
    queryKey: ['search', params],
    queryFn: () => researchApi.search(params),
    enabled: params.q.trim().length > 0,
  });
}

export function useAutocomplete(q: string) {
  return useQuery({
    queryKey: ['search', 'autocomplete', q],
    queryFn: () => researchApi.autocomplete(q),
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

export function useDocumentCrossLinks(id: string | undefined) {
  return useQuery({
    queryKey: ['archives', 'document', id, 'cross-links'],
    queryFn: () => archivesApi.crossLinks(id as string),
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

export function useChangeRadar(params: { department?: string; severity?: string; page?: number; pageSize?: number }) {
  return useQuery({ queryKey: ['insights', 'change-radar', params], queryFn: () => insightsApi.changeRadar(params) });
}
