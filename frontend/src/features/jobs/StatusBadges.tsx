import { Loader2 } from 'lucide-react'

import { Badge, type Tone } from '@/components/ui/Badge'
import type { BusinessStatus, JobStatus, Level } from '@/lib/types'

const jobTones: Record<JobStatus, Tone> = { queued: 'gray', running: 'blue', completed: 'green', failed: 'red' }
const businessTones: Record<BusinessStatus, Tone> = {
  pending: 'gray',
  researching: 'blue',
  done: 'green',
  failed: 'red',
}
const priorityTones: Record<Level, Tone> = { high: 'red', medium: 'amber', low: 'gray' }

const capitalize = (s: string) => s.charAt(0).toUpperCase() + s.slice(1)

export function JobStatusBadge({ status }: { status: JobStatus }) {
  return (
    <Badge tone={jobTones[status]}>
      {status === 'running' && <Loader2 className="size-3 animate-spin" aria-hidden />}
      {capitalize(status)}
    </Badge>
  )
}

export function BusinessStatusBadge({ status }: { status: BusinessStatus }) {
  return (
    <Badge tone={businessTones[status]}>
      {status === 'researching' && <Loader2 className="size-3 animate-spin" aria-hidden />}
      {capitalize(status)}
    </Badge>
  )
}

export function PriorityBadge({ priority }: { priority: Level | null }) {
  if (!priority) return <span className="text-slate-400">—</span>
  return <Badge tone={priorityTones[priority]}>{capitalize(priority)}</Badge>
}
