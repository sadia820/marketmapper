import { Loader2 } from 'lucide-react'

export function PageSpinner() {
  return (
    <div className="flex min-h-[40vh] items-center justify-center" aria-label="Loading">
      <Loader2 className="size-6 animate-spin text-slate-400" />
    </div>
  )
}
