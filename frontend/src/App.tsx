import { createBrowserRouter, Navigate, RouterProvider } from 'react-router'

import { AppShell } from '@/components/layout/AppShell'
import { RedirectIfAuthed, RequireAuth } from '@/components/layout/RouteGuards'
import { LoginPage } from '@/features/auth/LoginPage'
import { RegisterPage } from '@/features/auth/RegisterPage'
import { JobDetailPage } from '@/features/jobs/JobDetailPage'
import { JobsPage } from '@/features/jobs/JobsPage'

const router = createBrowserRouter([
  {
    element: <RedirectIfAuthed />,
    children: [
      { path: '/login', element: <LoginPage /> },
      { path: '/register', element: <RegisterPage /> },
    ],
  },
  {
    element: <RequireAuth />,
    children: [
      {
        element: <AppShell />,
        children: [
          { index: true, element: <JobsPage /> },
          { path: 'jobs/:jobId', element: <JobDetailPage /> },
        ],
      },
    ],
  },
  { path: '*', element: <Navigate to="/" replace /> },
])

export function App() {
  return <RouterProvider router={router} />
}
