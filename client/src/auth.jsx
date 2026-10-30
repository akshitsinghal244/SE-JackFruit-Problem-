import { createContext, useContext, useEffect, useState, useCallback } from 'react'
import { api, setToken, getToken, setUnauthorizedHandler } from './api'

const Ctx = createContext(null)
export const useAuth = () => useContext(Ctx)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [ready, setReady] = useState(false)
  const [notice, setNotice] = useState('')

  const clear = useCallback((code) => {
    setToken(''); setUser(null)
    if (code === 'TOKEN_EXPIRED') setNotice('Your session expired. Please sign in again.')
  }, [])

  useEffect(() => {
    setUnauthorizedHandler(clear)
    if (!getToken()) { setReady(true); return }
    api.me().then(setUser).catch(() => setToken('')).finally(() => setReady(true))
  }, [clear])

  const login = async (email, password) => {
    const r = await api.login({ email, password })
    setToken(r.access_token); setNotice('')
    setUser({ username: r.username, role: r.role })
  }
  const logout = async () => { try { await api.logout() } catch { /* ignore */ } clear() }

  return <Ctx.Provider value={{ user, ready, login, logout, notice, setNotice }}>{children}</Ctx.Provider>
}
