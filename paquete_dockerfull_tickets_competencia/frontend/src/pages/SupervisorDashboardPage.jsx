import { useEffect, useState } from 'react'
import { useAuth } from '../state/AuthContext'
import { getCoverageApi } from '../services/api'

function BarChart({ data, labelKey, valueKey, color, maxName }) {
  const max = Math.max(...data.map((r) => r[valueKey]), 1)
  return (
    <div className="bar-chart">
      {data.map((r, i) => (
        <div className="bar-row" key={i}>
          <span className="bar-label" title={r[labelKey]}>{r[labelKey]}</span>
          <div className="bar-track">
            <div className={`bar-fill bar-fill-${color}`} style={{ width: `${(r[valueKey] / max) * 100}%` }} />
          </div>
          <span className="bar-count">{r[valueKey]}</span>
        </div>
      ))}
    </div>
  )
}

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
              <div className="section-title">Por Cadena</div>
              {data.byBusiness?.length ? (
                <BarChart data={data.byBusiness} labelKey="businessCode" valueKey="ticketCount" color="blue" />
              ) : <p className="muted">Sin datos</p>}
            </div>
            <div className="card">
              <div className="section-title">Por Status Documental</div>
              {data.byScanStatus ? (
                <BarChart
                  data={Object.entries(data.byScanStatus).map(([k, v]) => ({ status: k, count: v }))}
                  labelKey="status" valueKey="count" color="green" />
              ) : <p className="muted">Sin datos</p>}
            </div>
          </div>

          <div className="card mt-16">
            <div className="section-title">Por Tienda</div>
            {data.byStore?.length ? (
              <BarChart data={data.byStore} labelKey="storeCode" valueKey="ticketCount" color="amber" />
            ) : <p className="muted">Sin datos</p>}
          </div>
        </>
      )}
    </div>
  )
}
