import { useEffect, useState } from 'react'
import { useAuth } from '../state/AuthContext'
import { searchAuditEventsApi } from '../services/api'
import DataTable from '../ui/DataTable'
import StatusBadge from '../ui/StatusBadge'

export default function AuditPage() {
  const { currentUser } = useAuth()
  const [rows, setRows] = useState([])
  const [meta, setMeta] = useState(null)
  const [error, setError] = useState('')
  const [filters, setFilters] = useState({ eventType: '', entityName: '', sourceTicketKey: '' })
  const [page, setPage] = useState(1)

  function fetchData(p = page) {
    const params = { page: p, pageSize: 50 }
    if (filters.eventType) params.eventType = filters.eventType
    if (filters.entityName) params.entityName = filters.entityName
    if (filters.sourceTicketKey) params.sourceTicketKey = filters.sourceTicketKey
    searchAuditEventsApi(params)
      .then((res) => { setRows(res.data?.data || []); setMeta(res.data?.meta) })
      .catch((err) => setError(err?.response?.data?.detail || 'Error al cargar eventos'))
  }

  useEffect(() => { fetchData() }, [page])

  function handleSearch(e) {
    e.preventDefault()
    setPage(1)
    fetchData(1)
  }

  if (!['ADMIN', 'SUPERVISOR'].includes(currentUser?.roleCode)) {
    return <div className="page"><p>No tiene permisos para este modulo.</p></div>
  }

  return (
    <div className="page">
      <h1>Auditoria de Eventos</h1>
      {error && <p className="error-text">{error}</p>}
      <form className="filter-bar" onSubmit={handleSearch}>
        <input placeholder="Tipo evento" value={filters.eventType} onChange={(e) => setFilters({ ...filters, eventType: e.target.value })} />
        <input placeholder="Entidad" value={filters.entityName} onChange={(e) => setFilters({ ...filters, entityName: e.target.value })} />
        <input placeholder="Ticket key" value={filters.sourceTicketKey} onChange={(e) => setFilters({ ...filters, sourceTicketKey: e.target.value })} />
        <button className="btn btn-secondary" type="submit">Buscar</button>
      </form>
      <DataTable
        columns={[
          { key: 'eventType', title: 'Tipo', render: (r) => <StatusBadge value={r.eventType} /> },
          { key: 'entityName', title: 'Entidad' },
          { key: 'entityId', title: 'ID' },
          { key: 'sourceTicketKey', title: 'Ticket Key' },
          { key: 'userDisplayName', title: 'Usuario' },
          { key: 'eventTimestamp', title: 'Fecha', render: (r) => r.eventTimestamp ? new Date(r.eventTimestamp).toLocaleString() : '-' },
          { key: 'ipAddress', title: 'IP' },
        ]}
        rows={rows}
        emptyMessage="Sin eventos"
      />
      {meta && meta.totalPages > 1 && (
        <div className="row mt-16">
          <button className="btn btn-secondary" disabled={page <= 1} onClick={() => setPage(page - 1)}>Anterior</button>
          <span className="muted">Pagina {meta.page} de {meta.totalPages} ({meta.totalRecords} registros)</span>
          <button className="btn btn-secondary" disabled={page >= meta.totalPages} onClick={() => setPage(page + 1)}>Siguiente</button>
        </div>
      )}
    </div>
  )
}
