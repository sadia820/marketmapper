import { Navigate, Outlet, useLocation } from 'react-router'

import { PageSpinner } from '@/components/ui/Spinner'
import { useAuth } from '@/lib/useAuth'

/** Only signed-in users may pass. */
export function RequireAuth() {
  const { user, isLoading } = useAuth()
  const location = useLocation()
  if (isLoading) return <PageSpinner />
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />
  return <Outlet />
}

/** Signed-in users are sent to the app instead of login/register. */
export function RedirectIfAuthed() {
  const { user, isLoading } = useAuth()
  if (isLoading) return <PageSpinner />
  if (user) return <Navigate to="/" replace />
  return <Outlet />
}
