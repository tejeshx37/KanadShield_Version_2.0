import { FileText } from 'lucide-react';
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { PageHeader } from '../components/ui/PageHeader';
import { LoadingState, ErrorState, EmptyState } from '../components/ui/QueryStates';
import { StatusPill } from '../components/ui/Pills';
import { useArchivesList, useDepartments, useDocumentTypes, useJurisdictions } from '../api/hooks';

export function ArchivesPage() {
  const [department, setDepartment] = useState('');
  const [type, setType] = useState('');
  const [jurisdiction, setJurisdiction] = useState('');
  const [page, setPage] = useState(1);

  const departments = useDepartments();
  const documentTypes = useDocumentTypes();
  const jurisdictions = useJurisdictions();

  const list = useArchivesList({
    department: department || undefined,
    type: type || undefined,
    jurisdiction: jurisdiction || undefined,
    page,
    pageSize: 20,
  });

  return (
    <div>
      <PageHeader title="Archives" description="Browse and filter the full document corpus." />

      <div className="mb-6 flex flex-wrap gap-3">
        <select
          value={department}
          onChange={(e) => {
            setDepartment(e.target.value);
            setPage(1);
          }}
          className="rounded-[--radius-token] border border-card-border bg-card-bg px-3 py-2 text-sm"
        >
          <option value="">All departments</option>
          {departments.data?.map((d) => (
            <option key={d.id} value={d.id}>
              {d.name}
            </option>
          ))}
        </select>
        <select
          value={type}
          onChange={(e) => {
            setType(e.target.value);
            setPage(1);
          }}
          className="rounded-[--radius-token] border border-card-border bg-card-bg px-3 py-2 text-sm"
        >
          <option value="">All types</option>
          {documentTypes.data?.map((t) => (
            <option key={t.id} value={t.id}>
              {t.name}
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
          {jurisdictions.data?.map((j) => (
            <option key={j.id} value={j.id}>
              {j.name}
            </option>
          ))}
        </select>
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
              <div className="mb-2 flex items-center justify-between">
                <StatusPill status={doc.status} />
                <span className="mono text-xs text-ink-muted">{doc.referenceNumber}</span>
              </div>
              <p className="mb-1 flex items-center gap-2 text-base font-bold text-ink">
                <FileText size={16} className="text-ink-muted" aria-hidden="true" />
                {doc.title}
              </p>
              <p className="text-xs text-ink-muted">
                {doc.department} · {doc.type} · {new Date(doc.issuedDate).toLocaleDateString()}
              </p>
            </Link>
          ))}
        </div>
      )}

      {list.data && list.data.total > list.data.pageSize && (
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
            disabled={page * list.data.pageSize >= list.data.total}
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
