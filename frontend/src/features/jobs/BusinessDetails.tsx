import type { ReactNode } from 'react'

import { Badge } from '@/components/ui/Badge'
import { CopyButton } from '@/features/jobs/CopyButton'
import type { Business } from '@/lib/types'

function Section({ title, action, children }: { title: string; action?: ReactNode; children: ReactNode }) {
  return (
    <section>
      <div className="flex items-center justify-between">
        <h4 className="text-xs font-semibold tracking-wide text-slate-500 uppercase">{title}</h4>
        {action}
      </div>
      <div className="mt-2 text-sm text-slate-700">{children}</div>
    </section>
  )
}

export function BusinessDetails({ business: b }: { business: Business }) {
  if (b.status === 'failed') {
    return <p className="text-sm text-red-600">Research failed: {b.error ?? 'unknown error'}</p>
  }
  if (b.status !== 'done') {
    return <p className="text-sm text-slate-500">Results will appear here once research finishes.</p>
  }

  return (
    <div className="grid gap-6 md:grid-cols-2">
      <div className="space-y-5">
        <Section title="Summary">
          <p>{b.summary || 'No summary available.'}</p>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {b.size_estimate && b.size_estimate !== 'unknown' && <Badge>Size: {b.size_estimate}</Badge>}
            {b.confidence && <Badge>Confidence: {b.confidence}</Badge>}
            {b.mode && <Badge>{b.mode === 'ai' ? 'AI analysis' : 'Rule-based'}</Badge>}
          </div>
        </Section>
        {!!b.services?.length && (
          <Section title="Services">
            <p>{b.services.join(' · ')}</p>
          </Section>
        )}
        <Section title="Gaps found">
          {b.gaps?.length ? (
            <ul className="list-disc space-y-1 pl-4">
              {b.gaps.map((gap) => (
                <li key={gap}>{gap}</li>
              ))}
            </ul>
          ) : (
            <p className="text-slate-500">No obvious gaps found.</p>
          )}
        </Section>
      </div>
      <div className="space-y-5">
        <Section title="Recommended offers">
          {b.offers?.length ? (
            <ol className="space-y-2">
              {b.offers.map((offer, i) => (
                <li key={offer.id} className="rounded-lg bg-white p-3 ring-1 ring-slate-200">
                  <p className="font-medium text-slate-900">
                    {i + 1}. {offer.name}
                  </p>
                  {offer.reason && <p className="mt-0.5 text-xs text-slate-500">{offer.reason}</p>}
                </li>
              ))}
            </ol>
          ) : (
            <p className="text-slate-500">No matching offers.</p>
          )}
        </Section>
        {b.outreach_angle && (
          <Section title="Outreach angle" action={<CopyButton text={b.outreach_angle} />}>
            <p className="rounded-lg bg-brand-50 p-3 text-brand-900">{b.outreach_angle}</p>
          </Section>
        )}
      </div>
    </div>
  )
}
