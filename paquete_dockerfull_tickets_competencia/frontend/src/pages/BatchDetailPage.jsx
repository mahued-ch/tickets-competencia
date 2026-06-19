import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { getBatchApi, getBatchErrorsApi, getBatchFilesApi } from '../services/api'
import DataTable from '../ui/DataTable'

export default function BatchDetailPage() {
  const { batchId } = useParams()
  const [batch, setBatch] = useState(null)
  const [files, setFiles] = useState([])
  const [errors, setErrors] = useState([])
  const [msg, setMsg] = useState('')

  useEffect(() => {
    Promise.all([
      getBatchApi(batchId),
      getBatchFilesApi(batchId),
      getBatchErrorsApi(batchId),
    ])
      .then(([b, f, e]) => {
        setBatch(b.data?.data || null)
        setFiles(f.data?.data || [])
        setErrors(e.data?.data || [])
      })
      .catch((err) => setMsg(err?.response?.data?.detail || 'Error al cargar lote'))
  }, [batchId])

  if (!batch) return <div className="page"><p>{msg || 'Cargando...'}</p></div>

  return (
    <div className="page">
      <h1>Lote {batch.batchCode}</h1>
      <div className="card">
        <div><strong>Status:</strong> {batch.status}</div>
        <div><strong>Insertados:</strong> {batch.insertedTicketCount}</div>
        <div><strong>Omitidos:</strong> {batch.skippedTicketCount}</div>
        <div><strong>Errores:</strong> {batch.errorCount}</div>
      </div>

      <div className="card mt-16">
        <div className="section-title">Archivos</div>
        <DataTable columns={[
          { key: 'fileType', title: 'Tipo' },
          { key: 'fileName', title: 'Nombre' },
          { key: 'recordCount', title: 'Registros' },
          { key: 'status', title: 'Status' },
        ]} rows={files} emptyMessage="Sin archivos" />
      </div>

      <div className="card mt-16">
        <div className="section-title">Errores</div>
        <DataTable columns={[
          { key: 'entityType', title: 'Entidad' },
          { key: 'sourceTicketKey', title: 'Llave' },
          { key: 'errorCode', title: 'Código' },
          { key: 'errorMessage', title: 'Mensaje' },
        ]} rows={errors} emptyMessage="Sin errores" />
      </div>
    </div>
  )
}
