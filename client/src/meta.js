export const MODELS = [
  { key: 'ml', name: 'Machine Learning', short: 'ML', color: '#38bdf8', blurb: 'Random Forest / XGBoost' },
  { key: 'dl', name: 'Deep Learning', short: 'DL', color: '#a78bfa', blurb: 'LSTM / MLP' },
  { key: 'qml', name: 'Quantum ML', short: 'QML', color: '#f472b6', blurb: 'Variational quantum classifier' },
]
export const CAT_CLASS = { Low: 'low', Medium: 'med', High: 'high' }
export const fmtDate = (d) => new Date(d + 'T00:00:00').toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
