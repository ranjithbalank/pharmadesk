import axios from 'axios'

const TOKEN_KEY = 'pharmadesk_token'
export const getToken = () => localStorage.getItem(TOKEN_KEY)
export const setToken = (t: string) => localStorage.setItem(TOKEN_KEY, t)
export const clearToken = () => localStorage.removeItem(TOKEN_KEY)

// "PharmaDesk" is the permanent product brand. The pharmacy's own name (the
// "medical name") is configured in Settings and shown alongside it, so the tab
// reads "PharmaDesk — <medical name>". Persisted so it's known before the
// authed settings load (no flash).
export const BRAND = 'PharmaDesk'
const SHOP_KEY = 'pharmadesk_shop'
export const getShopName = () => localStorage.getItem(SHOP_KEY) || ''
export const setShopName = (name: string) => {
  const n = (name || '').trim()
  if (!n) return
  localStorage.setItem(SHOP_KEY, n)
  document.title = `${BRAND} — ${n}`
}

// Same-origin '/api' in dev (Vite proxy) and in the packaged desktop app.
// On a split host (Vercel frontend → Render backend) set VITE_API_BASE_URL
// to the backend origin, e.g. https://pharmadesk-backend.onrender.com
export const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? '') + '/api'

export const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
})

// Attach the login token to every request.
api.interceptors.request.use((config) => {
  const token = getToken()
  if (token) config.headers.Authorization = `Token ${token}`
  return config
})

// A 401 means the token is missing/expired — drop it and bounce to login.
api.interceptors.response.use(
  (r) => r,
  (error) => {
    if (error?.response?.status === 401 && getToken()) {
      clearToken()
      window.location.reload()
    }
    return Promise.reject(error)
  },
)

/** PUT multipart form data (e.g. settings with a logo file). Lets the browser
 * set Content-Type with the correct boundary — never set it by hand, or the
 * server can't parse the upload. */
export async function putForm<T = unknown>(url: string, fd: FormData) {
  const token = getToken()
  return axios.put<T>(API_BASE + url, fd, {
    headers: token ? { Authorization: `Token ${token}` } : {},
  })
}

/** Trigger a browser download for a binary export endpoint (xlsx / pdf). */
export async function downloadFile(url: string, filename: string) {
  const res = await api.get(url, { responseType: 'blob' })
  const blob = new Blob([res.data])
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = filename
  link.click()
  URL.revokeObjectURL(link.href)
}

/** Open a binary endpoint (e.g. an invoice/PO PDF) inline in a new tab for
 * printing. Fetches it through the authenticated client — a plain <a href>
 * can't send the login token and, on a split host, points at the wrong origin.
 * Falls back to a download if the browser blocks the popup. */
export async function openFile(url: string, filename = 'document.pdf') {
  const res = await api.get(url, { responseType: 'blob' })
  const blobUrl = URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }))
  const win = window.open(blobUrl, '_blank')
  if (!win) {
    const link = document.createElement('a')
    link.href = blobUrl
    link.download = filename
    link.click()
  }
  setTimeout(() => URL.revokeObjectURL(blobUrl), 60_000)
}

/** Money formatter — Indian rupee, the pharmacy's currency. */
export const inr = (n: number | string) =>
  '₹' + Number(n || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
