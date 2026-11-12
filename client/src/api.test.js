/**
 * api.js unit tests: the uniform error body {error:{code,message,details}} (SADS 3.4),
 * bearer-token handling and the 401 -> sign-out hook that implements TC-15 A3.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError, api, setToken, setUnauthorizedHandler } from './api'

const ok = (body) => ({ ok: true, status: 200, json: async () => body, headers: new Map() })

beforeEach(() => {
  setToken('')
  localStorage.clear()
})

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('request handling', () => {
  it('sends the bearer token when one is stored', async () => {
    setToken('tok-123')
    const fetchMock = vi.fn().mockResolvedValue(ok({ id: 1 }))
    vi.stubGlobal('fetch', fetchMock)
    await api.me()
    const init = fetchMock.mock.calls[0][1]
    expect(init.headers.Authorization).toBe('Bearer tok-123')
  })

  it('maps the uniform error body onto ApiError with status, code, message and details', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: false, status: 422, json: async () => ({ error: { code: 'VALIDATION_ERROR', message: 'Invalid input', details: [{ field: 'store_id', reason: 'unknown store' }] } }),
    }))
    await expect(api.predict({})).rejects.toMatchObject({
      status: 422, code: 'VALIDATION_ERROR', message: 'Invalid input',
      details: [{ field: 'store_id', reason: 'unknown store' }],
    })
    expect(new ApiError(422, 'X', 'm', []) instanceof Error).toBe(true)
  })

  it('exposes a NETWORK error when the server cannot be reached', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('offline')))
    await expect(api.predict({})).rejects.toMatchObject({ status: 0, code: 'NETWORK' })
  })

  it('signs the user out on a 401 (expired or tampered token)', async () => {
    const onUnauthorized = vi.fn()
    setUnauthorizedHandler(onUnauthorized)
    setToken('expired')
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: false, status: 401, json: async () => ({ error: { code: 'TOKEN_EXPIRED', message: 'Session expired' } }),
    }))
    await expect(api.me()).rejects.toMatchObject({ code: 'TOKEN_EXPIRED' })
    expect(onUnauthorized).toHaveBeenCalledWith('TOKEN_EXPIRED')
    setUnauthorizedHandler(() => {})
  })

  it('keeps a login failure as a plain 401 and does not sign out', async () => {
    const onUnauthorized = vi.fn()
    setUnauthorizedHandler(onUnauthorized)
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: false, status: 401, json: async () => ({ error: { code: 'AUTH_INVALID', message: 'Invalid credentials' } }),
    }))
    await expect(api.login({ email: 'a@b.c', password: 'x' })).rejects.toMatchObject({ code: 'AUTH_INVALID' })
    expect(onUnauthorized).not.toHaveBeenCalled()
  })

  it('returns null for 204 No Content (logout)', async () => {
    setToken('t')
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, status: 204, json: async () => ({}) }))
    await expect(api.logout()).resolves.toBeNull()
  })
})

describe('endpoints (paths and methods)', () => {
  const cases = [
    ['register', '/auth/register', 'POST'],
    ['login', '/auth/login', 'POST'],
    ['logout', '/auth/logout', 'POST'],
    ['me', '/auth/me', 'GET'],
    ['predict', '/predict', 'POST'],
    ['modelsInfo', '/models/info', 'GET'],
    ['history', '/history?limit=50', 'GET'],
    ['health', '/admin/health', 'GET'],
    ['users', '/admin/users', 'GET'],
  ]

  it.each(cases)('%s calls the documented %s %s', async (name, path, method) => {
    const fetchMock = vi.fn().mockResolvedValue(ok(name === 'login' ? { access_token: 't' } : {}))
    vi.stubGlobal('fetch', fetchMock)
    if (name === 'health') await api.health()
    if (name === 'setActive') return
    await api[name]()
    expect(fetchMock.mock.calls[0][0]).toBe(`/api/v1${path}`)
    expect(fetchMock.mock.calls[0][1].method).toBe(method)
  })

  it('toggles a user with PATCH and the is_active body', async () => {
    const fetchMock = vi.fn().mockResolvedValue(ok({ id: 3, is_active: false }))
    vi.stubGlobal('fetch', fetchMock)
    await api.setActive(3, false)
    expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/admin/users/3')
    expect(fetchMock.mock.calls[0][1].method).toBe('PATCH')
    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({ is_active: false })
  })
})
