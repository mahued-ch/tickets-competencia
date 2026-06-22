import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { searchTicketsApi } from '../services/api'
import DataTable from '../ui/DataTable'
import StatusBadge from '../ui/StatusBadge'

export default function TicketsPage() {
  const [rows, setRows] = useState([])
  const [meta, setMeta] = useState(null)
  const [loading, setLoading] = useState(false)
  const [filters, setFilters] = useState({
    sourceBusinessCode: '', sourceStoreCode: '',
    sourceTicketKey: '', sourceStatusCode: '', scanStatus: '',
    sourceTicketDateFrom: '', sourceTicketDateTo: '',
  })

  const load = async () => {
    setLoading(true)
    try {
      const params = Object.fromEntries(Object.entries({ ...filters, page: 1, pageSize: 50 }).filter(([,v]) => v !== '' && v !== null && v !== undefined))
      const res = await searchTicketsApi(params)
      setRows(res.data?.data || [])
      setMeta(res.data?.meta || null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const setF = (k) => (e) => setFilters((s) => ({ ...s, [k]: e.target.value }))

  const columns = [
    { key: 'ticketId', title: 'ID' },
    { key: 'sourceBusinessCode', title: 'Cadena' },
    { key: 'sourceStoreCode', title: 'Tienda' },
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
        <input placeholder="Cadena" value={filters.sourceBusinessCode} onChange={setF('sourceBusinessCode')} />
        <input placeholder="Tienda" value={filters.sourceStoreCode} onChange={setF('sourceStoreCode')} />
        <input placeholder="Llave origen" value={filters.sourceTicketKey} onChange={setF('sourceTicketKey')} />
        <input placeholder="Status origen" value={filters.sourceStatusCode} onChange={setF('sourceStatusCode')} />
        <select value={filters.scanStatus} onChange={setF('scanStatus')}>
          <option value="">scanStatus...</option>
          <option value="NO_FILE">NO_FILE</option>
          <option value="FILE_UPLOADED">FILE_UPLOADED</option>
          <option value="FILE_CONFIRMED">FILE_CONFIRMED</option>
        </select>
        <input type="date" value={filters.sourceTicketDateFrom} onChange={setF('sourceTicketDateFrom')} />
        <input type="date" value={filters.sourceTicketDateTo} onChange={setF('sourceTicketDateTo')} />
        <button className="btn" onClick={load}>Buscar</button>
      </div>
      {loading ? <p>Cargando...</p> : <DataTable columns={columns} rows={rows} emptyMessage="No se encontraron tickets" />}
      {meta && <p className="muted">Total: {meta.totalRecords} tickets</p>}
    </div>
  )
}
