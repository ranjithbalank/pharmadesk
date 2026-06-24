import { useEffect, useState } from 'react'
import { api, clearToken, getToken } from './lib/api'
import Login from './pages/Login'

type Status = 'checking' | 'in' | 'out'

/** Gates the whole app behind the single shared login (SEC-1). Validates any
 * saved token against the server before showing the app. */
export default function AuthGate({ children }: { children: React.ReactNode }) {
  const [status, setStatus] = useState<Status>(getToken() ? 'checking' : 'out')

  useEffect(() => {
    if (status !== 'checking') return
    api.get('/auth/me/')
      .then(() => setStatus('in'))
      .catch(() => { clearToken(); setStatus('out') })
  }, [status])

  if (status === 'checking') {
    return <div className="min-h-screen grid place-items-center text-muted text-sm">Loading…</div>
  }
  if (status === 'out') {
    return <Login onLoggedIn={() => setStatus('in')} />
  }
  return <>{children}</>
}
