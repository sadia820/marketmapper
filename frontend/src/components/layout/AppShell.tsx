import { LogOut } from 'lucide-react'
import { Link, Outlet } from 'react-router'

import { Logo } from '@/components/layout/Logo'
import { Button } from '@/components/ui/Button'
import { useAuth } from '@/lib/useAuth'

export function AppShell() {
  const { user, logout } = useAuth()

  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
          <Link to="/" aria-label="MarketMapper home">
            <Logo />
          </Link>
          <div className="flex items-center gap-3">
            <span className="hidden text-sm text-slate-600 sm:block">{user?.name}</span>
            <Button variant="ghost" onClick={logout}>
              <LogOut className="size-4" aria-hidden />
              Sign out
            </Button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
        <Outlet />
      </main>
    </div>
  )
}
