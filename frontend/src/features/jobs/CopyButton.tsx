import { Check, Copy } from 'lucide-react'
import { useState } from 'react'

import { Button } from '@/components/ui/Button'

export function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)

  async function copy() {
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  return (
    <Button variant="secondary" className="px-2.5 py-1 text-xs" onClick={copy}>
      {copied ? <Check className="size-3.5" aria-hidden /> : <Copy className="size-3.5" aria-hidden />}
      {copied ? 'Copied' : 'Copy'}
    </Button>
  )
}
