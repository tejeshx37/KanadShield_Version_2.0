import { FileText } from 'lucide-react';
import { useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Link } from 'react-router-dom';
import { PageHeader } from '../components/ui/PageHeader';
import { LoadingState, ErrorState, EmptyState } from '../components/ui/QueryStates';
import { StatusPill } from '../components/ui/Pills';
import { useDepartments, useDocumentTypes, useJurisdictions, useSearch } from '../api/hooks';

function FacetGroup({
  title,
  facets,
  activeId,
  onSelect,
}: {
  title: string;
  facets: { id: string; label: string; count: number }[];
  activeId?: string;
  onSelect: (id?: string) => void;
}) {
  return (
    <div className="mb-6">
      <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-ink-muted">{title}</p>
      <ul className="flex flex-col gap-1">
        {facets.map((f) => (
          <li key={f.id}>
            <button
              type="button"
              onClick={() => onSelect(activeId === f.id ? undefined : f.id)}
              className={`flex w-full items-center justify-between rounded-[--radius-token] px-2 py-1.5 text-left text-sm ${
                activeId === f.id ? 'bg-accent-gold-soft text-ink' : 'text-ink-muted hover:bg-card-border/40'
              }`}
            >
              <span>{f.label}</span>
              <span>{f.count}</span>
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
  const department = searchParams.get('department') ?? undefined;
  const type = searchParams.get('type') ?? undefined;
  const jurisdiction = searchParams.get('jurisdiction') ?? undefined;

  useDepartments();
  useDocumentTypes();
  useJurisdictions();

  const params = useMemo(
    () => ({ q: searchParams.get('q') ?? '', department, type, jurisdiction }),
    [searchParams, department, type, jurisdiction],
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
            {results.data?.facets && (
              <>
                <FacetGroup
                  title="Department"
                  facets={results.data.facets.department}
                  activeId={department}
                  onSelect={(v) => updateParam('department', v)}
                />
                <FacetGroup
                  title="Type"
                  facets={results.data.facets.type}
                  activeId={type}
                  onSelect={(v) => updateParam('type', v)}
                />
                <FacetGroup
                  title="Jurisdiction"
                  facets={results.data.facets.jurisdiction}
                  activeId={jurisdiction}
                  onSelect={(v) => updateParam('jurisdiction', v)}
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
                    key={r.id}
                    to={`/archives/documents/${r.id}`}
                    className="block rounded-[--radius-token] border border-card-border bg-card-bg p-5 hover:border-accent-gold"
                  >
                    <div className="mb-2 flex items-center justify-between">
                      <StatusPill status={r.status} />
                      <span className="mono text-xs text-ink-muted">{r.referenceNumber}</span>
                    </div>
                    <p className="mb-1 flex items-center gap-2 text-base font-bold text-ink">
                      <FileText size={16} className="text-ink-muted" aria-hidden="true" />
                      {r.title}
                    </p>
                    <p className="mb-2 text-xs text-ink-muted">
                      {r.department} · {r.type} · {new Date(r.issuedDate).toLocaleDateString()}
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
