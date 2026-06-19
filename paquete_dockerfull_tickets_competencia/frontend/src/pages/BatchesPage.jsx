import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../state/AuthContext'
import { listBatchesApi } from '../services/api'
import DataTable from '../ui/DataTable'
import StatusBadge from '../ui/StatusBadge'

export default function BatchesPage() {
  const { currentUser } = useAuth()
  const [rows, setRows] = useState([])
  const [error, setError] = useState('')

  useEffect(() => {
    listBatchesApi()
      .then((res) => setRows(res.data?.data || []))
      .catch((err) => setError(err?.response?.data?.detail || 'Error al cargar lotes'))
  }, [])

  if (!['ADMIN', 'SUPERVISOR'].includes(currentUser?.roleCode)) {
    return <div className="page"><p>No tiene permisos para este modulo.</p></div>
  }

  return (
    <div className="page">
      <h1>Lotes de Integración</h1>
      {error && <p className="error-text">{error}</p>}
      <DataTable
        columns={[
          { key: 'batchCode', title: 'Batch Code' },
          { key: 'status', title: 'Status', render: (r) => <StatusBadge value={r.status} /> },
          { key: 'insertedTicketCount', title: 'Insertados' },
          { key: 'skippedTicketCount', title: 'Omitidos' },
          { key: 'errorCount', title: 'Errores' },
          { key: 'actions', title: 'Acciones', render: (r) => <Link className="link-btn" to={`/integration/batches/${r.batchId}`}>Ver detalle</Link> },
        ]}
        rows={rows}
        emptyMessage="Sin lotes"
      />
    </div>
  )
}
