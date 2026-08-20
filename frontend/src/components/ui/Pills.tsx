import type { DocumentStatus } from '../../api/types';

// Mirrors backend/app/models/enums.py ImpactLevel — used by the (not yet
// wired) Change Radar view.
export type Severity = 'critical' | 'high' | 'medium' | 'low';

const statusLabel: Record<DocumentStatus, string> = {
  active: 'Active',
  amended: 'Amended',
  superseded: 'Superseded',
};

const statusClass: Record<DocumentStatus, string> = {
  active: 'text-status-active bg-status-active-bg',
  amended: 'text-status-amended bg-status-amended-bg',
  superseded: 'text-status-superseded bg-status-superseded-bg',
};

export function StatusPill({ status }: { status: DocumentStatus }) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-semibold ${statusClass[status]}`}
    >
      {statusLabel[status]}
    </span>
  );
}

const severityLabel: Record<Severity, string> = {
  critical: 'CRITICAL',
  high: 'HIGH',
  medium: 'MEDIUM',
  low: 'LOW',
};

const severityClass: Record<Severity, string> = {
  critical: 'text-severity-critical bg-severity-critical-bg',
  high: 'text-severity-high bg-severity-high-bg',
  medium: 'text-severity-medium bg-severity-medium-bg',
  low: 'text-severity-low bg-severity-low-bg',
};

export function SeverityPill({ severity }: { severity: Severity }) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-bold tracking-wide ${severityClass[severity]}`}
    >
      {severityLabel[severity]}
    </span>
  );
}
