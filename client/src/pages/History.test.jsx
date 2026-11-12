/**
 * History page tests: FR-10 (latest 50 predictions, newest first, own records only)
 * and FR-11 (CSV export of those records).
 */
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import History from './History'
import { api } from '../api'

vi.mock('../api', () => ({ api: { history: vi.fn(), exportCsv: vi.fn() } }))

const rows = [
  { id: 2, store_id: 4, item_id: 7, date: '2017-10-02', prev_sales: [1, 2, 3, 4, 5, 6, 7],
    results: { ml: { status: 'ok', category: 'Low' }, dl: { status: 'ok', category: 'Low' }, qml: { status: 'error' } },
    consensus: 'Low', created_at: '2017-10-03T09:00:00Z' },
  { id: 1, store_id: 3, item_id: 12, date: '2017-09-15', prev_sales: [41, 38, 45, 50, 47, 39, 44],
    results: { ml: { status: 'ok', category: 'Medium' }, dl: { status: 'ok', category: 'Medium' }, qml: { status: 'ok', category: 'High' } },
    consensus: 'Medium', created_at: '2017-09-16T08:00:00Z' },
]

const renderPage = () => render(<MemoryRouter><History /></MemoryRouter>)

beforeEach(() => vi.clearAllMocks())

describe('History', () => {
  it('lists the stored predictions newest first', async () => {
    api.history.mockResolvedValue(rows)
    renderPage()
    await waitFor(() => expect(screen.getByRole('table')).toBeInTheDocument())
    const body = screen.getAllByRole('row').slice(1)                 // skip the header row
    expect(body).toHaveLength(2)
    expect(body[0]).toHaveTextContent('4')                           // newest first: store 4
    expect(body[0]).toHaveTextContent('2017-10-02')
    expect(body[1]).toHaveTextContent('3')                           // then store 3
    expect(body[1]).toHaveTextContent('2017-09-15')
  })

  it('shows the consensus of each row', async () => {
    api.history.mockResolvedValue(rows)
    renderPage()
    await waitFor(() => expect(screen.getAllByText('Medium').length).toBeGreaterThan(0))
    expect(screen.getAllByText('Low').length).toBeGreaterThan(0)
    expect(screen.getByRole('button', { name: /Export CSV/i })).toBeEnabled()
  })

  it('shows an empty state instead of an empty table', async () => {
    api.history.mockResolvedValue([])
    renderPage()
    await waitFor(() => expect(screen.getByText('No predictions yet')).toBeInTheDocument())
    expect(screen.getByRole('button', { name: /Export CSV/i })).toBeDisabled()
  })

  it('marks a model that failed as an error in the row', async () => {
    api.history.mockResolvedValue([rows[0]])
    renderPage()
    await waitFor(() => expect(screen.getAllByText('Low').length).toBe(3))   // ml, dl and the consensus
    expect(screen.getAllByText('error').length).toBe(1)                      // the QML cell
  })

  it('calls the export endpoint when Export CSV is pressed', async () => {
    const u = userEvent.setup()
    api.history.mockResolvedValue(rows)
    api.exportCsv.mockResolvedValue(undefined)
    renderPage()
    await waitFor(() => expect(screen.getByRole('button', { name: /Export CSV/i })).toBeEnabled())
    await u.click(screen.getByRole('button', { name: /Export CSV/i }))
    expect(api.exportCsv).toHaveBeenCalledTimes(1)
  })

  it('shows the server error message when history cannot be loaded', async () => {
    api.history.mockRejectedValue(new Error('Session expired'))
    renderPage()
    await waitFor(() => expect(screen.getByText('Session expired')).toBeInTheDocument())
  })
})
