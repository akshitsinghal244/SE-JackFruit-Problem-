/**
 * Predict page tests: TC-04 (client-side validation blocks the request and shows field errors),
 * TC-03 (three model cards with category/confidence/accuracy) and TC-05 (consensus banner).
 */
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import Predict from './Predict'
import { api } from '../api'

vi.mock('../api', () => ({
  api: { predict: vi.fn() },
}))

const user = () => userEvent.setup()

const fill = async (u, { store = '3', item = '12', date = '2017-09-15', sales = [41, 38, 45, 50, 47, 39, 44] } = {}) => {
  await u.selectOptions(screen.getByLabelText('Store', { selector: 'label select' }), store)
  await u.clear(screen.getByLabelText(/^Item/))
  await u.type(screen.getByLabelText(/^Item/), item)
  const dateInput = screen.getByLabelText(/Target date/)
  await u.clear(dateInput)
  await u.type(dateInput, date)
  const boxes = screen.getAllByLabelText(/^Sales /)
  for (let i = 0; i < boxes.length; i++) {
    await u.clear(boxes[i])
    if (sales[i] !== undefined) await u.type(boxes[i], String(sales[i]))
  }
}

const results = (over = {}) => ({
  ml: { status: 'ok', category: 'Medium', confidence: 78.4, probabilities: { low: 0.12, medium: 0.784, high: 0.096 }, accuracy: 81.2, latency_ms: 3.1 },
  dl: { status: 'ok', category: 'Medium', confidence: 74.9, probabilities: { low: 0.2, medium: 0.749, high: 0.051 }, accuracy: 79.6, latency_ms: 40 },
  qml: { status: 'ok', category: 'High', confidence: 52.3, probabilities: { low: 0.3, medium: 0.177, high: 0.523 }, accuracy: 63.1, latency_ms: 380 },
  ...over,
})

const renderPage = () => render(<MemoryRouter><Predict /></MemoryRouter>)

beforeEach(() => {
  vi.clearAllMocks()
})

describe('TC-04: client-side validation', () => {
  it('blocks the request and shows field errors for out-of-range inputs', async () => {
    const u = user()
    renderPage()
    await fill(u, { store: '', item: '51', date: '2031-01-01', sales: [-1, 501, 'abc', 1, 1, 1, 1] })
    await u.click(screen.getByRole('button', { name: /Predict demand/i }))

    expect(api.predict).not.toHaveBeenCalled()                       // nothing is sent to the server
    expect(screen.getByText('Choose a store from 1 to 10')).toBeInTheDocument()
    expect(screen.getByText('Item must be a whole number from 1 to 50')).toBeInTheDocument()
    expect(screen.getByText('Pick a date between 2013-01-01 and 2030-12-31')).toBeInTheDocument()
    expect(screen.getAllByText('0-500').length).toBe(3)              // one per invalid sales box
  })

  it('rejects a non-numeric sales value and a missing sales value', async () => {
    const u = user()
    renderPage()
    await fill(u, { sales: ['x', undefined, 1, 1, 1, 1, 1] })
    await u.click(screen.getByRole('button', { name: /Predict demand/i }))
    expect(api.predict).not.toHaveBeenCalled()
    expect(screen.getAllByText('0-500').length).toBeGreaterThan(0)
  })

  it('accepts the boundaries 1/10, 1/50, 0/500 and 2013-01-01', async () => {
    const u = user()
    api.predict.mockResolvedValue({ id: 1, consensus: 'Medium', results: results(), history_saved: true })
    renderPage()
    await fill(u, { store: '10', item: '50', date: '2013-01-01', sales: [0, 500, 0, 500, 0, 500, 0] })
    await u.click(screen.getByRole('button', { name: /Predict demand/i }))
    await waitFor(() => expect(api.predict).toHaveBeenCalledTimes(1))
    expect(api.predict.mock.calls[0][0]).toEqual({
      store_id: 10, item_id: 50, date: '2013-01-01', prev_sales: [0, 500, 0, 500, 0, 500, 0],
    })
  })

  it('sends the 7 sales values in oldest-to-newest order', async () => {
    const u = user()
    api.predict.mockResolvedValue({ id: 2, consensus: 'Medium', results: results(), history_saved: true })
    renderPage()
    await fill(u)
    await u.click(screen.getByRole('button', { name: /Predict demand/i }))
    await waitFor(() => expect(api.predict).toHaveBeenCalled())
    expect(api.predict.mock.calls[0][0].prev_sales).toEqual([41, 38, 45, 50, 47, 39, 44])
  })

  it('maps a server 422 back onto the offending fields', async () => {
    const u = user()
    api.predict.mockRejectedValue({
      status: 422, code: 'VALIDATION_ERROR', message: 'Invalid input',
      details: [{ field: 'store_id', reason: 'unknown store' }, { field: 'item_id', reason: 'unknown item' }],
    })
    renderPage()
    await fill(u)
    await u.click(screen.getByRole('button', { name: /Predict demand/i }))
    await waitFor(() => expect(screen.getByText('unknown store')).toBeInTheDocument())
    expect(screen.getByText('unknown item')).toBeInTheDocument()
  })
})

