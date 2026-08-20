import { cn } from '@/lib/cn'

const JURISDICTION_STYLES: Record<string, string> = {
  CENTRAL: 'bg-authority-central/10 text-authority-central',
  STATE: 'bg-authority-state/10 text-authority-state',
}

export function Badge({ children, className, tone }: { children: React.ReactNode; className?: string; tone?: string }) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium',
        tone ? JURISDICTION_STYLES[tone] ?? 'bg-ink-100 text-ink-700' : 'bg-ink-100 text-ink-700',
        className,
      )}
    >
      {children}
    </span>
  )
}
