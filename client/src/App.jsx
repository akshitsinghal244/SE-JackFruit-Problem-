import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from './auth'
import Layout from './components/Layout'
import Login from './pages/Login'
import Predict from './pages/Predict'
import History from './pages/History'
import Models from './pages/Models'
import Admin from './pages/Admin'

export default function App() {
  const { user, ready } = useAuth()
  if (!ready) return <div className="splash"><div className="spinner" /></div>
  if (!user) return (
    <Routes>
      <Route path="/register" element={<Login mode="register" />} />
      <Route path="/login" element={<Login mode="login" />} />
      <Route path="*" element={<Login mode="login" />} />
    </Routes>
  )
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Navigate to="/predict" replace />} />
        <Route path="/predict" element={<Predict />} />
        <Route path="/history" element={<History />} />
        <Route path="/models" element={<Models />} />
        <Route path="/admin" element={user.role === 'admin' ? <Admin /> : <Navigate to="/" />} />
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </Layout>
  )
}
