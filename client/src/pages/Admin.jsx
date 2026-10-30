import { useCallback, useEffect, useState } from 'react'
import { api } from '../api'
import { useAuth } from '../auth'
import { MODELS } from '../meta'

export default function Admin() {
  const { user } = useAuth()
  const [health, setHealth] = useState(null)
  const [users, setUsers] = useState(null)
  const [audit, setAudit] = useState([])
  const [err, setErr] = useState('')
  const load = useCallback((refresh) => { api.health(refresh).then(setHealth).catch((e) => setErr(e.message)) }, [])
  useEffect(() => {
    load(true)
    api.users().then(setUsers).catch((e) => setErr(e.message))
    api.audit().then(setAudit).catch(() => {})
    const t = setInterval(() => load(false), 30000)      // FR-12: refresh every 30 s
    return () => clearInterval(t)
  }, [load])
  const toggle = async (u) => {
    try { await api.setActive(u.id, !u.is_active); setUsers(await api.users()); setAudit(await api.audit()) } catch (e) { setErr(e.message) }
  }
  return (
    <>
      <header className="page-h"><div><h1>Admin</h1><p className="muted">Service health, users and recent security events.</p></div><button className="ghost" onClick={() => load(true)}>Refresh health</button></header>
      {err && <div className="alert bad">{err}</div>}
      <div className="grid3">
        {MODELS.map((m) => {
          const h = health?.find((x) => x.service === m.key)
          return (
            <div key={m.key} className="card health"><span className={`pulse ${h ? h.status.toLowerCase() : ''}`} />
              <div><b>{m.name}</b><small className="muted">{h ? `${h.status} · checked ${new Date(h.checked_at).toLocaleTimeString()}` : 'checking...'}</small></div></div>
          )
        })}
      </div>
      <h2 className="sec">Users</h2>
      <div className="card table-wrap">
        {!users ? <div className="skeleton" style={{ height: 120 }} /> : (
          <table><thead><tr><th>User</th><th>Email</th><th>Role</th><th>Status</th><th /></tr></thead>
            <tbody>{users.map((u) => (
              <tr key={u.id}><td>{u.username}</td><td className="muted">{u.email}</td><td>{u.role}</td>
                <td><span className={`badge ${u.is_active ? 'low' : 'none'}`}><i />{u.is_active ? 'Active' : 'Disabled'}</span></td>
                <td className="r"><button className="ghost sm" disabled={u.username === user.username} onClick={() => toggle(u)}>{u.is_active ? 'Disable' : 'Enable'}</button></td></tr>
            ))}</tbody></table>
        )}
      </div>
      <h2 className="sec">Audit log</h2>
      <div className="card table-wrap">
        <table><thead><tr><th>Time</th><th>Action</th><th>User</th><th>IP</th><th>Outcome</th></tr></thead>
          <tbody>{audit.map((a) => <tr key={a.id}><td className="muted">{new Date(a.created_at).toLocaleString()}</td><td>{a.action}</td><td>{a.user_id ?? '-'}</td><td className="muted">{a.ip}</td><td>{a.outcome}</td></tr>)}</tbody></table>
      </div>
    </>
  )
}
