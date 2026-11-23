import type { ReactNode } from 'react'

import { Logo } from '@/components/layout/Logo'
import { Card } from '@/components/ui/Card'

interface AuthLayoutProps {
  title: string
  subtitle: string
  children: ReactNode
  footer: ReactNode
}

export function AuthLayout({ title, subtitle, children, footer }: AuthLayoutProps) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center px-4 py-12">
      <Logo />
      <Card className="mt-8 w-full max-w-sm p-8">
        <h1 className="text-xl font-semibold text-slate-900">{title}</h1>
        <p className="mt-1 text-sm text-slate-500">{subtitle}</p>
        <div className="mt-6">{children}</div>
      </Card>
      <p className="mt-6 text-sm text-slate-500">{footer}</p>
    </div>
  )
}
