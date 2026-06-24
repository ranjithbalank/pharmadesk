import axios from 'axios'

export const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
})

/** PUT multipart form data (e.g. settings with a logo file). Lets the browser
 * set Content-Type with the correct boundary — never set it by hand, or the
 * server can't parse the upload. */
export async function putForm<T = unknown>(url: string, fd: FormData) {
  return axios.put<T>('/api' + url, fd)
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

/** Money formatter — Indian rupee, the pharmacy's currency. */
export const inr = (n: number | string) =>
  '₹' + Number(n || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
