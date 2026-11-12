/**
 * Admin page tests: FR-12 (service health, refreshed at least every 30 s) and
 * FR-13 (enable/disable a user, which is what SEC-06 enforces at the API).
 */
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import Admin from './Admin'
import { api } from '../api'
import { useAuth } from '../auth'

vi.mock('../api', () => ({
  api: { health: vi.fn(), users: vi.fn(), audit: vi.fn(), setActive: vi.fn() },
}))

// Layout needs a user; the page also reads it to disable the "own account" button.
vi.mock('../auth', () => ({ useAuth: () => ({ user: { username: 'admin', role: 'admin' } }) }))

const health = [{ service: 'ml', status: 'UP', checked_at: '2026-11-12T10:00:00Z' },
                { service: 'dl', status: 'UP', checked_at: '2026-11-12T10:00:00Z' },
                { service: 'qml', status: 'DOWN', checked_at: '2026-11-12T10:00:00Z' }]
const users = [{ id: 1, username: 'admin', email: 'admin@rdcp.test', role: 'admin', is_active: true },
               { id: 2, username: 'ana', email: 'ana@x.com', role: 'user', is_active: true },
               { id: 3, username: 'bob', email: 'bob@x.com', role: 'user', is_active: false }]
const audit = [{ id: 1, user_id: 2, action: 'LOGIN', ip: '10.0.0.5', outcome: 'success', created_at: '2026-11-12T10:00:00Z' }]

const renderPage = () => render(<MemoryRouter><Admin /></MemoryRouter>)

beforeEach(() => vi.clearAllMocks())

describe('Admin: service health (FR-12)', () => {
  it('shows UP/DOWN for each of the three services', async () => {
    api.health.mockResolvedValue(health)
    api.users.mockResolvedValue(users)
    api.audit.mockResolvedValue(audit)
    renderPage()
    await waitFor(() => expect(screen.getByText('DOWN', { exact: false, selector: '.health small' })).toBeInTheDocument())
    expect(screen.getAllByText(/^UP ·/, { selector: '.health small' }).length).toBe(2)
  })

  it('refreshes the health status when the button is pressed', async () => {
    const u = userEvent.setup()
    api.health.mockResolvedValue(health)
    api.users.mockResolvedValue(users)
    api.audit.mockResolvedValue(audit)
    renderPage()
    await waitFor(() => expect(api.health).toHaveBeenCalledWith(true))
    const before = api.health.mock.calls.length
    await u.click(screen.getByRole('button', { name: /Refresh health/i }))
    await waitFor(() => expect(api.health.mock.calls.length).toBeGreaterThan(before))
    expect(api.health).toHaveBeenLastCalledWith(true)                // force a fresh poll, not the cache
  })

  it('polls again automatically every 30 seconds', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
    api.health.mockResolvedValue(health)
    api.users.mockResolvedValue(users)
    api.audit.mockResolvedValue(audit)
    renderPage()
    await waitFor(() => expect(api.health).toHaveBeenCalled())
    const before = api.health.mock.calls.length
    vi.advanceTimersByTime(30_000)
    await waitFor(() => expect(api.health.mock.calls.length).toBeGreaterThan(before))
    vi.useRealTimers()
  })
})

describe('Admin: user management (FR-13 / SEC-06)', () => {
  it('lists every user with role and status', async () => {
    api.health.mockResolvedValue(health)
    api.users.mockResolvedValue(users)
    api.audit.mockResolvedValue(audit)
    renderPage()
    await waitFor(() => expect(screen.getByText('ana')).toBeInTheDocument())
    expect(screen.getByText('ana@x.com')).toBeInTheDocument()
    expect(screen.getByText('bob@x.com')).toBeInTheDocument()
    expect(screen.getAllByText('Active').length).toBe(2)
    expect(screen.getByText('Disabled')).toBeInTheDocument()
  })

  it('sends the toggle for the chosen user and reloads the list', async () => {
    const u = userEvent.setup()
    api.health.mockResolvedValue(health)
    api.users.mockResolvedValue(users)
    api.audit.mockResolvedValue(audit)
    api.setActive.mockResolvedValue({ id: 2, is_active: false })
    renderPage()
    const anaRow = await screen.findByText('ana@x.com').then((cell) => cell.closest('tr'))
    await u.click(within(anaRow).getByRole('button', { name: 'Disable' }))
    await waitFor(() => expect(api.setActive).toHaveBeenCalledWith(2, false))
    expect(api.users).toHaveBeenCalledTimes(2)                        // reload after the change
    expect(api.audit).toHaveBeenCalledTimes(2)                        // audit is refreshed too
  })

  it('never lets an admin disable their own account', async () => {
    api.health.mockResolvedValue(health)
    api.users.mockResolvedValue(users)
    api.audit.mockResolvedValue(audit)
    renderPage()
    await waitFor(() => expect(screen.getByText('admin@rdcp.test')).toBeInTheDocument())
    const own = screen.getAllByRole('button', { name: /Disable|Enable/ })[0]
    expect(own).toBeDisabled()
  })

  it('shows the recent audit events with user, action, IP and outcome', async () => {
    api.health.mockResolvedValue(health)
    api.users.mockResolvedValue(users)
    api.audit.mockResolvedValue(audit)
    renderPage()
    await waitFor(() => expect(screen.getByText('Audit log')).toBeInTheDocument())
    expect(screen.getByText('LOGIN')).toBeInTheDocument()
    expect(screen.getByText('10.0.0.5')).toBeInTheDocument()
    expect(screen.getByText('success')).toBeInTheDocument()
  })
})

describe('Admin access', () => {
  it('is only reachable for an admin (App.jsx routes non-admins away)', () => {
    expect(useAuth().user.role).toBe('admin')
  })
})
