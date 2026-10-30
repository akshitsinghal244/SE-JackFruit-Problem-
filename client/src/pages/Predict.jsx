import { useMemo, useState } from 'react'
import { api } from '../api'
import Badge from '../components/Badge'
import ModelCard from '../components/ModelCard'
import { AccuracyChart, ProbChart } from '../components/Charts'
import { MODELS } from '../meta'

const today = () => new Date().toISOString().slice(0, 10)
const SAMPLE = { store: '3', item: '12', date: '2017-09-15', sales: ['41', '38', '45', '50', '47', '39', '44'] }
const isInt = (v) => /^\d+$/.test(String(v).trim())

function validate(f) {
  const e = { sales: [] }
  if (!isInt(f.store) || +f.store < 1 || +f.store > 10) e.store = 'Choose a store from 1 to 10'
  if (!isInt(f.item) || +f.item < 1 || +f.item > 50) e.item = 'Item must be a whole number from 1 to 50'
  if (!f.date || f.date < '2013-01-01' || f.date > '2030-12-31') e.date = 'Pick a date between 2013-01-01 and 2030-12-31'
  f.sales.forEach((s, i) => { if (!isInt(s) || +s > 500) e.sales[i] = '0-500' })
  const bad = e.store || e.item || e.date || e.sales.some(Boolean)
  return bad ? e : null
}

export default function Predict() {
  const [f, setF] = useState({ store: '', item: '', date: today(), sales: Array(7).fill('') })
  const [errs, setErrs] = useState(null)
  const [banner, setBanner] = useState('')
  const [busy, setBusy] = useState(false)
  const [res, setRes] = useState(null)

  const labels = useMemo(() => {
    const base = f.date ? new Date(f.date + 'T00:00:00') : new Date()
    return [7, 6, 5, 4, 3, 2, 1].map((k) => { const d = new Date(base); d.setDate(d.getDate() - k); return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' }) })
  }, [f.date])

  const setSale = (i, v) => setF({ ...f, sales: f.sales.map((x, j) => (j === i ? v : x)) })
  const submit = async (ev) => {
    ev.preventDefault(); setBanner('')
    const e = validate(f); setErrs(e)
    if (e) return
    setBusy(true); setRes(null)
    try {
      const data = await api.predict({ store_id: +f.store, item_id: +f.item, date: f.date, prev_sales: f.sales.map(Number) })
      setRes(data)
    } catch (x) {
      if (x.status === 422 && x.details.length) {
        const m = { sales: [] }
        x.details.forEach((d) => {
          if (d.field === 'store_id') m.store = d.reason
          else if (d.field === 'item_id') m.item = d.reason
          else if (d.field === 'date') m.date = d.reason
          else if (d.field.startsWith('prev_sales')) { const i = +d.field.split('.')[1]; Number.isInteger(i) ? (m.sales[i] = d.reason) : (m.salesAll = d.reason) }
        })
        setErrs(m)
      }
      setBanner(x.code === 'RATE_LIMITED' ? 'Too many requests - please wait a few seconds.' : x.message)
    } finally { setBusy(false) }
  }
  const sample = () => { setF(SAMPLE); setErrs(null) }

  const oks = res ? MODELS.filter((m) => res.results[m.key]?.status === 'ok') : []
  const agree = res && res.consensus !== 'No consensus' ? oks.filter((m) => res.results[m.key].category === res.consensus).length : 0
  const acc = res ? Object.fromEntries(oks.map((m) => [m.key, res.results[m.key].accuracy])) : {}

  return (
    <>
      <header className="page-h"><div><h1>Predict demand</h1><p className="muted">Enter an item&apos;s recent sales and see what each model expects for the target day.</p></div></header>

      <form className="card form" onSubmit={submit} noValidate>
        <div className="grid3">
          <label>Store
            <select value={f.store} onChange={(e) => setF({ ...f, store: e.target.value })} className={errs?.store ? 'bad' : ''}>
              <option value="">Select...</option>{Array.from({ length: 10 }, (_, i) => <option key={i} value={i + 1}>Store {i + 1}</option>)}
            </select>{errs?.store && <em className="fe">{errs.store}</em>}
          </label>
          <label>Item (1-50)
            <input inputMode="numeric" value={f.item} onChange={(e) => setF({ ...f, item: e.target.value })} placeholder="e.g. 12" className={errs?.item ? 'bad' : ''} />
            {errs?.item && <em className="fe">{errs.item}</em>}
          </label>
          <label>Target date
            <input type="date" min="2013-01-01" max="2030-12-31" value={f.date} onChange={(e) => setF({ ...f, date: e.target.value })} className={errs?.date ? 'bad' : ''} />
            {errs?.date && <em className="fe">{errs.date}</em>}
          </label>
        </div>

        <div className="sales-h"><span>Units sold in the previous 7 days <small className="muted">(oldest to newest - last box is the day before the target)</small></span></div>
        <div className="sales">
          {f.sales.map((v, i) => (
            <label key={i} className="sale"><small>{i === 6 ? 'Yesterday' : labels[i]}</small>
              <input inputMode="numeric" value={v} onChange={(e) => setSale(i, e.target.value)} placeholder="0" className={errs?.sales?.[i] ? 'bad' : ''} aria-label={`Sales ${labels[i]}`} />
              {errs?.sales?.[i] && <em className="fe">{errs.sales[i]}</em>}
            </label>
          ))}
        </div>
        {errs?.salesAll && <em className="fe">{errs.salesAll}</em>}
        {banner && <div className="alert bad" role="alert">{banner}</div>}
        <div className="actions">
          <button type="button" className="ghost" onClick={sample}>Use sample</button>
          <button className="primary" disabled={busy}>{busy ? <><span className="spinner sm" /> Running 3 models...</> : 'Predict demand'}</button>
        </div>
      </form>

      {(busy || res) && (
        <section className="results">
          {res && (
            <div className={`card consensus ${res.consensus === 'No consensus' ? 'none' : ''}`}>
              <div><small className="muted">Consensus (majority vote)</small>
                <div className="cons-row">{res.consensus === 'No consensus' ? <span className="badge none big">No consensus</span> : <Badge cat={res.consensus} big />}
                  <span className="muted">{res.consensus === 'No consensus' ? 'The models disagree - treat this prediction with caution.' : `${agree} of ${oks.length} models agree`}</span></div></div>
              <p className="hint"><b>How to read this:</b> High / Low means above / below what this item <i>usually</i> sells at this store - a restocking signal, not a ranking of best-sellers.</p>
            </div>
          )}
          <div className="grid3 models">
            {MODELS.map((m) => <ModelCard key={m.key} model={m.key} loading={busy} result={res?.results[m.key]} />)}
          </div>
          {res && <div className="grid2"><ProbChart results={res.results} /><AccuracyChart items={acc} /></div>}
          {res && <p className="served muted">Handled by web-server pod <code>{res.served_by}</code> · request <code>{res.request_id}</code></p>}
          {res && !res.history_saved && <div className="alert info">Prediction shown, but it could not be saved to your history.</div>}
        </section>
      )}
    </>
  )
}
