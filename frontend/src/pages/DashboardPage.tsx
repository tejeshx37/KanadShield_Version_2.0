import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip, CartesianGrid } from 'recharts';
import { PageHeader } from '../components/ui/PageHeader';
import { LoadingState, ErrorState, EmptyState } from '../components/ui/QueryStates';
import {
  useCorpusHealth,
  useDepartmentInsights,
  useFrequentDocuments,
  useSearchHistory,
  useTrendingSearches,
  useUserAlerts,
} from '../api/hooks';
import { ApiError } from '../api/client';

function Card({ children, className = '' }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={`rounded-[--radius-token] border border-card-border bg-card-bg p-5 ${className}`}>
      {children}
    </div>
  );
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-ink-muted">{children}</p>;
}

function AuthGatedState({ error, onRetry }: { error: unknown; onRetry: () => void }) {
  if (error instanceof ApiError && error.status === 401) {
    return <EmptyState title="Sign in required" description="This section shows your personal activity once signed in." />;
  }
  return <ErrorState error={error} onRetry={onRetry} />;
}

export function DashboardPage() {
  const trending = useTrendingSearches();
  const frequent = useFrequentDocuments();
  const departments = useDepartmentInsights();
  const corpusHealth = useCorpusHealth();
  const history = useSearchHistory();
  const alerts = useUserAlerts();

  return (
    <div>
      <PageHeader
        title="Dashboard"
        description="Your recent activity, active alerts, and platform-wide analytics."
      />

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        <Card>
          <SectionLabel>Trending Searches</SectionLabel>
          {trending.isLoading && <LoadingState label="Loading trending searches…" />}
          {trending.isError && <ErrorState error={trending.error} onRetry={() => trending.refetch()} />}
          {trending.data && trending.data.items.length === 0 && <EmptyState title="No trending searches yet" />}
          {trending.data && trending.data.items.length > 0 && (
            <ul className="flex flex-col gap-2">
              {trending.data.items.map((s) => (
                <li key={s.query} className="flex items-center justify-between text-sm">
                  <span className="text-ink">{s.query}</span>
                  <span className="text-ink-muted">{s.count}</span>
                </li>
              ))}
            </ul>
          )}
        </Card>

        <Card>
          <SectionLabel>Frequently Accessed Documents</SectionLabel>
          {frequent.isLoading && <LoadingState label="Loading document activity…" />}
          {frequent.isError && <ErrorState error={frequent.error} onRetry={() => frequent.refetch()} />}
          {frequent.data && frequent.data.items.length === 0 && <EmptyState title="No document activity yet" />}
          {frequent.data && frequent.data.items.length > 0 && (
            <ul className="flex flex-col gap-2">
              {frequent.data.items.map((doc) => (
                <li key={doc.document_id} className="flex items-center justify-between text-sm">
                  <span className="text-ink">{doc.title}</span>
                  <span className="text-ink-muted">{doc.views} views</span>
                </li>
              ))}
            </ul>
          )}
        </Card>

        <Card className="lg:col-span-2">
          <SectionLabel>Department-wise Activity</SectionLabel>
          {departments.isLoading && <LoadingState label="Loading department activity…" />}
          {departments.isError && <ErrorState error={departments.error} onRetry={() => departments.refetch()} />}
          {departments.data && departments.data.items.length === 0 && (
            <EmptyState title="No department activity yet" />
          )}
          {departments.data && departments.data.items.length > 0 && (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={departments.data.items}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--card-border)" />
                  <XAxis dataKey="name" stroke="var(--ink-muted)" fontSize={12} />
                  <YAxis stroke="var(--ink-muted)" fontSize={12} />
                  <Tooltip
                    contentStyle={{
                      background: 'var(--card-bg)',
                      border: '1px solid var(--card-border)',
                      borderRadius: 8,
                    }}
                  />
                  <Bar dataKey="document_count" fill="var(--accent-gold)" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </Card>

        <Card>
          <SectionLabel>Corpus Health</SectionLabel>
          {corpusHealth.isLoading && <LoadingState label="Loading corpus health…" />}
          {corpusHealth.isError && <ErrorState error={corpusHealth.error} onRetry={() => corpusHealth.refetch()} />}
          {corpusHealth.data && (
            <div className="flex flex-col gap-2 text-sm text-ink">
              <div className="flex justify-between">
                <span>Total documents</span>
                <span className="mono font-medium">{corpusHealth.data.total_documents}</span>
              </div>
              <div className="flex justify-between">
                <span>Classification confidence — high</span>
                <span className="mono font-medium">
                  {corpusHealth.data.classification_confidence_distribution.high}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Classification confidence — low</span>
                <span className="mono font-medium">
                  {corpusHealth.data.classification_confidence_distribution.low}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Date extraction confidence — unknown</span>
                <span className="mono font-medium">
                  {corpusHealth.data.date_extraction_confidence_distribution.unknown}
                </span>
              </div>
            </div>
          )}
        </Card>

        <Card>
          <SectionLabel>Active Alerts</SectionLabel>
          {alerts.isLoading && <LoadingState label="Loading alerts…" />}
          {alerts.isError && <AuthGatedState error={alerts.error} onRetry={() => alerts.refetch()} />}
          {alerts.data && alerts.data.items.length === 0 && <EmptyState title="No active alerts" />}
          {alerts.data && alerts.data.items.length > 0 && (
            <ul className="flex flex-col gap-2">
              {alerts.data.items.map((a) => (
                <li key={a.id} className="flex items-center justify-between text-sm">
                  <span className="text-ink">{a.alert_type}</span>
                  <span className="text-xs text-ink-muted">{a.frequency}</span>
                </li>
              ))}
            </ul>
          )}
        </Card>

        <Card className="lg:col-span-2">
          <SectionLabel>Your Recent Searches</SectionLabel>
          {history.isLoading && <LoadingState label="Loading activity…" />}
          {history.isError && <AuthGatedState error={history.error} onRetry={() => history.refetch()} />}
          {history.data && history.data.items.length === 0 && <EmptyState title="No recent activity" />}
          {history.data && history.data.items.length > 0 && (
            <ul className="flex flex-col gap-2">
              {history.data.items.map((item, i) => (
                <li key={i} className="flex items-center justify-between text-sm">
                  <span className="text-ink">{item.query}</span>
                  <span className="text-xs text-ink-muted">
                    {item.result_count} results · {new Date(item.created_at).toLocaleString()}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>
    </div>
  );
}
