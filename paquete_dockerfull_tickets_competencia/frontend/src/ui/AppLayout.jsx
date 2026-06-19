import { useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../state/AuthContext'
import ChangePasswordModal from './ChangePasswordModal'

export default function AppLayout() {
  const { currentUser, logout } = useAuth()
  const role = currentUser?.roleCode
  const [showPasswordModal, setShowPasswordModal] = useState(false)

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">Tickets Competencia</div>
        <nav className="nav-menu">
          <NavLink to="/dashboard">Dashboard</NavLink>
          <NavLink to="/tickets">Tickets</NavLink>
          {(role === 'ADMIN' || role === 'SUPERVISOR') && <NavLink to="/integration/batches">Lotes</NavLink>}
          {role === 'ADMIN' && <NavLink to="/admin/users">Usuarios</NavLink>}
        </nav>
      </aside>
      <main className="main-area">
        <header className="topbar">
          <div>
            <strong>{currentUser?.displayName}</strong> <span className="muted">({currentUser?.roleCode})</span>
          </div>
          <div className="row gap-8">
            <button className="btn btn-secondary btn-sm" onClick={() => setShowPasswordModal(true)}>Cambiar contraseña</button>
            <button className="btn btn-secondary" onClick={logout}>Salir</button>
          </div>
        </header>
        <section className="content-area">
          <Outlet />
        </section>
      </main>
      {showPasswordModal && <ChangePasswordModal onClose={() => setShowPasswordModal(false)} />}
    </div>
  )
}
