/**
 * ModelCard tests: the FR-07 card contract (category, confidence, accuracy, latency),
 * the probability bars (FR-09) and the FR-14 error state.
 */
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import ModelCard from './ModelCard'

const result = {
  status: 'ok', category: 'High', confidence: 62.5,
  probabilities: { low: 0.1, medium: 0.275, high: 0.625 },
  accuracy: 63.1, latency_ms: 412.3,
}

describe('ModelCard', () => {
  it('renders the predicted category, confidence and test accuracy', () => {
    render(<ModelCard model="ml" result={result} />)
    expect(screen.getByText('Machine Learning')).toBeInTheDocument()
    expect(screen.getByText('predicted demand')).toBeInTheDocument()
    expect(screen.getByText('Test accuracy')).toBeInTheDocument()
    expect(screen.getByText('63.1%')).toBeInTheDocument()
    expect(screen.getByText('412.3 ms')).toBeInTheDocument()
    expect(screen.getByLabelText('confidence 62.5%')).toBeInTheDocument()
    expect(screen.getByText('63%')).toBeInTheDocument()             // the rounded value inside the ring
    // the category badge next to "predicted demand" shows High
    expect(screen.getByText('predicted demand').previousSibling).toHaveTextContent('High')
  })

  it('renders the three probabilities as percentages', () => {
    render(<ModelCard model="qml" result={result} />)
    expect(screen.getByText('10.0%')).toBeInTheDocument()      // Low
    expect(screen.getByText('27.5%')).toBeInTheDocument()      // Medium
    expect(screen.getByText('62.5%')).toBeInTheDocument()      // High
  })

  it('renders nothing at all before a result arrives', () => {
    const { container } = render(<ModelCard model="dl" result={null} loading={false} />)
    expect(container).toBeEmptyDOMElement()
  })

  it('shows a skeleton per card while the models are running', () => {
    const { container } = render(<ModelCard model="dl" result={null} loading />)
    expect(container.querySelector('.skeleton')).toBeInTheDocument()
  })

  it('shows an error card for a failed model and says the others are unaffected', () => {
    render(<ModelCard model="qml" result={{ status: 'error', code: 'SVC_TIMEOUT', message: 'Model service timed out' }} />)
    expect(screen.getByText('Timed out')).toBeInTheDocument()
    expect(screen.getByText(/The other models are unaffected/i)).toBeInTheDocument()
  })

  it('shows "Unavailable" for a service that is down rather than slow', () => {
    render(<ModelCard model="dl" result={{ status: 'error', code: 'SVC_UNAVAILABLE', message: 'Model service unavailable' }} />)
    expect(screen.getByText('Unavailable')).toBeInTheDocument()
  })
})
