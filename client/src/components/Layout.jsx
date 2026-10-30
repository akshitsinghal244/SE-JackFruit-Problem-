import { NavLink } from 'react-router-dom'
import { useAuth } from '../auth'

const Icon = ({ d }) => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d={d} /></svg>
)
const ICONS = {
  predict: 'M3 17l6-6 4 4 8-8M14 7h7v7',
  history: 'M3 12a9 9 0 1 0 3-6.7L3 8M3 3v5h5M12 7v5l3 2',
  models: 'M12 2l9 5-9 5-9-5 9-5zM3 12l9 5 9-5M3 17l9 5 9-5',
  admin: 'M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6l8-3zM9 12l2 2 4-4',
  sun: 'M12 4V2M12 22v-2M4 12H2M22 12h-2M5.6 5.6L4.2 4.2M19.8 19.8l-1.4-1.4M5.6 18.4l-1.4 1.4M19.8 4.2l-1.4 1.4M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8z',
  moon: 'M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z',
  out: 'M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9',
}

export default function Layout({ children }) {
  const { user, logout } = useAuth()
  const toggle = () => {
    const next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark'
    document.documentElement.dataset.theme = next
    localStorage.setItem('rdcp_theme', next)
  }
  const links = [['/predict', 'Predict', 'predict'], ['/history', 'History', 'history'], ['/models', 'Models', 'models'], ...(user.role === 'admin' ? [['/admin', 'Admin', 'admin']] : [])]
  return (
    <div className="shell">
      <aside className="side">
        <div className="brand"><span className="logo">R</span><div><b>RDCP</b><small>Demand Predictor</small></div></div>
        <nav>
          {links.map(([to, label, ic]) => (
            <NavLink key={to} to={to} end className={({ isActive }) => 'nav' + (isActive ? ' on' : '')}><Icon d={ICONS[ic]} /><span>{label}</span></NavLink>
          ))}
        </nav>
        <div className="side-foot">
          <div className="me"><span className="avatar">{user.username[0].toUpperCase()}</span><div><b>{user.username}</b><small>{user.role}</small></div></div>
          <div className="row">
            <button className="ghost icon" onClick={toggle} title="Toggle theme" aria-label="Toggle theme"><span className="show-dark"><Icon d={ICONS.sun} /></span><span className="show-light"><Icon d={ICONS.moon} /></span></button>
            <button className="ghost icon" onClick={logout} title="Sign out" aria-label="Sign out"><Icon d={ICONS.out} /></button>
          </div>
        </div>
      </aside>
      <main className="main">{children}</main>
    </div>
  )
}
