import { useEffect, useState } from 'react'
import { api } from '../api'
import Badge from '../components/Badge'
import { MODELS } from '../meta'

export default function History() {
  const [rows, setRows] = useState(null)
  const [err, setErr] = useState('')
  useEffect(() => { api.history().then(setRows).catch((e) => setErr(e.message)) }, [])
  return (
    <>
      <header className="page-h"><div><h1>History</h1><p className="muted">Your latest 50 predictions.</p></div>
        <button className="ghost" disabled={!rows?.length} onClick={() => api.exportCsv().catch((e) => setErr(e.message))}>Export CSV</button></header>
      {err && <div className="alert bad">{err}</div>}
      <div className="card table-wrap">
        {!rows ? <div className="skeleton" style={{ height: 200 }} /> : rows.length === 0 ? <div className="empty"><b>No predictions yet</b><p className="muted">Run one on the Predict page and it will show up here.</p></div> : (
          <table>
            <thead><tr><th>When</th><th>Store</th><th>Item</th><th>Date</th>{MODELS.map((m) => <th key={m.key}>{m.short}</th>)}<th>Consensus</th></tr></thead>
            <tbody>{rows.map((r) => (
              <tr key={r.id}><td className="muted">{new Date(r.created_at).toLocaleString()}</td><td>{r.store_id}</td><td>{r.item_id}</td><td>{r.date}</td>
                {MODELS.map((m) => <td key={m.key}>{r.results[m.key]?.status === 'ok' ? <Badge cat={r.results[m.key].category} /> : <span className="badge none">error</span>}</td>)}
                <td>{r.consensus === 'No consensus' ? <span className="badge none">none</span> : <Badge cat={r.consensus} />}</td></tr>
            ))}</tbody>
          </table>
        )}
      </div>
    </>
  )
}
