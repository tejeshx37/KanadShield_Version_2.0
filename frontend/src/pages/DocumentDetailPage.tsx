import { ExternalLink, FileText, Sparkles } from 'lucide-react';
import { Link, useParams } from 'react-router-dom';
import { LoadingState, ErrorState, EmptyState } from '../components/ui/QueryStates';
import { StatusPill } from '../components/ui/Pills';
import { useDocumentAiSummary, useDocumentDetail, useDocumentGraph } from '../api/hooks';
import { DocumentGraphView } from '../components/archives/DocumentGraphView';
import { deriveCrossLinks, deriveDocumentStatus, relationshipLabel } from '../lib/documentGraph';
import { documentTypeLabel, jurisdictionLabel } from '../lib/referenceData';

function AiSummarySection({ documentId }: { documentId: string }) {
  const { request, job } = useDocumentAiSummary(documentId);

  if (request.isIdle) {
    return (
      <button
        type="button"
        onClick={() => request.mutate()}
        className="inline-flex items-center gap-2 rounded-[--radius-token] border border-accent-gold px-4 py-2 text-sm font-semibold text-accent-gold hover:bg-accent-gold-soft"
      >
        <Sparkles size={16} aria-hidden="true" />
        Generate AI Summary
      </button>
    );
  }

  if (request.isPending || job.data?.status === 'pending' || (!job.data && job.isLoading)) {
    return <LoadingState label="Generating grounded summary… this runs as a background job and may take a moment." />;
  }

  if (request.isError) {
    return <ErrorState error={request.error} onRetry={() => request.mutate()} />;
  }

  if (job.data?.status === 'failed') {
    return <ErrorState error={new Error(job.data.error)} onRetry={() => request.mutate()} />;
  }

  if (job.data?.status === 'insufficient_evidence') {
    return (
      <EmptyState
        title="Insufficient evidence"
        description="The AI couldn't produce a grounded summary from the retrieved text for this document."
      />
    );
  }

  if (job.data?.status === 'success') {
    const result = job.data.result;
    return (
      <div>
        <p className="text-sm leading-relaxed text-ink">{result.summary}</p>
        {result.key_provisions.length > 0 && (
          <>
            <p className="mb-2 mt-4 text-xs font-semibold uppercase tracking-wide text-ink-muted">Key Provisions</p>
            <ul className="list-disc pl-5 text-sm text-ink">
              {result.key_provisions.map((p, i) => (
                <li key={i}>{p}</li>
              ))}
            </ul>
          </>
        )}
        {result.source_references.length > 0 && (
          <>
            <p className="mb-2 mt-4 text-xs font-semibold uppercase tracking-wide text-ink-muted">Grounded In</p>
            <ul className="flex flex-col gap-1 text-xs text-ink-muted">
              {result.source_references.map((ref, i) => (
                <li key={i}>
                  {ref.section ?? 'Referenced passage'}
                  {ref.page ? `, p.${ref.page}` : ''}
                </li>
              ))}
            </ul>
          </>
        )}
      </div>
    );
  }

  return <LoadingState label="Waiting for summary job…" />;
}

