import type { InputHTMLAttributes } from 'react'
import { cn } from '@/lib/cn'

export function Input({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cn(
        'w-full rounded-md border border-ink-300 bg-white px-3 py-2 text-sm text-ink-900 placeholder:text-ink-500 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500',
        className,
      )}
      {...props}
    />
  )
}
