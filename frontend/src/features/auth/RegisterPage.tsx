import { Link } from 'react-router'

import { Alert } from '@/components/ui/Alert'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { AuthLayout } from '@/features/auth/AuthLayout'
import { useAuthForm } from '@/features/auth/useAuthForm'
import { useAuth } from '@/lib/useAuth'

export function RegisterPage() {
  const { register } = useAuth()
  const { error, submitting, onSubmit } = useAuthForm((form) =>
    register(String(form.get('name')), String(form.get('email')), String(form.get('password'))),
  )

  return (
    <AuthLayout
      title="Create your account"
      subtitle="Join your team's MarketMapper workspace."
      footer={
        <>
          Already have an account?{' '}
          <Link to="/login" className="font-medium text-brand-600 hover:text-brand-700">
            Sign in
          </Link>
        </>
      }
    >
      <form onSubmit={onSubmit} className="space-y-4">
        {error && <Alert>{error}</Alert>}
        <Input label="Full name" name="name" autoComplete="name" required />
        <Input label="Work email" name="email" type="email" autoComplete="email" required />
        <Input
          label="Password"
          name="password"
          type="password"
          autoComplete="new-password"
          minLength={8}
          placeholder="At least 8 characters"
          required
        />
        <Button type="submit" className="w-full" loading={submitting}>
          Create account
        </Button>
      </form>
    </AuthLayout>
  )
}
