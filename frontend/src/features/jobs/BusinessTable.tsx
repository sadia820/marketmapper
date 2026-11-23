import { clsx } from 'clsx'
import { ChevronDown, ExternalLink } from 'lucide-react'
import { Fragment, useState } from 'react'

import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { BusinessDetails } from '@/features/jobs/BusinessDetails'
import { BusinessStatusBadge, PriorityBadge } from '@/features/jobs/StatusBadges'
import { hostname } from '@/lib/format'
import type { Business } from '@/lib/types'

interface BusinessTableProps {
  businesses: Business[]
  total: number
  page: number
  pageSize: number
  onPageChange: (page: number) => void
}

const COLUMNS = ['Business', 'Industry', 'Top offer', 'Priority', 'Status']

export function BusinessTable({ businesses, total, page, pageSize, onPageChange }: BusinessTableProps) {
  const [openId, setOpenId] = useState<number | null>(null)
  const pageCount = Math.max(1, Math.ceil(total / pageSize))

  return (
    <Card className="overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-50 text-left text-xs font-medium text-slate-500">
            <tr>
              {COLUMNS.map((col) => (
                <th key={col} scope="col" className="px-4 py-3 whitespace-nowrap">
                  {col}
                </th>
              ))}
              <th scope="col" className="w-10" />
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {businesses.map((b) => {
              const open = openId === b.id
              const url = b.final_url || b.website
              return (
                <Fragment key={b.id}>
                  <tr
                    onClick={() => setOpenId(open ? null : b.id)}
                    className={clsx('cursor-pointer transition-colors hover:bg-slate-50', open && 'bg-slate-50')}
                    aria-expanded={open}
                  >
                    <td className="px-4 py-3">
                      <p className="font-medium text-slate-900">{b.business_name}</p>
                      {url ? (
                        <a
                          href={url.startsWith('http') ? url : `https://${url}`}
                          target="_blank"
                          rel="noreferrer"
                          onClick={(e) => e.stopPropagation()}
                          className="inline-flex items-center gap-1 text-xs text-slate-500 hover:text-brand-600"
                        >
                          {hostname(url)}
                          <ExternalLink className="size-3" aria-hidden />
                        </a>
                      ) : (
                        <p className="text-xs text-slate-400">No website</p>
                      )}
                    </td>
                    <td className="px-4 py-3 text-slate-700">{b.industry || '—'}</td>
                    <td className="px-4 py-3">
                      {b.offers?.[0] ? (
                        <Badge tone="brand">{b.offers[0].name.split(' (')[0]}</Badge>
                      ) : (
                        <span className="text-slate-400">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <PriorityBadge priority={b.priority} />
                    </td>
                    <td className="px-4 py-3">
                      <BusinessStatusBadge status={b.status} />
                    </td>
                    <td className="px-3 py-3 text-slate-400">
                      <ChevronDown className={clsx('size-4 transition-transform', open && 'rotate-180')} aria-hidden />
                    </td>
                  </tr>
                  {open && (
                    <tr className="bg-slate-50">
                      <td colSpan={COLUMNS.length + 1} className="px-4 pt-1 pb-6">
                        <BusinessDetails business={b} />
                      </td>
                    </tr>
                  )}
                </Fragment>
              )
            })}
          </tbody>
        </table>
      </div>
      {pageCount > 1 && (
        <div className="flex items-center justify-between border-t border-slate-100 px-4 py-3 text-sm text-slate-600">
          <span>
            Page {page + 1} of {pageCount} · {total} businesses
          </span>
          <div className="flex gap-2">
            <Button variant="secondary" disabled={page === 0} onClick={() => onPageChange(page - 1)}>
              Previous
            </Button>
            <Button variant="secondary" disabled={page + 1 >= pageCount} onClick={() => onPageChange(page + 1)}>
              Next
            </Button>
          </div>
        </div>
      )}
    </Card>
  )
}
