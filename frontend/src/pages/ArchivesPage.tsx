import { FileText } from 'lucide-react';
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { PageHeader } from '../components/ui/PageHeader';
import { LoadingState, ErrorState, EmptyState } from '../components/ui/QueryStates';
import { useArchivesList } from '../api/hooks';
import { DOCUMENT_TYPES, JURISDICTIONS, documentTypeLabel, jurisdictionLabel } from '../lib/referenceData';

export function ArchivesPage() {
  const [documentType, setDocumentType] = useState('');
  const [jurisdiction, setJurisdiction] = useState('');
  const [state, setState] = useState('');
  const [page, setPage] = useState(1);

  const list = useArchivesList({
    document_type: documentType || undefined,
    jurisdiction: jurisdiction || undefined,
    state: state || undefined,
    page,
    page_size: 20,
  });

  return (
    <div>
      <PageHeader title="Archives" description="Browse and filter the full document corpus." />

      <div className="mb-6 flex flex-wrap gap-3">
        <select
          value={documentType}
          onChange={(e) => {
            setDocumentType(e.target.value);
            setPage(1);
          }}
          className="rounded-[--radius-token] border border-card-border bg-card-bg px-3 py-2 text-sm"
        >
          <option value="">All types</option>
          {DOCUMENT_TYPES.map((t) => (
            <option key={t} value={t}>
              {documentTypeLabel(t)}
            </option>
          ))}
        </select>
        <select
          value={jurisdiction}
          onChange={(e) => {
            setJurisdiction(e.target.value);
            setPage(1);
          }}
          className="rounded-[--radius-token] border border-card-border bg-card-bg px-3 py-2 text-sm"
        >
          <option value="">All jurisdictions</option>
          {JURISDICTIONS.map((j) => (
            <option key={j} value={j}>
              {jurisdictionLabel(j)}
            </option>
          ))}
        </select>
        <input
          value={state}
          onChange={(e) => {
            setState(e.target.value);
            setPage(1);
          }}
          placeholder="State (e.g. Gujarat)"
          className="rounded-[--radius-token] border border-card-border bg-card-bg px-3 py-2 text-sm"
        />
      </div>

      {list.isLoading && <LoadingState label="Loading archives…" />}
      {list.isError && <ErrorState error={list.error} onRetry={() => list.refetch()} />}
      {list.data && list.data.items.length === 0 && (
        <EmptyState title="No documents found" description="Try adjusting your filters." />
      )}

      {list.data && list.data.items.length > 0 && (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {list.data.items.map((doc) => (
            <Link
              key={doc.id}
              to={`/archives/documents/${doc.id}`}
              className="block rounded-[--radius-token] border border-card-border bg-card-bg p-5 hover:border-accent-gold"
            >
              <div className="mb-2 flex items-center justify-between text-xs text-ink-muted">
                <span className="rounded-full bg-accent-gold-soft px-2.5 py-1 font-semibold text-accent-gold">
                  {documentTypeLabel(doc.document_type)}
                </span>
                <span>{doc.date ? new Date(doc.date).toLocaleDateString() : 'Date unknown'}</span>
              </div>
              <p className="mb-1 flex items-center gap-2 text-base font-bold text-ink">
                <FileText size={16} className="text-ink-muted" aria-hidden="true" />
                {doc.title}
              </p>
              <p className="text-xs text-ink-muted">
                {jurisdictionLabel(doc.jurisdiction)}
                {doc.state ? ` · ${doc.state}` : ''}
                {doc.year ? ` · ${doc.year}` : ''}
              </p>
            </Link>
          ))}
        </div>
      )}

      {list.data && list.data.total > list.data.page_size && (
        <div className="mt-6 flex items-center justify-center gap-4">
          <button
            type="button"
            disabled={page <= 1}
            onClick={() => setPage((p) => p - 1)}
            className="rounded-[--radius-token] border border-card-border px-3 py-1.5 text-sm disabled:opacity-40"
          >
            Previous
          </button>
          <span className="text-sm text-ink-muted">Page {page}</span>
          <button
            type="button"
            disabled={page * list.data.page_size >= list.data.total}
            onClick={() => setPage((p) => p + 1)}
            className="rounded-[--radius-token] border border-card-border px-3 py-1.5 text-sm disabled:opacity-40"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
