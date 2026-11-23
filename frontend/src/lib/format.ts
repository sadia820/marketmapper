const dateFormatter = new Intl.DateTimeFormat(undefined, {
  dateStyle: 'medium',
  timeStyle: 'short',
})

export function formatDate(iso: string): string {
  return dateFormatter.format(new Date(iso))
}

export function percent(part: number, total: number): number {
  return total === 0 ? 0 : Math.round((part / total) * 100)
}

export function hostname(url: string | null | undefined): string {
  if (!url) return ''
  try {
    return new URL(url.startsWith('http') ? url : `https://${url}`).hostname.replace(/^www\./, '')
  } catch {
    return url
  }
}
