import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { LogIn } from 'lucide-react'
import { api, setToken } from '../lib/api'

export default function Login({ onLoggedIn }: { onLoggedIn: () => void }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [err, setErr] = useState('')

  const login = useMutation({
    mutationFn: async () =>
      (await api.post<{ token: string }>('/auth/login/', { username, password })).data,
    onSuccess: (d) => { setToken(d.token); onLoggedIn() },
    onError: () => setErr('Incorrect username or password.'),
  })

  return (
    <div className="min-h-screen grid place-items-center bg-canvas p-6">
      <div className="w-full max-w-sm">
        <div className="flex flex-col items-center mb-6">
          <div className="w-14 h-14 rounded-2xl bg-accent grid place-items-center text-white font-bold text-2xl shadow-lg shadow-accent/40 mb-3">
            ℞
          </div>
          <h1 className="text-[22px] font-bold tracking-tight">PharmaDesk</h1>
          <p className="text-[13px] text-muted">Sign in to continue</p>
        </div>

        <form
          className="card p-6 space-y-4"
          onSubmit={(e) => { e.preventDefault(); setErr(''); login.mutate() }}
        >
          <div>
            <label className="label">Username</label>
            <input className="input" autoFocus value={username}
              onChange={(e) => setUsername(e.target.value)} placeholder="admin" />
          </div>
          <div>
            <label className="label">Password</label>
            <input className="input" type="password" value={password}
              onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" />
          </div>
          {err && <p className="text-[12.5px] text-danger">{err}</p>}
          <button type="submit" disabled={!username || !password || login.isPending}
            className="btn-primary w-full justify-center py-2.5">
            <LogIn size={16} /> {login.isPending ? 'Signing in…' : 'Sign in'}
          </button>
        </form>

        <p className="text-center text-[11.5px] text-muted mt-4">
          Offline-first · single counter login. Change the password in Settings after first sign-in.
        </p>
      </div>
    </div>
  )
}
