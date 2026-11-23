import { useState, type FormEvent } from 'react'
import { useLocation, useNavigate } from 'react-router'

/** Shared submit/loading/error handling for the login and register forms. */
export function useAuthForm(action: (form: FormData) => Promise<void>) {
  const navigate = useNavigate()
  const location = useLocation()
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await action(new FormData(event.currentTarget))
      const from = (location.state as { from?: string } | null)?.from
      navigate(from ?? '/', { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
    } finally {
      setSubmitting(false)
    }
  }

  return { error, submitting, onSubmit }
}
