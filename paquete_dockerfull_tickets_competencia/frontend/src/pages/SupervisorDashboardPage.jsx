import { useEffect, useState } from 'react'
import { useAuth } from '../state/AuthContext'
import { getCoverageApi } from '../services/api'
import DataTable from '../ui/DataTable'
import StatusBadge from '../ui/StatusBadge'

export default function SupervisorDashboardPage() {
  const { currentUser } = useAuth()
  const [data, setData] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    getCoverageApi()
      .then((res) => setData(res.data?.data))
      .catch((err) => setError(err?.response?.data?.detail || 'Error al cargar cobertura'))
  }, [])

  if (!['ADMIN', 'SUPERVISOR'].includes(currentUser?.roleCode)) {
    return <div className="page"><p>No tiene permisos para este modulo.</p></div>
  }

  return (
    <div className="page">
      <h1>Cobertura de Tickets</h1>
      {error && <p className="error-text">{error}</p>}
      {!data && !error && <p className="muted">Cargando...</p>}
      {data && (
        <>
          <div className="cards-grid">
            <div className="card"><div className="card-title">Total Tickets</div><div className="card-value">{data.totalTickets}</div></div>
            <div className="card"><div className="card-title">Con Archivo</div><div className="card-value">{data.withFile}</div></div>
            <div className="card"><div className="card-title">Sin Archivo</div><div className="card-value">{data.withoutFile}</div></div>
            <div className="card"><div className="card-title">Confirmados</div><div className="card-value">{data.confirmed}</div></div>
          </div>

          <div className="grid two-cols mt-16">
            <div className="card">
              <div className="section-title">Por Estatus de Origen</div>
              <DataTable
                columns={[
                  { key: 'status', title: 'Estatus', render: (r) => <StatusBadge value={r.status} /> },
                  { key: 'count', title: 'Cantidad' },
                ]}
                rows={Object.entries(data.byStatus || {}).map(([k, v]) => ({ id: k, status: k, count: v }))}
                emptyMessage="Sin datos"
              />
            </div>
            <div className="card">
              <div className="section-title">Por Estatus Documental</div>
              <DataTable
                columns={[
                  { key: 'status', title: 'Estatus', render: (r) => <StatusBadge value={r.status} /> },
                  { key: 'count', title: 'Cantidad' },
                ]}
                rows={Object.entries(data.byScanStatus || {}).map(([k, v]) => ({ id: k, status: k, count: v }))}
                emptyMessage="Sin datos"
              />
            </div>
          </div>

          <div className="card mt-16">
            <div className="section-title">Por Tienda</div>
            <DataTable
              columns={[
                { key: 'storeCode', title: 'Tienda' },
                { key: 'ticketCount', title: 'Tickets' },
              ]}
              rows={data.byStore || []}
              emptyMessage="Sin tiendas"
            />
          </div>
        </>
      )}
    </div>
  )
}
