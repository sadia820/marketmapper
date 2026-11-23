const TOKEN_KEY = 'mm_token'

export class ApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

export const tokenStore = {
  get: (): string | null => localStorage.getItem(TOKEN_KEY),
  set: (token: string) => localStorage.setItem(TOKEN_KEY, token),
  clear: () => localStorage.removeItem(TOKEN_KEY),
}

/** Fired when the API rejects our token, so the auth layer can sign the user out. */
export const UNAUTHORIZED_EVENT = 'mm:unauthorized'

async function errorMessage(res: Response): Promise<string> {
  try {
    const body = await res.json()
    if (typeof body.detail === 'string') return body.detail
    if (Array.isArray(body.detail)) return body.detail.map((d: { msg: string }) => d.msg).join(', ')
  } catch {
    /* response had no JSON body */
  }
  return `Request failed (${res.status})`
}

export async function request(path: string, init: RequestInit = {}): Promise<Response> {
  const headers = new Headers(init.headers)
  const token = tokenStore.get()
  if (token) headers.set('Authorization', `Bearer ${token}`)

  const res = await fetch(`/api${path}`, { ...init, headers })
  if (res.status === 401 && token) window.dispatchEvent(new Event(UNAUTHORIZED_EVENT))
  if (!res.ok) throw new ApiError(res.status, await errorMessage(res))
  return res
}

export const api = {
  get: async <T>(path: string): Promise<T> => (await request(path)).json(),

  postJson: async <T>(path: string, body: unknown): Promise<T> =>
    (
      await request(path, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
    ).json(),

  postForm: async <T>(path: string, body: FormData | URLSearchParams): Promise<T> =>
    (await request(path, { method: 'POST', body })).json(),

  delete: async (path: string): Promise<void> => {
    await request(path, { method: 'DELETE' })
  },

  download: async (path: string, filename: string): Promise<void> => {
    const blob = await (await request(path)).blob()
    const url = URL.createObjectURL(blob)
    const link = Object.assign(document.createElement('a'), { href: url, download: filename })
    link.click()
    URL.revokeObjectURL(url)
  },
}