describe('TC-03 / TC-07: the three model cards', () => {
  it('shows category, confidence and test accuracy for every model', async () => {
    const u = user()
    api.predict.mockResolvedValue({ id: 9, consensus: 'Medium', results: results(), history_saved: true })
    renderPage()
    await fill(u)
    await u.click(screen.getByRole('button', { name: /Predict demand/i }))

    await waitFor(() => expect(screen.getByText('Consensus (majority vote)')).toBeInTheDocument())
    expect(screen.getAllByText('Medium').length).toBeGreaterThan(0)
    expect(screen.getByText('78%')).toBeInTheDocument()               // confidence ring (rounded)
    expect(screen.getByText('81.2%')).toBeInTheDocument()             // ML test accuracy
    expect(screen.getByText('79.6%')).toBeInTheDocument()             // DL test accuracy
    expect(screen.getByText('63.1%')).toBeInTheDocument()             // QML test accuracy
    expect(screen.getByText(/3\.1 ms/)).toBeInTheDocument()           // latency
    expect(screen.getAllByText(/predicted demand/i).length).toBe(3)   // one card per model
  })

  it('explains what High/Low means (restocking signal, not best-seller ranking)', async () => {
    const u = user()
    api.predict.mockResolvedValue({ id: 9, consensus: 'Medium', results: results(), history_saved: true })
    renderPage()
    await fill(u)
    await u.click(screen.getByRole('button', { name: /Predict demand/i }))
    await waitFor(() => expect(screen.getByText(/restocking signal/i)).toBeInTheDocument())
  })

  it('names the gateway pod and the request id', async () => {
    const u = user()
    api.predict.mockResolvedValue({ id: 9, consensus: 'Medium', results: results(), history_saved: true, served_by: 'gateway-7', request_id: 'abc123' })
    renderPage()
    await fill(u)
    await u.click(screen.getByRole('button', { name: /Predict demand/i }))
    await waitFor(() => expect(screen.getByText('gateway-7')).toBeInTheDocument())
    expect(screen.getByText('abc123')).toBeInTheDocument()
  })
})

describe('TC-05: consensus banner', () => {
  it('shows the majority category when 2 of 3 models agree', async () => {
    const u = user()
    api.predict.mockResolvedValue({ id: 9, consensus: 'Medium', results: results(), history_saved: true })
    renderPage()
    await fill(u)
    await u.click(screen.getByRole('button', { name: /Predict demand/i }))
    await waitFor(() => expect(screen.getByText('2 of 3 models agree')).toBeInTheDocument())
  })

  it('shows No consensus when all three disagree', async () => {
    const u = user()
    api.predict.mockResolvedValue({
      id: 9, consensus: 'No consensus', history_saved: true,
      results: results({
        ml: { status: 'ok', category: 'Low', confidence: 40, probabilities: { low: 0.4, medium: 0.3, high: 0.3 }, accuracy: 81.2, latency_ms: 3 },
        dl: { status: 'ok', category: 'Medium', confidence: 40, probabilities: { low: 0.3, medium: 0.4, high: 0.3 }, accuracy: 79.6, latency_ms: 40 },
      }),
    })
    renderPage()
    await fill(u)
    await u.click(screen.getByRole('button', { name: /Predict demand/i }))
    await waitFor(() => expect(screen.getByText('No consensus')).toBeInTheDocument())
    expect(screen.getByText(/The models disagree/i)).toBeInTheDocument()
  })

  it('counts only the models that answered when one failed', async () => {
    const u = user()
    api.predict.mockResolvedValue({
      id: 9, consensus: 'Medium', history_saved: true,
      results: results({ qml: { status: 'error', code: 'SVC_TIMEOUT', message: 'Model service timed out' } }),
    })
    renderPage()
    await fill(u)
    await u.click(screen.getByRole('button', { name: /Predict demand/i }))
    await waitFor(() => expect(screen.getByText('2 of 2 models agree')).toBeInTheDocument())
  })
})

describe('TC-14 / FR-14 in the UI', () => {
  it('shows an error card for the failed model while the others still render', async () => {
    const u = user()
    api.predict.mockResolvedValue({
      id: 9, consensus: 'Medium', history_saved: true,
      results: results({ qml: { status: 'error', code: 'SVC_UNAVAILABLE', message: 'Model service unavailable' } }),
    })
    renderPage()
    await fill(u)
    await u.click(screen.getByRole('button', { name: /Predict demand/i }))
    await waitFor(() => expect(screen.getByText('Unavailable')).toBeInTheDocument())
    expect(screen.getByText(/The other models are unaffected/i)).toBeInTheDocument()
    expect(screen.getByText('81.2%')).toBeInTheDocument()
  })

  it('warns when the prediction could not be saved to history', async () => {
    const u = user()
    api.predict.mockResolvedValue({ id: null, consensus: 'Medium', results: results(), history_saved: false })
    renderPage()
    await fill(u)
    await u.click(screen.getByRole('button', { name: /Predict demand/i }))
    await waitFor(() => expect(screen.getByText(/could not be saved to your history/i)).toBeInTheDocument())
  })
})

describe('rate limiting (SEC-07)', () => {
  it('shows a friendly message instead of the raw 429', async () => {
    const u = user()
    api.predict.mockRejectedValue({ status: 429, code: 'RATE_LIMITED', message: 'Too many requests' })
    renderPage()
    await fill(u)
    await u.click(screen.getByRole('button', { name: /Predict demand/i }))
    await waitFor(() => expect(screen.getByText(/Too many requests - please wait/i)).toBeInTheDocument())
  })
})
