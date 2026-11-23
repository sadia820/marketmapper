import { ArrowLeft, Download, Trash2 } from 'lucide-react'
import { useState } from 'react'
import { Link, useLocation, useNavigate, useParams } from 'react-router'

import { Alert } from '@/components/ui/Alert'
import { Button } from '@/components/ui/Button'
import { PageSpinner } from '@/components/ui/Spinner'
import { BusinessTable } from '@/features/jobs/BusinessTable'
import { JobProgressCard } from '@/features/jobs/JobProgressCard'
import { useBusinesses, useDeleteJob, useJob } from '@/features/jobs/queries'
import { api } from '@/lib/api'
import { formatDate } from '@/lib/format'

const PAGE_SIZE = 50

export function JobDetailPage() {
  const { jobId = '' } = useParams()
  const navigate = useNavigate()
  const ignoredColumns = (useLocation().state as { ignoredColumns?: string[] } | null)?.ignoredColumns
  const [page, setPage] = useState(0)
  const [exporting, setExporting] = useState(false)

  const { data: job, isLoading, error } = useJob(jobId)
  const businesses = useBusinesses(jobId, page, PAGE_SIZE, job)
  const deleteJob = useDeleteJob()

  if (isLoading) return <PageSpinner />
  if (error || !job) return <Alert>{error?.message ?? 'Upload not found'}</Alert>

  async function exportCsv() {
    setExporting(true)
    try {
      await api.download(`/jobs/${jobId}/export.csv`, `${job!.filename.replace(/\.[^.]+$/, '')}-results.csv`)
    } finally {
      setExporting(false)
    }
  }

  function remove() {
    if (!window.confirm(`Delete "${job!.filename}" and all its results?`)) return
    deleteJob.mutate(jobId, { onSuccess: () => navigate('/', { replace: true }) })
  }

  return (
    <div className="space-y-6">
      <Link to="/" className="inline-flex items-center gap-1 text-sm text-slate-500 hover:text-slate-900">
        <ArrowLeft className="size-4" aria-hidden />
        All uploads
      </Link>

      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0">
          <h1 className="truncate text-2xl font-semibold tracking-tight text-slate-900">{job.filename}</h1>
          <p className="mt-1 text-sm text-slate-500">
            Uploaded {formatDate(job.created_at)} by {job.owner.name}
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="danger" onClick={remove} loading={deleteJob.isPending}>
            <Trash2 className="size-4" aria-hidden />
            Delete
          </Button>
          <Button variant="secondary" onClick={exportCsv} loading={exporting} disabled={job.processed === 0}>
            <Download className="size-4" aria-hidden />
            Export CSV
          </Button>
        </div>
      </div>

      {!!ignoredColumns?.length && (
        <Alert tone="info">
          Ignored non-business columns: <strong>{ignoredColumns.join(', ')}</strong>. MarketMapper only uses
          business name, website, city, country and notes.
        </Alert>
      )}

      <JobProgressCard job={job} />

      {businesses.error ? (
        <Alert>{businesses.error.message}</Alert>
      ) : businesses.data ? (
        <BusinessTable
          businesses={businesses.data.items}
          total={businesses.data.total}
          page={page}
          pageSize={PAGE_SIZE}
          onPageChange={setPage}
        />
      ) : (
        <PageSpinner />
      )}
    </div>
  )
}
