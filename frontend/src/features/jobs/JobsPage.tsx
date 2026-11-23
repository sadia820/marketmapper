import { JobList } from '@/features/jobs/JobList'
import { UploadCard } from '@/features/jobs/UploadCard'

export function JobsPage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900">Research uploads</h1>
        <p className="mt-1 text-sm text-slate-500">
          Upload a list of businesses. MarketMapper reads each company's website and recommends TxLabz offers.
        </p>
      </div>
      <UploadCard />
      <section className="space-y-3">
        <h2 className="text-sm font-semibold text-slate-900">Recent uploads</h2>
        <JobList />
      </section>
    </div>
  )
}
