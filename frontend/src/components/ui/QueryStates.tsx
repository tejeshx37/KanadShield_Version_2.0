import type { ReactNode } from 'react';
import { ApiError } from '../../api/client';

export function LoadingState({ label = 'Loading…' }: { label?: string }) {
  return (
    <div role="status" className="flex items-center gap-3 py-10 text-ink-muted">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-card-border border-t-accent-gold" />
      <span>{label}</span>
    </div>
  );
}

export function ErrorState({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  const message =
    error instanceof ApiError
      ? error.message
      : error instanceof Error
        ? error.message
        : 'Something went wrong while contacting the backend.';

  return (
    <div
      role="alert"
      className="rounded-[--radius-token] border border-severity-critical-bg bg-severity-critical-bg px-5 py-4 text-severity-critical"
    >
      <p className="font-semibold">Couldn't load this data</p>
      <p className="mt-1 text-sm">{message}</p>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="mt-3 rounded-[--radius-token] border border-severity-critical px-3 py-1.5 text-sm font-medium"
        >
          Retry
        </button>
      )}
    </div>
  );
}

export function EmptyState({ title, description }: { title: string; description?: string }) {
  return (
    <div className="rounded-[--radius-token] border border-dashed border-card-border bg-card-bg px-6 py-12 text-center">
      <p className="font-semibold text-ink">{title}</p>
      {description && <p className="mt-1 text-sm text-ink-muted">{description}</p>}
    </div>
  );
}

export function NotYetImplemented({ title, description }: { title: string; description: ReactNode }) {
  return (
    <div className="rounded-[--radius-token] border border-card-border bg-card-bg px-6 py-12 text-center">
      <p className="font-serif text-xl font-bold text-ink">{title}</p>
      <div className="mx-auto mt-2 max-w-md text-sm text-ink-muted">{description}</div>
      <span className="mt-4 inline-block rounded-full bg-accent-gold-soft px-3 py-1 text-xs font-semibold text-accent-gold">
        Not yet implemented
      </span>
    </div>
  );
}
