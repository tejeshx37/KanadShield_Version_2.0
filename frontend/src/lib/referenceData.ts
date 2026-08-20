// Mirrors backend/app/models/enums.py DocumentType and Jurisdiction.
// The backend exposes no list endpoint for these — they are fixed Python
// enums, not corpus-derived reference data — so they're kept here as the
// single source of truth on the frontend side instead of duplicated inline
// in each component that needs them.

export const DOCUMENT_TYPES = [
  'ACT',
  'RULE',
  'REGULATION',
  'GR',
  'NOTIFICATION',
  'CIRCULAR',
  'ORDER',
  'GAZETTE',
  'JUDGMENT',
  'SCHEME',
  'ORDINANCE',
  'STATUTE',
  'GUIDELINE',
  'OTHER',
] as const;

export type DocumentType = (typeof DOCUMENT_TYPES)[number];

export const JURISDICTIONS = ['CENTRAL', 'STATE'] as const;

export type Jurisdiction = (typeof JURISDICTIONS)[number];

const documentTypeLabels: Record<DocumentType, string> = {
  ACT: 'Act',
  RULE: 'Rule',
  REGULATION: 'Regulation',
  GR: 'Government Resolution',
  NOTIFICATION: 'Notification',
  CIRCULAR: 'Circular',
  ORDER: 'Order',
  GAZETTE: 'Gazette',
  JUDGMENT: 'Judgment',
  SCHEME: 'Scheme',
  ORDINANCE: 'Ordinance',
  STATUTE: 'Statute',
  GUIDELINE: 'Guideline',
  OTHER: 'Other',
};

export function documentTypeLabel(type: string): string {
  return documentTypeLabels[type as DocumentType] ?? type;
}

const jurisdictionLabels: Record<Jurisdiction, string> = {
  CENTRAL: 'Central',
  STATE: 'State',
};

export function jurisdictionLabel(jurisdiction: string): string {
  return jurisdictionLabels[jurisdiction as Jurisdiction] ?? jurisdiction;
}
