import { Card } from '@/components/ui/Card'
import { ProgressBar } from '@/components/ui/ProgressBar'
import { isActive } from '@/features/jobs/queries'
import { JobStatusBadge } from '@/features/jobs/StatusBadges'
import { percent } from '@/lib/format'
import type { Job } from '@/lib/types'

function Stat({ label, value }: { label: string; value: number | string }) {
  return (
    <div>
      <dt className="text-xs font-medium text-slate-500">{label}</dt>
      <dd className="mt-1 text-2xl font-semibold tracking-tight text-slate-900">{value}</dd>
    </div>
  )
}

export function JobProgressCard({ job }: { job: Job }) {
  const pct = percent(job.processed, job.total)
  return (
    <Card className="p-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h2 className="text-sm font-semibold text-slate-900">Progress</h2>
          <JobStatusBadge status={job.status} />
        </div>
        <span className="text-sm font-medium text-slate-700">{pct}%</span>
      </div>
      <div className="mt-4">
        <ProgressBar value={pct} label="Research progress" />
      </div>
      {isActive(job) && (
        <p className="mt-2 text-xs text-slate-500">Researching websites… this page updates automatically.</p>
      )}
      <dl className="mt-6 grid grid-cols-3 gap-4">
        <Stat label="Businesses" value={job.total} />
        <Stat label="Researched" value={job.processed - job.failed_count} />
        <Stat label="Failed" value={job.failed_count} />
      </dl>
    </Card>
  )
}
