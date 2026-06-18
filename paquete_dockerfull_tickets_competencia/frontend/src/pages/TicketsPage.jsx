import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../state/AuthContext'
import { searchTicketsApi } from '../services/api'
import DataTable from '../ui/DataTable'
import StatusBadge from '../ui/StatusBadge'

export default function TicketsPage() {
  const { demoUser } = useAuth()
  const [rows, setRows] = useState([])
  const [meta, setMeta] = useState(null)
  const [loading, setLoading] = useState(false)
  const [filters, setFilters] = useState({ sourceStatusCode: '', scanStatus: '', sourceTicketKey: '' })

  const load = async () => {
    setLoading(true)
    try {
      const params = Object.fromEntries(Object.entries({ ...filters, page: 1, pageSize: 50 }).filter(([,v]) => v !== '' && v !== null && v !== undefined))
      const res = await searchTicketsApi(demoUser, params)
      setRows(res.data?.data || [])
      setMeta(res.data?.meta || null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const columns = [
    { key: 'ticketId', title: 'ID' },
    { key: 'sourceTicketKey', title: 'Llave Origen' },
    { key: 'sourceStatusCode', title: 'Status Origen' },
    { key: 'scanStatus', title: 'Status Archivo', render: (r) => <StatusBadge value={r.scanStatus} /> },
    { key: 'hasScanFile', title: 'Tiene Archivo', render: (r) => r.hasScanFile ? 'Sí' : 'No' },
    { key: 'actions', title: 'Acciones', render: (r) => <Link className="link-btn" to={`/tickets/${r.ticketId}`}>Ver detalle</Link> },
  ]

  return (
    <div className="page">
      <h1>Tickets</h1>
      <div className="filter-bar">
        <input placeholder="sourceTicketKey" value={filters.sourceTicketKey} onChange={(e) => setFilters((s) => ({ ...s, sourceTicketKey: e.target.value }))} />
        <input placeholder="status origen" value={filters.sourceStatusCode} onChange={(e) => setFilters((s) => ({ ...s, sourceStatusCode: e.target.value }))} />
        <select value={filters.scanStatus} onChange={(e) => setFilters((s) => ({ ...s, scanStatus: e.target.value }))}>
          <option value="">scanStatus...</option>
          <option value="NO_FILE">NO_FILE</option>
          <option value="FILE_UPLOADED">FILE_UPLOADED</option>
          <option value="FILE_CONFIRMED">FILE_CONFIRMED</option>
        </select>
        <button className="btn" onClick={load}>Buscar</button>
      </div>
      {loading ? <p>Cargando...</p> : <DataTable columns={columns} rows={rows} emptyMessage="No se encontraron tickets" />}
      {meta && <p className="muted">Total: {meta.totalRecords} tickets</p>}
    </div>
  )
}
