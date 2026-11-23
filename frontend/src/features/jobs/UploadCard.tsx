import { clsx } from 'clsx'
import { FileSpreadsheet, UploadCloud } from 'lucide-react'
import { useRef, useState, type DragEvent } from 'react'
import { useNavigate } from 'react-router'

import { Alert } from '@/components/ui/Alert'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { useUploadJob } from '@/features/jobs/queries'

const ACCEPTED = '.csv,.xlsx'

export function UploadCard() {
  const navigate = useNavigate()
  const inputRef = useRef<HTMLInputElement>(null)
  const [dragging, setDragging] = useState(false)
  const upload = useUploadJob()

  function submit(file: File | undefined) {
    if (!file) return
    upload.mutate(file, {
      onSuccess: ({ job, ignored_columns }) =>
        navigate(`/jobs/${job.id}`, { state: { ignoredColumns: ignored_columns } }),
    })
  }

  function onDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault()
    setDragging(false)
    submit(event.dataTransfer.files[0])
  }

  return (
    <Card className="p-6">
      <div
        onDragOver={(e) => {
          e.preventDefault()
          setDragging(true)
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        className={clsx(
          'flex flex-col items-center rounded-lg border-2 border-dashed px-6 py-10 text-center transition-colors',
          dragging ? 'border-brand-500 bg-brand-50' : 'border-slate-300',
        )}
      >
        <UploadCloud className="size-10 text-slate-400" aria-hidden />
        <p className="mt-3 text-sm font-medium text-slate-900">Drop a CSV or Excel file here</p>
        <p className="mt-1 text-sm text-slate-500">
          Needs a <code className="rounded bg-slate-100 px-1">business_name</code> column. Add{' '}
          <code className="rounded bg-slate-100 px-1">website</code>, city and country for better results.
        </p>
        <Button className="mt-5" loading={upload.isPending} onClick={() => inputRef.current?.click()}>
          <FileSpreadsheet className="size-4" aria-hidden />
          Choose file
        </Button>
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED}
          className="sr-only"
          onChange={(e) => {
            submit(e.target.files?.[0])
            e.target.value = ''
          }}
        />
      </div>
      {upload.isError && (
        <div className="mt-4">
          <Alert>{upload.error.message}</Alert>
        </div>
      )}
    </Card>
  )
}
