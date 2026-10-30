// Thin fetch wrapper for the RDCP web server (/api/v1). Errors use the uniform body {error:{code,message,details}}.
const BASE = '/api/v1'
let token = localStorage.getItem('rdcp_token') || ''
let onUnauthorized = () => {}

export const setToken = (t) => { token = t || ''; t ? localStorage.setItem('rdcp_token', t) : localStorage.removeItem('rdcp_token') }
export const getToken = () => token
export const setUnauthorizedHandler = (fn) => { onUnauthorized = fn }

export class ApiError extends Error {
  constructor(status, code, message, details = []) { super(message); this.status = status; this.code = code; this.details = details }
}

async function request(path, { method = 'GET', body, raw = false } = {}) {
  let res
  try {
    res = await fetch(BASE + path, {
      method,
      headers: { ...(body ? { 'Content-Type': 'application/json' } : {}), ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      body: body ? JSON.stringify(body) : undefined,
    })
  } catch {
    throw new ApiError(0, 'NETWORK', 'Cannot reach the server. Check your connection.')
  }
  if (raw && res.ok) return res
  if (res.status === 204) return null
  let data = null
  try { data = await res.json() } catch { /* empty body */ }
  if (!res.ok) {
    const e = data?.error || {}
    if (res.status === 401 && token && path !== '/auth/login') onUnauthorized(e.code)
    throw new ApiError(res.status, e.code || 'ERROR', e.message || 'Something went wrong', e.details || [])
  }
  return data
}

export const api = {
  register: (b) => request('/auth/register', { method: 'POST', body: b }),
  login: (b) => request('/auth/login', { method: 'POST', body: b }),
  logout: () => request('/auth/logout', { method: 'POST' }),
  me: () => request('/auth/me'),
  predict: (b) => request('/predict', { method: 'POST', body: b }),
  modelsInfo: () => request('/models/info'),
  history: () => request('/history?limit=50'),
  exportCsv: async () => {
    const res = await request('/history/export', { raw: true })
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = Object.assign(document.createElement('a'), { href: url, download: 'rdcp_history.csv' })
    a.click(); URL.revokeObjectURL(url)
  },
  health: (refresh) => request(`/admin/health${refresh ? '?refresh=true' : ''}`),
  users: () => request('/admin/users'),
  setActive: (id, is_active) => request(`/admin/users/${id}`, { method: 'PATCH', body: { is_active } }),
  audit: () => request('/admin/audit?limit=15'),
}
