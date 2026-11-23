import { clsx } from 'clsx'
import type { ReactNode } from 'react'

export type Tone = 'gray' | 'blue' | 'green' | 'amber' | 'red' | 'brand'

const tones: Record<Tone, string> = {
  gray: 'bg-slate-100 text-slate-700 ring-slate-500/20',
  blue: 'bg-sky-50 text-sky-700 ring-sky-600/20',
  green: 'bg-emerald-50 text-emerald-700 ring-emerald-600/20',
  amber: 'bg-amber-50 text-amber-800 ring-amber-600/20',
  red: 'bg-red-50 text-red-700 ring-red-600/20',
  brand: 'bg-brand-50 text-brand-700 ring-brand-600/20',
}

export function Badge({ tone = 'gray', children }: { tone?: Tone; children: ReactNode }) {
  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-xs font-medium whitespace-nowrap ring-1 ring-inset',
        tones[tone],
      )}
    >
      {children}
    </span>
  )
}
