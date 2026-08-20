export type DocumentStatus = 'active' | 'amended' | 'superseded';
export type Severity = 'critical' | 'high' | 'medium' | 'low';

export interface Paginated<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
}

export interface FacetCount {
  id: string;
  label: string;
  count: number;
}

export interface Department {
  id: string;
  name: string;
  code: string;
}

export interface DocumentType {
  id: string;
  name: string;
}

export interface Jurisdiction {
  id: string;
  name: string;
}

export interface Language {
  code: string;
  label: string;
}

export interface DocumentSummary {
  id: string;
  title: string;
  type: string;
  department: string;
  jurisdiction: string;
  status: DocumentStatus;
  issuedDate: string;
  referenceNumber: string;
}

export interface DocumentDetail extends DocumentSummary {
  sourceUrl: string;
  cachedCopyUrl?: string;
  summary: string;
  keyProvisions: string[];
  metadata: Record<string, string>;
}

export type CrossLinkType = 'issued_under' | 'supersedes' | 'superseded_by' | 'interprets' | 'cites';

export interface CrossLink {
  type: CrossLinkType;
  document: DocumentSummary;
}

export interface GraphNode {
  id: string;
  label: string;
  type: string;
}

export interface GraphEdge {
  source: string;
  target: string;
  type: string;
}

export interface DocumentGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface SearchResult extends DocumentSummary {
  snippet: string;
}

export interface SearchResponse extends Paginated<SearchResult> {
  facets: {
    department: FacetCount[];
    type: FacetCount[];
    jurisdiction: FacetCount[];
  };
}

export interface AutocompleteSuggestion {
  label: string;
  entityType: string;
  entityId: string;
}

export interface ActivityItem {
  id: string;
  type: string;
  description: string;
  timestamp: string;
  documentId?: string;
}

export interface AlertItem {
  id: string;
  title: string;
  description: string;
  createdAt: string;
  severity: Severity;
}

export interface DashboardSummary {
  trendingSearches: { term: string; count: number }[];
  frequentDocuments: DocumentSummary[];
  departmentActivity: { departmentId: string; departmentName: string; count: number }[];
  corpusHealth: {
    classificationConfidenceAvg: number;
    extractionConfidenceAvg: number;
    classificationConfidenceDistribution: { bucket: string; count: number }[];
    extractionConfidenceDistribution: { bucket: string; count: number }[];
  };
}

export interface ChangeRadarItem {
  id: string;
  severity: Severity;
  title: string;
  whatChanged: string;
  publishedAt: string;
  affectedDocuments: DocumentSummary[];
}

export interface Scheme {
  id: string;
  name: string;
  department: string;
  summary: string;
  sourceUrl: string;
}

export interface SchemeMatch {
  scheme: Scheme;
  matchedConditions: string[];
  missingConditions: string[];
  requiredDocuments: string[];
  sourceUrl: string;
}
