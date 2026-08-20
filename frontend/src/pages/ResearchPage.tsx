import { FileText } from 'lucide-react';
import { useMemo, useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { PageHeader } from '../components/ui/PageHeader';
import { LoadingState, ErrorState, EmptyState } from '../components/ui/QueryStates';
import { useDepartments, useSearch } from '../api/hooks';
import { documentTypeLabel, jurisdictionLabel } from '../lib/referenceData';

function FacetGroup({
  title,
  facets,
  activeId,
  onSelect,
  labelFor,
}: {
  title: string;
  facets: Record<string, number>;
  activeId?: string;
  onSelect: (id?: string) => void;
  labelFor: (id: string) => string;
}) {
  const entries = Object.entries(facets);
  if (entries.length === 0) return null;

  return (
    <div className="mb-6">
      <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-ink-muted">{title}</p>
      <ul className="flex flex-col gap-1">
        {entries.map(([id, count]) => (
          <li key={id}>
            <button
              type="button"
              onClick={() => onSelect(activeId === id ? undefined : id)}
              className={`flex w-full items-center justify-between rounded-[--radius-token] px-2 py-1.5 text-left text-sm ${
                activeId === id ? 'bg-accent-gold-soft text-ink' : 'text-ink-muted hover:bg-card-border/40'
              }`}
            >
              <span>{labelFor(id)}</span>
              <span>{count}</span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function ResearchPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [inputValue, setInputValue] = useState(searchParams.get('q') ?? '');
  const documentType = searchParams.get('document_type') ?? undefined;
  const jurisdiction = searchParams.get('jurisdiction') ?? undefined;
  const department = searchParams.get('department') ?? undefined;

  const departments = useDepartments();

  const params = useMemo(
    () => ({
      q: searchParams.get('q') ?? '',
      document_type: documentType,
      jurisdiction,
      department,
    }),
    [searchParams, documentType, jurisdiction, department],
  );

  const results = useSearch(params);

  function updateParam(key: string, value?: string) {
    const next = new URLSearchParams(searchParams);
    if (value) next.set(key, value);
    else next.delete(key);
    setSearchParams(next);
  }

  return (
    <div>
      <PageHeader title="Research" description="Unified keyword and semantic search across the corpus." />

      <form
        onSubmit={(e) => {
          e.preventDefault();
          updateParam('q', inputValue);
        }}
        className="mb-6 flex gap-2"
      >
        <input
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder="Search by keyword, citation, or concept…"
          className="flex-1 rounded-[--radius-token] border border-card-border bg-card-bg px-4 py-2.5 text-sm focus:outline-none"
        />
        <button
          type="submit"
          className="rounded-[--radius-token] bg-accent-gold px-5 py-2.5 text-sm font-semibold text-white"
        >
          Search
        </button>
      </form>

      {!params.q && <EmptyState title="Start a search" description="Enter a term above to search the corpus." />}

      {params.q && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-[220px_1fr]">
          <aside>
            <div className="mb-6">
              <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-ink-muted">Department</p>
              <select
                value={department ?? ''}
                onChange={(e) => updateParam('department', e.target.value || undefined)}
                className="w-full rounded-[--radius-token] border border-card-border bg-card-bg px-2 py-1.5 text-sm"
              >
                <option value="">All departments</option>
                {departments.data?.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.name}
                  </option>
                ))}
              </select>
            </div>

            {results.data?.facets && (
              <>
                <FacetGroup
                  title="Type"
                  facets={results.data.facets.document_type}
                  activeId={documentType}
                  onSelect={(v) => updateParam('document_type', v)}
                  labelFor={documentTypeLabel}
                />
                <FacetGroup
                  title="Jurisdiction"
                  facets={results.data.facets.jurisdiction}
                  activeId={jurisdiction}
                  onSelect={(v) => updateParam('jurisdiction', v)}
                  labelFor={jurisdictionLabel}
                />
              </>
            )}
          </aside>

          <section>
            {results.isLoading && <LoadingState label="Searching…" />}
            {results.isError && <ErrorState error={results.error} onRetry={() => results.refetch()} />}
            {results.data && results.data.items.length === 0 && (
              <EmptyState title="No results" description="Try a different search term or clear filters." />
            )}
            {results.data && results.data.items.length > 0 && (
              <div className="flex flex-col gap-4">
                {results.data.items.map((r) => (
                  <Link
                    key={r.document_id}
                    to={`/archives/documents/${r.document_id}`}
                    className="block rounded-[--radius-token] border border-card-border bg-card-bg p-5 hover:border-accent-gold"
                  >
                    <div className="mb-2 flex items-center justify-between text-xs text-ink-muted">
                      <span className="rounded-full bg-accent-gold-soft px-2.5 py-1 font-semibold text-accent-gold">
                        {documentTypeLabel(r.document_type)}
                      </span>
                      <span>{r.date ? new Date(r.date).toLocaleDateString() : 'Date unknown'}</span>
                    </div>
                    <p className="mb-1 flex items-center gap-2 text-base font-bold text-ink">
                      <FileText size={16} className="text-ink-muted" aria-hidden="true" />
                      {r.title}
                    </p>
                    <p className="mb-2 text-xs text-ink-muted">
                      {jurisdictionLabel(r.jurisdiction)}
                      {r.state ? ` · ${r.state}` : ''}
                    </p>
                    <p className="text-sm text-ink-muted">{r.snippet}</p>
                  </Link>
                ))}
              </div>
            )}
          </section>
        </div>
      )}
    </div>
  );
}
