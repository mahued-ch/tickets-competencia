import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { listScanTicketsApi } from '../services/api'
import StatusBadge from '../ui/StatusBadge'

export default function ScanTicketsPage() {
  const [tickets, setTickets] = useState([])
  const [meta, setMeta] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    listScanTicketsApi({ pageSize: 50 })
      .then((res) => {
        setTickets(res.data?.data || [])
        setMeta(res.data?.meta || null)
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="page">
      <div className="page-header">
        <h1>Tickets por Escaneo</h1>
        <Link to="/scan-tickets/new" className="btn btn-success">Nuevo escaneo</Link>
      </div>

      {loading ? (
        <p>Cargando...</p>
      ) : tickets.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: 40 }}>
          <p>No hay tickets creados por escaneo.</p>
          <p className="muted">Crea uno nuevo para comenzar.</p>
        </div>
      ) : (
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Código</th>
                <th>Competidor</th>
                <th>Tienda</th>
                <th>Fecha</th>
                <th>Status Scan</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {tickets.map((t) => (
                <tr key={t.ticketId}>
                  <td>{t.ticketId}</td>
                  <td>{t.sourceTicketCode}</td>
                  <td>{t.sourceBusinessCode}</td>
                  <td>{t.sourceStoreCode}</td>
                  <td>{t.sourceTicketDate}</td>
                  <td><StatusBadge value={t.scanStatus} /></td>
                  <td>
                    <Link to={`/scan-tickets/${t.ticketId}`} className="btn btn-sm">Editar</Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {meta && (
        <p className="muted mt-16">
          Página {meta.page} de {meta.totalPages} ({meta.totalRecords} registros)
        </p>
      )}
    </div>
  )
}
