import Badge from './Badge'
import { MODELS } from '../meta'

function Ring({ value, color }) {
  const r = 30, c = 2 * Math.PI * r
  return (
    <svg width="76" height="76" viewBox="0 0 76 76" className="ring" aria-label={`confidence ${value}%`}>
      <circle cx="38" cy="38" r={r} className="ring-bg" />
      <circle cx="38" cy="38" r={r} stroke={color} strokeDasharray={`${(value / 100) * c} ${c}`} className="ring-fg" transform="rotate(-90 38 38)" />
      <text x="38" y="43" textAnchor="middle" className="ring-t">{Math.round(value)}%</text>
    </svg>
  )
}

export default function ModelCard({ model, result, loading }) {
  const m = MODELS.find((x) => x.key === model)
  const head = (
    <div className="mc-head"><span className="dot" style={{ background: m.color }} /><div><b>{m.name}</b><small>{m.blurb}</small></div></div>
  )
  if (loading) return <div className="card mc">{head}<div className="skeleton" style={{ height: 150 }} /></div>
  if (!result) return null
  if (result.status !== 'ok') {
    return (
      <div className="card mc err">
        {head}
        <div className="mc-err"><span className="warn">!</span><div><b>{result.code === 'SVC_TIMEOUT' ? 'Timed out' : 'Unavailable'}</b><p>{result.message}. The other models are unaffected.</p></div></div>
      </div>
    )
  }
  const p = result.probabilities
  return (
    <div className="card mc" style={{ '--accent': m.color }}>
      {head}
      <div className="mc-main"><div><Badge cat={result.category} big /><small className="muted">predicted demand</small></div><Ring value={result.confidence} color={m.color} /></div>
      <div className="probs">
        {[['Low', p.low, 'low'], ['Medium', p.medium, 'med'], ['High', p.high, 'high']].map(([l, v, c]) => (
          <div key={l} className="prob"><span>{l}</span><div className="bar"><div className={`fill ${c}`} style={{ width: `${v * 100}%` }} /></div><em>{(v * 100).toFixed(1)}%</em></div>
        ))}
      </div>
      <div className="mc-foot"><span title="Accuracy on the held-out last 3 months">Test accuracy <b>{result.accuracy}%</b></span><span>{result.latency_ms} ms</span></div>
    </div>
  )
}
