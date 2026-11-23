import type { LucideIcon } from 'lucide-react'
import type { ReactNode } from 'react'

interface EmptyStateProps {
  icon: LucideIcon
  title: string
  children?: ReactNode
}

export function EmptyState({ icon: Icon, title, children }: EmptyStateProps) {
  return (
    <div className="px-6 py-12 text-center">
      <Icon className="mx-auto size-10 text-slate-300" aria-hidden />
      <h3 className="mt-3 text-sm font-semibold text-slate-900">{title}</h3>
      {children && <div className="mt-1 text-sm text-slate-500">{children}</div>}
    </div>
  )
}
