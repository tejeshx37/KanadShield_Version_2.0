export type DocumentType =
  | 'ACT'
  | 'RULE'
  | 'REGULATION'
  | 'GR'
  | 'NOTIFICATION'
  | 'CIRCULAR'
  | 'ORDER'
  | 'GAZETTE'
  | 'JUDGMENT'
  | 'SCHEME'
  | 'ORDINANCE'
  | 'STATUTE'
  | 'GUIDELINE'
  | 'OTHER'

export type Jurisdiction = 'CENTRAL' | 'STATE'

export interface DocumentSummary {
  id: string
  source: string
  title: string
  document_type: DocumentType
  jurisdiction: Jurisdiction
  state: string | null
  source_language: string
  date: string | null
  year: number | null
  subject: string | null
  source_url: string | null
  text_available: boolean
  classification_confidence: number | null
}

export interface DocumentDetail extends DocumentSummary {
  case_number: string | null
  act_number: string | null
  keywords: string[] | null
  pdf_path: string | null
  date_confidence: number | null
  doc_metadata: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface SearchResultItem {
  document_id: string
  title: string
  document_type: string
  jurisdiction: string
  state: string | null
  date: string | null
  source_url: string | null
  snippet: string
  score: number
  lexical_score: number
  semantic_score: number
}

export interface SearchResponse {
  items: SearchResultItem[]
  total: number
  page: number
  page_size: number
  facets: { document_type: Record<string, number>; jurisdiction: Record<string, number> }
  search_time_ms: number
}

export interface DocumentSummaryAI {
  summary: string
  key_provisions: string[]
  eligibility: string[]
  conditions: string[]
  dates: string[]
  limitations: string[]
  source_references: { document_id: string; page: number | null; section: string | null; source_url: string | null }[]
}

export interface AskAnswer {
  answer: string
  citations: { document_id: string; page: number | null; section: string | null; source_url: string | null }[]
  insufficient_evidence: boolean
}

export interface SchemeMatchResult {
  scheme_id: string
  scheme_name: string
  matched_conditions: string[]
  missing_conditions: string[]
  required_documents: string[]
  official_source: string | null
  explanation: string
  is_potentially_eligible: boolean
}
