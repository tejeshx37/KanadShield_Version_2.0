import type { ButtonHTMLAttributes } from 'react'
import { cn } from '@/lib/cn'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'outline'
  size?: 'sm' | 'md'
}

const variantClasses: Record<NonNullable<ButtonProps['variant']>, string> = {
  primary: 'bg-brand-700 text-white hover:bg-brand-600 disabled:bg-ink-300',
  secondary: 'bg-ink-100 text-ink-900 hover:bg-ink-300',
  ghost: 'bg-transparent text-ink-700 hover:bg-ink-100',
  outline: 'border border-ink-300 text-ink-900 hover:bg-ink-100 bg-white',
}

export function Button({ variant = 'primary', size = 'md', className, ...props }: ButtonProps) {
  return (
    <button
      className={cn(
        'inline-flex items-center justify-center gap-2 rounded-md font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-60',
        size === 'sm' ? 'px-3 py-1.5 text-sm' : 'px-4 py-2 text-sm',
        variantClasses[variant],
        className,
      )}
      {...props}
    />
  )
}