export function DocumentDetailPage() {
  const { id } = useParams<{ id: string }>();
  const detail = useDocumentDetail(id);
  const graph = useDocumentGraph(id);

  if (detail.isLoading) return <LoadingState label="Loading document…" />;
  if (detail.isError) return <ErrorState error={detail.error} onRetry={() => detail.refetch()} />;
  if (!detail.data) return null;

  const doc = detail.data;
  const referenceNumber = doc.case_number ?? doc.act_number ?? doc.id.slice(0, 8);

  const centerNode = graph.data?.nodes.find((n) => n.document_id === doc.id);
  const status = graph.data && centerNode ? deriveDocumentStatus(graph.data.edges, centerNode.id) : undefined;
  const crossLinks = graph.data && centerNode ? deriveCrossLinks(graph.data, centerNode.id) : [];

  return (
    <div>
      <div className="mb-6 flex items-start justify-between gap-4">
        <div>
          <div className="mb-2 flex items-center gap-3">
            {status && <StatusPill status={status} />}
            <span className="mono text-xs text-ink-muted">{referenceNumber}</span>
          </div>
          <h1 className="font-serif text-3xl font-bold text-ink">{doc.title}</h1>
          <p className="mt-1 text-sm text-ink-muted">
            {jurisdictionLabel(doc.jurisdiction)}
            {doc.state ? ` · ${doc.state}` : ''} · {documentTypeLabel(doc.document_type)}
            {doc.date ? ` · ${new Date(doc.date).toLocaleDateString()}` : ''}
          </p>
        </div>
      </div>

      <div className="mb-6 flex flex-wrap gap-3">
        {doc.source_url ? (
          <a
            href={doc.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 rounded-[--radius-token] bg-accent-gold px-4 py-2.5 text-sm font-semibold text-white"
          >
            <ExternalLink size={16} aria-hidden="true" />
            View Original Source
          </a>
        ) : (
          <p className="rounded-[--radius-token] border border-card-border bg-card-bg px-4 py-2.5 text-sm text-ink-muted">
            No official source URL recorded for this document.
          </p>
        )}
      </div>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-[1fr_320px]">
        <div className="flex flex-col gap-5">
          <div className="rounded-[--radius-token] border border-card-border bg-card-bg p-5">
            <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-ink-muted">AI Summary</p>
            {doc.text_available ? (
              id && <AiSummarySection documentId={id} />
            ) : (
              <EmptyState
                title="No extracted text available"
                description="This document has no extracted text on file, so a grounded summary can't be generated."
              />
            )}
          </div>

          <div className="rounded-[--radius-token] border border-card-border bg-card-bg p-5">
            <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-ink-muted">Metadata</p>
            <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
              <dt className="text-ink-muted">Source</dt>
              <dd className="text-ink">{doc.source}</dd>
              <dt className="text-ink-muted">Language</dt>
              <dd className="text-ink">{doc.source_language}</dd>
              {doc.subject && (
                <>
                  <dt className="text-ink-muted">Subject</dt>
                  <dd className="text-ink">{doc.subject}</dd>
                </>
              )}
              {doc.keywords && doc.keywords.length > 0 && (
                <>
                  <dt className="text-ink-muted">Keywords</dt>
                  <dd className="text-ink">{doc.keywords.join(', ')}</dd>
                </>
              )}
              {doc.classification_confidence != null && (
                <>
                  <dt className="text-ink-muted">Classification confidence</dt>
                  <dd className="mono text-ink">{(doc.classification_confidence * 100).toFixed(0)}%</dd>
                </>
              )}
            </dl>
          </div>
        </div>

        <div className="flex flex-col gap-5">
          <div className="rounded-[--radius-token] border border-card-border bg-card-bg p-5">
            <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-ink-muted">
              Cross-Linked Documents
            </p>
            {graph.isLoading && <LoadingState label="Loading links…" />}
            {graph.isError && <ErrorState error={graph.error} onRetry={() => graph.refetch()} />}
            {graph.data && crossLinks.length === 0 && !graph.isLoading && (
              <EmptyState title="No cross-links found" />
            )}
            {crossLinks.length > 0 && (
              <ul className="flex flex-col gap-3">
                {crossLinks.map((link, i) => (
                  <li key={i}>
                    <p className="mb-1 text-xs font-medium text-ink-muted">
                      {link.direction === 'outgoing' ? relationshipLabel(link.relationshipType) : `${relationshipLabel(link.relationshipType)} (by)`}
                    </p>
                    <Link
                      to={`/archives/documents/${link.node.document_id}`}
                      className="flex items-center gap-2 text-sm text-ink underline decoration-card-border underline-offset-2 hover:text-accent-gold"
                    >
                      <FileText size={14} className="shrink-0 text-ink-muted" aria-hidden="true" />
                      {link.node.name}
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="rounded-[--radius-token] border border-card-border bg-card-bg p-5">
            <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-ink-muted">
              Legal Knowledge Graph
            </p>
            {graph.isLoading && <LoadingState label="Loading graph…" />}
            {graph.isError && <ErrorState error={graph.error} onRetry={() => graph.refetch()} />}
            {graph.data && graph.data.nodes.length <= 1 && <EmptyState title="No graph relationships found" />}
            {graph.data && graph.data.nodes.length > 1 && id && (
              <DocumentGraphView graph={graph.data} centerDocumentId={id} />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
