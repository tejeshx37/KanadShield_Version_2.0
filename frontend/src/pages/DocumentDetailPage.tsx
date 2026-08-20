import { ExternalLink, FileText } from 'lucide-react';
import { Link, useParams } from 'react-router-dom';
import { LoadingState, ErrorState, EmptyState } from '../components/ui/QueryStates';
import { StatusPill } from '../components/ui/Pills';
import { useDocumentCrossLinks, useDocumentDetail, useDocumentGraph } from '../api/hooks';
import { DocumentGraphView } from '../components/archives/DocumentGraphView';
import type { CrossLinkType } from '../api/types';

const crossLinkLabel: Record<CrossLinkType, string> = {
  issued_under: 'Issued Under',
  supersedes: 'Supersedes',
  superseded_by: 'Superseded By',
  interprets: 'Interprets',
  cites: 'Cites',
};

export function DocumentDetailPage() {
  const { id } = useParams<{ id: string }>();
  const detail = useDocumentDetail(id);
  const crossLinks = useDocumentCrossLinks(id);
  const graph = useDocumentGraph(id);

  if (detail.isLoading) return <LoadingState label="Loading document…" />;
  if (detail.isError) return <ErrorState error={detail.error} onRetry={() => detail.refetch()} />;
  if (!detail.data) return null;

  const doc = detail.data;

  return (
    <div>
      <div className="mb-6 flex items-start justify-between gap-4">
        <div>
          <div className="mb-2 flex items-center gap-3">
            <StatusPill status={doc.status} />
            <span className="mono text-xs text-ink-muted">{doc.referenceNumber}</span>
          </div>
          <h1 className="font-serif text-3xl font-bold text-ink">{doc.title}</h1>
          <p className="mt-1 text-sm text-ink-muted">
            {doc.department} · {doc.type} · {doc.jurisdiction} · {new Date(doc.issuedDate).toLocaleDateString()}
          </p>
        </div>
      </div>

      <div className="mb-6 flex flex-wrap gap-3">
        <a
          href={doc.sourceUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 rounded-[--radius-token] bg-accent-gold px-4 py-2.5 text-sm font-semibold text-white"
        >
          <ExternalLink size={16} aria-hidden="true" />
          View Original Source
        </a>
        {doc.cachedCopyUrl && (
          <a
            href={doc.cachedCopyUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 rounded-[--radius-token] border border-card-border bg-card-bg px-4 py-2.5 text-sm font-medium text-ink"
          >
            <FileText size={16} aria-hidden="true" />
            View Cached Copy
          </a>
        )}
      </div>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-[1fr_320px]">
        <div className="flex flex-col gap-5">
          <div className="rounded-[--radius-token] border border-card-border bg-card-bg p-5">
            <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-ink-muted">AI Summary</p>
            <p className="text-sm leading-relaxed text-ink">{doc.summary}</p>
            {doc.keyProvisions.length > 0 && (
              <>
                <p className="mb-2 mt-4 text-xs font-semibold uppercase tracking-wide text-ink-muted">
                  Key Provisions
                </p>
                <ul className="list-disc pl-5 text-sm text-ink">
                  {doc.keyProvisions.map((p, i) => (
                    <li key={i}>{p}</li>
                  ))}
                </ul>
              </>
            )}
          </div>

          <div className="rounded-[--radius-token] border border-card-border bg-card-bg p-5">
            <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-ink-muted">Metadata</p>
            <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
              {Object.entries(doc.metadata).map(([key, value]) => (
                <div key={key} className="contents">
                  <dt className="text-ink-muted">{key}</dt>
                  <dd className="text-ink">{value}</dd>
                </div>
              ))}
            </dl>
          </div>
        </div>

        <div className="flex flex-col gap-5">
          <div className="rounded-[--radius-token] border border-card-border bg-card-bg p-5">
            <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-ink-muted">
              Cross-Linked Documents
            </p>
            {crossLinks.isLoading && <LoadingState label="Loading links…" />}
            {crossLinks.isError && <ErrorState error={crossLinks.error} onRetry={() => crossLinks.refetch()} />}
            {crossLinks.data && crossLinks.data.length === 0 && <EmptyState title="No cross-links found" />}
            {crossLinks.data && crossLinks.data.length > 0 && (
              <ul className="flex flex-col gap-3">
                {crossLinks.data.map((link, i) => (
                  <li key={i}>
                    <p className="mb-1 text-xs font-medium text-ink-muted">{crossLinkLabel[link.type]}</p>
                    <Link
                      to={`/archives/documents/${link.document.id}`}
                      className="flex items-center gap-2 text-sm text-ink underline decoration-card-border underline-offset-2 hover:text-accent-gold"
                    >
                      <FileText size={14} className="shrink-0 text-ink-muted" aria-hidden="true" />
                      {link.document.title}
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
              <DocumentGraphView graph={graph.data} centerId={id} />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
