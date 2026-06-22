import { useEffect, useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../state/AuthContext'
import { listBatchesApi, runImportApi } from '../services/api'
import DataTable from '../ui/DataTable'
import StatusBadge from '../ui/StatusBadge'

export default function BatchesPage() {
  const { currentUser } = useAuth()
  const [rows, setRows] = useState([])
  const [error, setError] = useState('')
  const [importing, setImporting] = useState(false)
  const [importResult, setImportResult] = useState('')

  const load = useCallback(() => {
    listBatchesApi()
      .then((res) => setRows(res.data?.data || []))
      .catch((err) => setError(err?.response?.data?.detail || 'Error al cargar lotes'))
  }, [])

  useEffect(() => { load() }, [load])

  const handleImport = async () => {
    setImporting(true)
    setImportResult('')
    try {
      const res = await runImportApi()
      const results = res.data?.data || []
      if (!results.length) {
        setImportResult('No se encontraron lotes pendientes.')
      } else {
        const lines = results.map((r) => `${r.batchCode}: ${r.status} (insertados=${r.inserted}, errores=${r.errors})`).join('; ')
        setImportResult(`Procesado: ${lines}`)
      }
      load()
    } catch (err) {
      setImportResult(err?.response?.data?.detail || 'Error al ejecutar importación')
    } finally {
      setImporting(false)
    }
  }

  if (!['ADMIN', 'SUPERVISOR'].includes(currentUser?.roleCode)) {
    return <div className="page"><p>No tiene permisos para este modulo.</p></div>
  }

  return (
    <div className="page">
      <div className="row" style={{ justifyContent: 'space-between', alignItems: 'center' }}>
        <h1 style={{ margin: 0 }}>Lotes de Integración</h1>
        <button className="btn" disabled={importing} onClick={handleImport}>
          {importing ? 'Importando...' : 'Importar ahora'}
        </button>
      </div>
      {importResult && <p className="mt-16 info-box">{importResult}</p>}
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
