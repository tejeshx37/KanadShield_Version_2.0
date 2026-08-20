import type { DocumentGraph, DocumentStatus, GraphEdge, GraphNode } from '../api/types';

export interface CrossLink {
  relationshipType: string;
  direction: 'incoming' | 'outgoing';
  node: GraphNode;
}

const relationshipLabels: Record<string, string> = {
  CONTAINS: 'Contains',
  AMENDS: 'Amends',
  AMENDED_BY: 'Amended By',
  REPEALS: 'Repeals',
  REPEALED_BY: 'Repealed By',
  IMPLEMENTS: 'Implements',
  IMPLEMENTED_BY: 'Implemented By',
  CITES: 'Cites',
  CITED_BY: 'Cited By',
  INTERPRETS: 'Interprets',
  INTERPRETED_BY: 'Interpreted By',
  REFERS_TO: 'Refers To',
  RELATED_TO: 'Related To',
  PUBLISHED_IN: 'Published In',
  ISSUED_BY: 'Issued By',
  BELONGS_TO: 'Belongs To',
  SUPERSEDES: 'Supersedes',
  SUPERSEDED_BY: 'Superseded By',
};

export function relationshipLabel(type: string): string {
  return relationshipLabels[type] ?? type;
}

/** Cross-linked documents: graph edges touching the center node whose
 * counterpart entity resolves to a real ingested document. Entities that
 * are just text mentions (no canonical_document_id) aren't a "document"
 * the UI can link to, so they're excluded here — they still show in the
 * graph view itself. */
export function deriveCrossLinks(graph: DocumentGraph, centerNodeId: string): CrossLink[] {
  const nodesById = new Map(graph.nodes.map((n) => [n.id, n]));
  const links: CrossLink[] = [];

  for (const edge of graph.edges) {
    if (edge.source === centerNodeId) {
      const node = nodesById.get(edge.target);
      if (node?.document_id) links.push({ relationshipType: edge.type, direction: 'outgoing', node });
    } else if (edge.target === centerNodeId) {
      const node = nodesById.get(edge.source);
      if (node?.document_id) links.push({ relationshipType: edge.type, direction: 'incoming', node });
    }
  }

  return links;
}

/** Derives an honest active/amended/superseded status from real relationship
 * edges. The backend has no explicit status field, and its extractor only
 * ever emits the forward relationship types (AMENDS, SUPERSEDES — never
 * AMENDED_BY/SUPERSEDED_BY, see relationship_extraction.py) with the
 * mentioning document as edge source. So "center is amended/superseded"
 * means center is the TARGET of an incoming AMENDS/SUPERSEDES edge. */
export function deriveDocumentStatus(edges: GraphEdge[], centerNodeId: string): DocumentStatus {
  const incoming = edges.filter((e) => e.target === centerNodeId);
  if (incoming.some((e) => e.type === 'SUPERSEDES')) return 'superseded';
  if (incoming.some((e) => e.type === 'AMENDS')) return 'amended';
  return 'active';
}
