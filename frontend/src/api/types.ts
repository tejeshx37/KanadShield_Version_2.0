// Shapes mirror backend/app/schemas/*.py and the dict responses returned
// directly by backend/app/api/v1/*.py — see that source for the
// authoritative definitions.

export type DocumentStatus = 'active' | 'amended' | 'superseded';

export interface Paginated<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface Department {
  id: string;
  name: string;
  ministry_id: string | null;
}

export interface Ministry {
  id: string;
  name: string;
}

export interface Court {
  id: string;
  name: string;
}

export interface DocumentSummary {
  id: string;
  source: string;
  title: string;
  document_type: string;
  jurisdiction: string;
  state: string | null;
  source_language: string;
  date: string | null;
  year: number | null;
  subject: string | null;
  source_url: string | null;
  text_available: boolean;
  classification_confidence: number | null;
}

export interface DocumentDetail extends DocumentSummary {
  case_number: string | null;
  act_number: string | null;
  keywords: string[] | null;
  pdf_path: string | null;
  date_confidence: number | null;
  doc_metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface SearchResultItem {
  document_id: string;
  title: string;
  document_type: string;
  jurisdiction: string;
  state: string | null;
  date: string | null;
  source_url: string | null;
  snippet: string;
  score: number;
  lexical_score: number;
  semantic_score: number;
}

export interface SearchResponse {
  items: SearchResultItem[];
  total: number;
  page: number;
  page_size: number;
  facets: {
    document_type: Record<string, number>;
    jurisdiction: Record<string, number>;
  };
  search_time_ms: number;
}

export interface TrendingSearch {
  query: string;
  count: number;
}

export interface FrequentDocument {
  document_id: string;
  title: string;
  views: number;
}

export interface DepartmentInsight {
  department_id: string;
  name: string;
  document_count: number;
  last_activity: string | null;
}

export interface ConfidenceDistribution {
  high: number;
  medium: number;
  low: number;
  unknown: number;
}

export interface CorpusHealth {
  total_documents: number;
  ingestion_volume_by_month: { month: string; count: number }[];
  classification_confidence_distribution: ConfidenceDistribution;
  date_extraction_confidence_distribution: ConfidenceDistribution;
}

export interface SearchHistoryItem {
  query: string;
  filters: Record<string, unknown>;
  result_count: number;
  created_at: string;
}

export interface AlertItem {
  id: string;
  alert_type: string;
  target: Record<string, unknown>;
  frequency: string;
  is_active: boolean;
  last_checked_at: string | null;
}

export interface GraphNode {
  id: string;
  type: string;
  name: string;
  document_id: string | null;
}

export interface GraphEdge {
  source: string;
  target: string;
  type: string;
  confidence: number | null;
  evidence_text: string | null;
}

export interface DocumentGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

// AI jobs (backend/app/api/v1/ai.py) are async: POST enqueues a Celery job,
// GET /ai/jobs/{id} is polled until it settles.
export interface JobAccepted {
  job_id: string;
  status: 'queued';
}

export interface SourceReference {
  document_id: string;
  page: number | null;
  section: string | null;
  source_url: string | null;
}

export interface DocumentSummaryResult {
  summary: string;
  key_provisions: string[];
  eligibility: string[];
  conditions: string[];
  dates: string[];
  limitations: string[];
  source_references: SourceReference[];
}

export type JobStatus =
  | { status: 'pending' }
  | { status: 'failed'; error: string }
  | { status: 'success'; result: DocumentSummaryResult }
  | { status: 'insufficient_evidence'; error?: string }
  | { status: 'started' | 'retry' | 'revoked' };
