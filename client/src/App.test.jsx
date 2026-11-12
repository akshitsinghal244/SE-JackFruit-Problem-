/**
 * App routing tests: TC-15 (SEC-06) as seen by the user - a signed-in analyst gets no Admin
 * route, an admin does, and an anonymous visitor only ever sees login/register.
 */
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import App from './App'
import { api } from './api'
import { AuthProvider } from './auth'

vi.mock('./api', () => ({
  api: { me: vi.fn(), login: vi.fn(), logout: vi.fn(), predict: vi.fn(), history: vi.fn(), modelsInfo: vi.fn(), health: vi.fn(), users: vi.fn(), audit: vi.fn() },
  setToken: vi.fn(),
  getToken: vi.fn(() => ''),
  setUnauthorizedHandler: vi.fn(),
}))

const boot = (user) => render(
  <MemoryRouter initialEntries={['/predict']}>
    <AuthProvider>
      <App />
    </AuthProvider>
  </MemoryRouter>,
  user ? { value: { user, ready: true } } : {},
)

// AuthProvider is mocked below through the api layer, so we stub the context value directly.
vi.mock('./auth', async (orig) => {
  const actual = await orig()
  return { ...actual, useAuth: () => ({ user: globalThis.__rdcp_user, ready: true, login: vi.fn(), logout: vi.fn() }) }
})

beforeEach(() => {
  vi.clearAllMocks()
  globalThis.__rdcp_user = null
})

describe('access control in the UI', () => {
  it('sends an anonymous visitor to the login screen', async () => {
    api.me.mockRejectedValue(new Error('nope'))
    boot(null)
    await waitFor(() => expect(screen.getByRole('button', { name: /sign in|log in|register/i })).toBeInTheDocument())
  })

  it('shows the admin link only to an admin', async () => {
    globalThis.__rdcp_user = { username: 'ana', role: 'user', email: 'ana@x.com' }
    boot({})
    await waitFor(() => expect(screen.getByText('Predict')).toBeInTheDocument())
    expect(screen.queryByText('Admin')).not.toBeInTheDocument()
  })

  it('shows the admin link to an admin', async () => {
    globalThis.__rdcp_user = { username: 'admin', role: 'admin', email: 'admin@x.com' }
    boot({})
    await waitFor(() => expect(screen.getByText('Admin')).toBeInTheDocument())
  })
})
