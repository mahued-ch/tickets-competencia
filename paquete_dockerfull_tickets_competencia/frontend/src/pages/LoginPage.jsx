import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../state/AuthContext'

export default function LoginPage() {
  const { currentUser, login, loading, error } = useAuth()
  const navigate = useNavigate()
  const [loginName, setLoginName] = useState('')
  const [password, setPassword] = useState('')

  useEffect(() => {
    if (currentUser) navigate('/dashboard')
  }, [currentUser, navigate])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!loginName || !password) return
    const ok = await login(loginName, password)
    if (ok) navigate('/dashboard')
  }

  return (
    <div className="login-screen">
      <div className="login-card">
        <h1>Tickets Competencia</h1>
        <p className="muted">Ingrese sus credenciales</p>
        <form onSubmit={handleSubmit} className="stack">
          <input
            type="text"
            placeholder="Usuario"
            value={loginName}
            onChange={(e) => setLoginName(e.target.value)}
            disabled={loading}
            autoFocus
          />
          <input
            type="password"
            placeholder="Contraseña"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            disabled={loading}
          />
          {error && <p className="error-msg">{error}</p>}
          <button type="submit" className="btn" disabled={loading || !loginName || !password}>
            {loading ? 'Ingresando...' : 'Ingresar'}
          </button>
        </form>
        <p className="muted mt-16" style={{ fontSize: '0.8rem' }}>
          Usuarios demo: admin, supervisor, store_a, store_b<br />
          Contraseña: demo123
        </p>
      </div>
    </div>
  )
}
