import { clsx } from 'clsx'

type Variant = 'default' | 'success' | 'warning' | 'error' | 'demo' | 'info'

const variants: Record<Variant, string> = {
  default: 'bg-gray-100 text-gray-800',
  success: 'bg-green-100 text-green-800',
  warning: 'bg-yellow-100 text-yellow-800',
  error: 'bg-red-100 text-red-800',
  demo: 'bg-amber-100 text-amber-800 border border-amber-400 font-bold',
  info: 'bg-blue-100 text-blue-800',
}

interface BadgeProps {
  children: React.ReactNode
  variant?: Variant
  className?: string
}

export function Badge({ children, variant = 'default', className }: BadgeProps) {
  return (
    <span className={clsx('inline-flex items-center px-2 py-0.5 rounded text-xs font-medium', variants[variant], className)}>
      {children}
    </span>
  )
}

export function StatusBadge({ status }: { status: string }) {
  const map: Record<string, Variant> = {
    pending: 'default',
    queued: 'info',
    running: 'warning',
    completed: 'success',
    failed: 'error',
    cancelled: 'default',
  }
  return <Badge variant={map[status] || 'default'}>{status}</Badge>
}
