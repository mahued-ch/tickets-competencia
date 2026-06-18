import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { useAuth } from '../state/AuthContext'
import { confirmScanFileApi, fetchScanFileBlob, getActiveScanFileApi, getTicketApi, getTicketItemsApi, getTicketStoresApi, uploadScanFileApi } from '../services/api'
import DataTable from '../ui/DataTable'
import StatusBadge from '../ui/StatusBadge'

export default function TicketDetailPage() {
  const { ticketId } = useParams()
  const { demoUser, currentUser } = useAuth()
  const [detail, setDetail] = useState(null)
  const [items, setItems] = useState([])
  const [stores, setStores] = useState([])
  const [scanFile, setScanFile] = useState(null)
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState('')
  const [uploading, setUploading] = useState(false)
  const [notes, setNotes] = useState('')
  const [selectedFile, setSelectedFile] = useState(null)

  const load = async () => {
    setLoading(true)
    setMessage('')
    try {
      const [d, i, s, sf] = await Promise.all([
        getTicketApi(demoUser, ticketId),
        getTicketItemsApi(demoUser, ticketId),
        getTicketStoresApi(demoUser, ticketId),
        getActiveScanFileApi(demoUser, ticketId),
      ])
      setDetail(d.data?.data || null)
      setItems(i.data?.data || [])
      setStores(s.data?.data || [])
      setScanFile(sf.data?.data || null)
    } catch (err) {
      setMessage(err?.response?.data?.detail || 'Error al cargar ticket')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [ticketId])

  const handleUpload = async () => {
    if (!selectedFile) return setMessage('Debe seleccionar un archivo')
    const form = new FormData()
    form.append('file', selectedFile)
    if (notes) form.append('notes', notes)
    setUploading(true)
    setMessage('')
    try {
      await uploadScanFileApi(demoUser, ticketId, form)
      setMessage('Archivo cargado/reemplazado correctamente')
      setSelectedFile(null)
      setNotes('')
      await load()
    } catch (err) {
      setMessage(err?.response?.data?.detail || 'Error al cargar archivo')
    } finally {
      setUploading(false)
    }
  }

  const handleConfirm = async () => {
    if (!confirm('Una vez confirmado, no podra reemplazarse. ¿Desea continuar?')) return
    setMessage('')
    try {
      await confirmScanFileApi(demoUser, ticketId, { notes: 'Confirmado desde starter frontend' })
      setMessage('Archivo confirmado correctamente')
      await load()
    } catch (err) {
      setMessage(err?.response?.data?.detail || 'Error al confirmar archivo')
    }
  }

  const handleViewFile = async () => {
    setMessage('')
    try {
      const blob = await fetchScanFileBlob(demoUser, ticketId)
      const url = URL.createObjectURL(blob)
      window.open(url, '_blank', 'noopener,noreferrer')
      setTimeout(() => URL.revokeObjectURL(url), 10000)
    } catch (err) {
      setMessage('No fue posible visualizar el archivo')
    }
  }

  if (loading) return <div className="page"><p>Cargando detalle...</p></div>
  if (!detail?.ticket) return <div className="page"><p>No se encontro el ticket</p><p className="error-text">{message}</p></div>

  const t = detail.ticket
  const scanStatus = t.scanStatus
  const canOperate = currentUser?.roleCode === 'STORE_USER' || currentUser?.roleCode === 'ADMIN' || currentUser?.roleCode === 'SUPERVISOR'
  const canUpload = canOperate && t.sourceStatusCode === '9' && scanStatus !== 'FILE_CONFIRMED'
  const canConfirm = canOperate && scanFile && !scanFile.isConfirmed

  return (
    <div className="page">
      <h1>Detalle del Ticket #{t.ticketId}</h1>
      <div className="card">
        <div className="grid two-cols">
          <div><strong>Llave Origen:</strong> {t.sourceTicketKey}</div>
          <div><strong>Status Origen:</strong> {t.sourceStatusCode || '-'}</div>
          <div><strong>Fecha Ticket:</strong> {String(t.sourceTicketDate)}</div>
          <div><strong>Status Archivo:</strong> <StatusBadge value={t.scanStatus} /></div>
        </div>
      </div>

      <div className="grid two-cols mt-16">
        <div className="card">
          <div className="section-title">Items</div>
          <DataTable
            columns={[
              { key: 'itemSequence', title: 'Secuencia' },
              { key: 'productCode', title: 'Producto' },
              { key: 'productDescription', title: 'Descripción' },
              { key: 'quantity', title: 'Cantidad' },
              { key: 'unitPrice', title: 'Precio' },
              { key: 'lineAmount', title: 'Importe' },
            ]}
            rows={items}
            emptyMessage="Sin items"
          />
        </div>

        <div className="card">
          <div className="section-title">Tiendas</div>
          <DataTable
            columns={[
              { key: 'storeCode', title: 'Tienda' },
            ]}
            rows={stores}
            emptyMessage="Sin tiendas"
          />
        </div>
      </div>

      <div className="card mt-16">
        <div className="section-title">Archivo escaneado</div>
        {!scanFile ? (
          <p className="muted">Este ticket no tiene archivo escaneado.</p>
        ) : (
          <div className="stack-sm">
            <div><strong>Archivo:</strong> {scanFile.fileName}</div>
            <div><strong>Versión:</strong> {scanFile.versionNumber}</div>
            <div><strong>MimeType:</strong> {scanFile.mimeType}</div>
            <div><strong>Confirmado:</strong> {scanFile.isConfirmed ? 'Sí' : 'No'}</div>
            <div className="row gap-8">
              <button className="btn btn-secondary" onClick={handleViewFile}>Ver archivo</button>
              {canConfirm && <button className="btn btn-success" onClick={handleConfirm}>Confirmar</button>}
            </div>
          </div>
        )}

        {canUpload ? (
          <div className="upload-box mt-16">
            <div className="section-subtitle">{scanFile ? 'Reemplazar archivo' : 'Cargar archivo'}</div>
            <input type="file" onChange={(e) => setSelectedFile(e.target.files?.[0] || null)} />
            <textarea placeholder="Notas (opcional)" value={notes} onChange={(e) => setNotes(e.target.value)} />
            <button className="btn" disabled={uploading} onClick={handleUpload}>{uploading ? 'Procesando...' : (scanFile ? 'Reemplazar' : 'Cargar')}</button>
            <p className="muted">Permitido solo si status origen = 9 y el archivo no esta confirmado.</p>
          </div>
        ) : (
          <p className="muted mt-16">No es posible cargar/reemplazar archivo para este ticket en su estado actual.</p>
        )}

        {message && <p className="mt-16 info-box">{message}</p>}
      </div>
    </div>
  )
}
