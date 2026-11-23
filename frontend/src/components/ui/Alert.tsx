import { clsx } from 'clsx'
import { AlertCircle, Info } from 'lucide-react'
import type { ReactNode } from 'react'

export function Alert({ tone = 'error', children }: { tone?: 'error' | 'info'; children: ReactNode }) {
  const Icon = tone === 'error' ? AlertCircle : Info
  return (
    <div
      role={tone === 'error' ? 'alert' : 'status'}
      className={clsx(
        'flex gap-2 rounded-lg px-3 py-2.5 text-sm',
        tone === 'error' ? 'bg-red-50 text-red-700' : 'bg-sky-50 text-sky-800',
      )}
    >
      <Icon className="mt-0.5 size-4 shrink-0" aria-hidden />
      <div>{children}</div>
    </div>
  )
}
