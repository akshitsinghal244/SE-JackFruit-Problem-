import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../api'
import { useAuth } from '../auth'

export default function Login({ mode }) {
  const reg = mode === 'register'
  const { login, notice } = useAuth()
  const nav = useNavigate()
  const [f, setF] = useState({ username: '', email: '', password: '' })
  const [err, setErr] = useState('')
  const [fields, setFields] = useState({})
  const [busy, setBusy] = useState(false)
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value })

  const submit = async (e) => {
    e.preventDefault(); setErr(''); setFields({}); setBusy(true)
    try {
      if (reg) { await api.register(f); await login(f.email, f.password); nav('/predict') } else await login(f.email, f.password)
    } catch (x) {
      setErr(x.message)
      const m = {}; (x.details || []).forEach((d) => { m[d.field] = d.reason }); setFields(m)
    } finally { setBusy(false) }
  }
  return (
    <div className="auth">
      <section className="auth-art">
        <div className="brand"><span className="logo">R</span><div><b>RDCP</b><small>Retail Demand Category Predictor</small></div></div>
        <h1>Will it sell <span className="grad">more than usual?</span></h1>
        <p>Enter a store, an item, a date and the last 7 days of sales. Three independent models - classical ML, deep learning and quantum ML - predict Low, Medium or High demand, side by side.</p>
        <ul>
          <li><span className="dot" style={{ background: '#38bdf8' }} />Machine Learning<small>Random Forest / XGBoost</small></li>
          <li><span className="dot" style={{ background: '#a78bfa' }} />Deep Learning<small>LSTM</small></li>
          <li><span className="dot" style={{ background: '#f472b6' }} />Quantum ML<small>Variational circuit</small></li>
        </ul>
      </section>
      <section className="auth-form">
        <form className="card" onSubmit={submit} noValidate>
          <h2>{reg ? 'Create your account' : 'Welcome back'}</h2>
          <p className="muted">{reg ? 'Takes 10 seconds.' : 'Sign in to run predictions.'}</p>
          {notice && !reg && <div className="alert info">{notice}</div>}
          {err && <div className="alert bad" role="alert">{err}</div>}
          {reg && <label>Username<input value={f.username} onChange={set('username')} autoComplete="username" required />{fields.username && <em className="fe">{fields.username}</em>}</label>}
          <label>Email<input type="email" value={f.email} onChange={set('email')} autoComplete="email" required />{fields.email && <em className="fe">{fields.email}</em>}</label>
          <label>Password<input type="password" value={f.password} onChange={set('password')} autoComplete={reg ? 'new-password' : 'current-password'} required />
            {reg && <small className="muted">8+ characters, at least 1 digit and 1 uppercase letter</small>}{fields.password && <em className="fe">{fields.password}</em>}</label>
          <button className="primary" disabled={busy}>{busy ? 'Please wait...' : reg ? 'Create account' : 'Sign in'}</button>
          <p className="switch">{reg ? <>Already registered? <Link to="/login">Sign in</Link></> : <>New here? <Link to="/register">Create an account</Link></>}</p>
        </form>
      </section>
    </div>
  )
}
