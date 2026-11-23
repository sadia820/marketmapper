import { ChevronRight, Inbox } from 'lucide-react'
import { Link } from 'react-router'

import { Card } from '@/components/ui/Card'
import { EmptyState } from '@/components/ui/EmptyState'
import { ProgressBar } from '@/components/ui/ProgressBar'
import { PageSpinner } from '@/components/ui/Spinner'
import { Alert } from '@/components/ui/Alert'
import { useJobs } from '@/features/jobs/queries'
import { JobStatusBadge } from '@/features/jobs/StatusBadges'
import { formatDate, percent } from '@/lib/format'

export function JobList() {
  const { data: jobs, isLoading, error } = useJobs()

  if (isLoading) return <PageSpinner />
  if (error) return <Alert>{error.message}</Alert>

  return (
    <Card>
      {!jobs?.length ? (
        <EmptyState icon={Inbox} title="No uploads yet">
          Upload your first list above to start researching.
        </EmptyState>
      ) : (
        <ul className="divide-y divide-slate-100">
          {jobs.map((job) => (
            <li key={job.id}>
              <Link
                to={`/jobs/${job.id}`}
                className="flex items-center gap-4 px-5 py-4 transition-colors hover:bg-slate-50"
              >
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-3">
                    <p className="truncate text-sm font-medium text-slate-900">{job.filename}</p>
                    <JobStatusBadge status={job.status} />
                  </div>
                  <p className="mt-1 text-xs text-slate-500">
                    {formatDate(job.created_at)} · {job.owner.name} · {job.total} businesses
                  </p>
                </div>
                <div className="hidden w-40 sm:block">
                  <ProgressBar value={percent(job.processed, job.total)} label={`${job.filename} progress`} />
                  <p className="mt-1 text-right text-xs text-slate-500">
                    {job.processed}/{job.total}
                  </p>
                </div>
                <ChevronRight className="size-4 text-slate-400" aria-hidden />
              </Link>
            </li>
          ))}
        </ul>
      )}
    </Card>
  )
}
