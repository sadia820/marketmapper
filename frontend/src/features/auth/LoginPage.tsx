import { Link } from 'react-router'

import { Alert } from '@/components/ui/Alert'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { AuthLayout } from '@/features/auth/AuthLayout'
import { useAuthForm } from '@/features/auth/useAuthForm'
import { useAuth } from '@/lib/useAuth'

export function LoginPage() {
  const { login } = useAuth()
  const { error, submitting, onSubmit } = useAuthForm((form) =>
    login(String(form.get('email')), String(form.get('password'))),
  )

  return (
    <AuthLayout
      title="Sign in"
      subtitle="Welcome back to MarketMapper."
      footer={
        <>
          New to the team?{' '}
          <Link to="/register" className="font-medium text-brand-600 hover:text-brand-700">
            Create an account
          </Link>
        </>
      }
    >
      <form onSubmit={onSubmit} className="space-y-4">
        {error && <Alert>{error}</Alert>}
        <Input label="Email" name="email" type="email" autoComplete="email" required />
        <Input label="Password" name="password" type="password" autoComplete="current-password" required />
        <Button type="submit" className="w-full" loading={submitting}>
          Sign in
        </Button>
      </form>
    </AuthLayout>
  )
}
