import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../state/AuthContext'

const USERS = [
  { value: 'admin', label: 'Administrador Demo (ADMIN)' },
  { value: 'supervisor', label: 'Supervisor Demo (SUPERVISOR)' },
  { value: 'store_a', label: 'Usuario Tienda A (STORE_USER)' },
  { value: 'store_b', label: 'Usuario Tienda B (STORE_USER)' },
]

export default function LoginPage() {
  const { currentUser, login } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    if (currentUser) navigate('/dashboard')
  }, [currentUser, navigate])

  const handleLogin = async (user) => {
    await login(user)
    navigate('/dashboard')
  }

  return (
    <div className="login-screen">
      <div className="login-card">
        <h1>Tickets Competencia</h1>
        <p className="muted">Starter Frontend Ejecutable</p>
        <div className="stack">
          {USERS.map((u) => (
            <button key={u.value} className="btn" onClick={() => handleLogin(u.value)}>{u.label}</button>
          ))}
        </div>
      </div>
    </div>
  )
}
