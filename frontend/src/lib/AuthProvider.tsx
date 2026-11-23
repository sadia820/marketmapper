import { useQueryClient } from '@tanstack/react-query'
import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'

import { api, tokenStore, UNAUTHORIZED_EVENT } from '@/lib/api'
import { AuthContext, type AuthContextValue } from '@/lib/auth-context'
import type { AuthResponse, User } from '@/lib/types'

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(() => Boolean(tokenStore.get()))

  const logout = useCallback(() => {
    tokenStore.clear()
    setUser(null)
    queryClient.clear()
  }, [queryClient])

  // Restore the session on first load.
  useEffect(() => {
    if (!tokenStore.get()) return
    api
      .get<User>('/auth/me')
      .then(setUser)
      .catch(logout)
      .finally(() => setIsLoading(false))
  }, [logout])

  useEffect(() => {
    window.addEventListener(UNAUTHORIZED_EVENT, logout)
    return () => window.removeEventListener(UNAUTHORIZED_EVENT, logout)
  }, [logout])

  const startSession = useCallback((res: AuthResponse) => {
    tokenStore.set(res.access_token)
    setUser(res.user)
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isLoading,
      logout,
      login: async (email, password) => {
        const form = new URLSearchParams({ username: email, password })
        startSession(await api.postForm<AuthResponse>('/auth/login', form))
      },
      register: async (name, email, password) => {
        startSession(await api.postJson<AuthResponse>('/auth/register', { name, email, password }))
      },
    }),
    [user, isLoading, logout, startSession],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
