import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip, CartesianGrid } from 'recharts';
import { PageHeader } from '../components/ui/PageHeader';
import { LoadingState, ErrorState, EmptyState } from '../components/ui/QueryStates';
import { useDashboardSummary, useUserActivity, useUserAlerts } from '../api/hooks';
import { useUiStore } from '../store/uiStore';
import { SeverityPill } from '../components/ui/Pills';

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

export function DashboardPage() {
  const activeDepartmentId = useUiStore((s) => s.activeDepartmentId) ?? undefined;
  const summary = useDashboardSummary(activeDepartmentId);
  const activity = useUserActivity();
  const alerts = useUserAlerts();

  return (
    <div>
      <PageHeader
        title="Dashboard"
        description="Your recent activity, active alerts, and platform-wide analytics."
      />

      {summary.isLoading && <LoadingState label="Loading dashboard analytics…" />}
      {summary.isError && <ErrorState error={summary.error} onRetry={() => summary.refetch()} />}

      {summary.data && (
        <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
          <Card>
            <SectionLabel>Trending Searches</SectionLabel>
            {summary.data.trendingSearches.length === 0 ? (
              <EmptyState title="No trending searches yet" />
            ) : (
              <ul className="flex flex-col gap-2">
                {summary.data.trendingSearches.map((s) => (
                  <li key={s.term} className="flex items-center justify-between text-sm">
                    <span className="text-ink">{s.term}</span>
                    <span className="text-ink-muted">{s.count}</span>
                  </li>
                ))}
              </ul>
            )}
          </Card>

          <Card>
            <SectionLabel>Frequently Accessed Documents</SectionLabel>
            {summary.data.frequentDocuments.length === 0 ? (
              <EmptyState title="No document activity yet" />
            ) : (
              <ul className="flex flex-col gap-2">
                {summary.data.frequentDocuments.map((doc) => (
                  <li key={doc.id} className="text-sm text-ink hover:underline">
                    {doc.title}
                  </li>
                ))}
              </ul>
            )}
          </Card>

          <Card className="lg:col-span-2">
            <SectionLabel>Department-wise Activity</SectionLabel>
            {summary.data.departmentActivity.length === 0 ? (
              <EmptyState title="No department activity yet" />
            ) : (
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={summary.data.departmentActivity}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--card-border)" />
                    <XAxis dataKey="departmentName" stroke="var(--ink-muted)" fontSize={12} />
                    <YAxis stroke="var(--ink-muted)" fontSize={12} />
                    <Tooltip
                      contentStyle={{
                        background: 'var(--card-bg)',
                        border: '1px solid var(--card-border)',
                        borderRadius: 8,
                      }}
                    />
                    <Bar dataKey="count" fill="var(--accent-gold)" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </Card>

          <Card>
            <SectionLabel>Corpus Health</SectionLabel>
            <div className="flex flex-col gap-2 text-sm text-ink">
              <div className="flex justify-between">
                <span>Avg. classification confidence</span>
                <span className="mono font-medium">
                  {(summary.data.corpusHealth.classificationConfidenceAvg * 100).toFixed(1)}%
                </span>
              </div>
              <div className="flex justify-between">
                <span>Avg. extraction confidence</span>
                <span className="mono font-medium">
                  {(summary.data.corpusHealth.extractionConfidenceAvg * 100).toFixed(1)}%
                </span>
              </div>
            </div>
          </Card>

          <Card>
            <SectionLabel>Active Alerts</SectionLabel>
            {alerts.isLoading && <LoadingState label="Loading alerts…" />}
            {alerts.isError && <ErrorState error={alerts.error} onRetry={() => alerts.refetch()} />}
            {alerts.data && alerts.data.length === 0 && <EmptyState title="No active alerts" />}
            {alerts.data && alerts.data.length > 0 && (
              <ul className="flex flex-col gap-3">
                {alerts.data.map((a) => (
                  <li key={a.id} className="flex items-start gap-2">
                    <SeverityPill severity={a.severity} />
                    <span className="text-sm text-ink">{a.title}</span>
                  </li>
                ))}
              </ul>
            )}
          </Card>

          <Card className="lg:col-span-2">
            <SectionLabel>Your Recent Activity</SectionLabel>
            {activity.isLoading && <LoadingState label="Loading activity…" />}
            {activity.isError && <ErrorState error={activity.error} onRetry={() => activity.refetch()} />}
            {activity.data && activity.data.length === 0 && <EmptyState title="No recent activity" />}
            {activity.data && activity.data.length > 0 && (
              <ul className="flex flex-col gap-2">
                {activity.data.map((item) => (
                  <li key={item.id} className="flex items-center justify-between text-sm">
                    <span className="text-ink">{item.description}</span>
                    <span className="text-xs text-ink-muted">{new Date(item.timestamp).toLocaleString()}</span>
                  </li>
                ))}
              </ul>
            )}
          </Card>
        </div>
      )}
    </div>
  );
}
