import { useEffect, useState } from 'react'
import { useAuth } from '../state/AuthContext'
import { getHealth } from '../services/api'

export default function DashboardPage() {
  const { currentUser } = useAuth()
  const [health, setHealth] = useState('...')

  useEffect(() => {
    getHealth().then((r) => setHealth(r.data?.data?.status || 'unknown')).catch(() => setHealth('error'))
  }, [])

  return (
    <div className="page">
      <h1>Dashboard</h1>
      <div className="cards-grid">
        <div className="card"><div className="card-title">API</div><div className="card-value">{health}</div></div>
        <div className="card"><div className="card-title">Usuario</div><div className="card-value">{currentUser?.displayName || '-'}</div></div>
        <div className="card"><div className="card-title">Rol</div><div className="card-value">{currentUser?.roleCode || '-'}</div></div>
        <div className="card"><div className="card-title">Tiendas</div><div className="card-value">{(currentUser?.storeCodes || []).join(', ') || 'Global'}</div></div>
      </div>
      <div className="card mt-16">
        <div className="card-title">Sugerencia de uso</div>
        <p className="muted">Ve a Tickets para consultar el lote demo ya importado por el starter backend.</p>
      </div>
    </div>
  )
}
