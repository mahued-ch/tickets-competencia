import { useEffect, useRef, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useAuth } from '../state/AuthContext'
import { confirmScanFileApi, getActiveScanFileApi, getTicketApi, getTicketItemsApi, getTicketStoresApi, uploadScanFileApi } from '../services/api'
import DataTable from '../ui/DataTable'
import StatusBadge from '../ui/StatusBadge'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

function authToken() {
  const token = localStorage.getItem('tickets_competencia_token')
  if (token) return token
  const demo = localStorage.getItem('tickets_competencia_demo_user')
  if (demo) return null
  return null
}

function scanImageUrl(ticketId) {
  const base = `${API_BASE}/tickets/${ticketId}/scan-file/download`
  const token = authToken()
  if (token) return `${base}?token=${token}`
  const demo = localStorage.getItem('tickets_competencia_demo_user')
  if (demo) return `${base}?x-demo-user=${demo}`
  return base
}

export default function TicketDetailPage() {
  const { ticketId } = useParams()
  const { currentUser } = useAuth()
  const [detail, setDetail] = useState(null)
  const [items, setItems] = useState([])
  const [stores, setStores] = useState([])
  const [scanFile, setScanFile] = useState(null)
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState('')
  const [uploading, setUploading] = useState(false)
  const [notes, setNotes] = useState('')
  const [selectedFile, setSelectedFile] = useState(null)
  const [leftWidth, setLeftWidth] = useState(30)
  const [isResizing, setIsResizing] = useState(false)
  const splitRef = useRef(null)

  const handleMouseDown = (e) => {
    e.preventDefault()
    setIsResizing(true)
  }

  useEffect(() => {
    if (!isResizing) return
    const handleMouseMove = (e) => {
      if (!splitRef.current) return
      const rect = splitRef.current.getBoundingClientRect()
      let pct = ((e.clientX - rect.left) / rect.width) * 100
      if (pct < 20) pct = 20
      if (pct > 50) pct = 50
      setLeftWidth(pct)
    }
    const handleMouseUp = () => setIsResizing(false)
    window.addEventListener('mousemove', handleMouseMove)
    window.addEventListener('mouseup', handleMouseUp)
    return () => {
      window.removeEventListener('mousemove', handleMouseMove)
      window.removeEventListener('mouseup', handleMouseUp)
    }
  }, [isResizing])

  const load = async () => {
    setLoading(true)
    setMessage('')
    try {
      const [d, i, s, sf] = await Promise.all([
        getTicketApi(ticketId),
        getTicketItemsApi(ticketId),
        getTicketStoresApi(ticketId),
        getActiveScanFileApi(ticketId),
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
      await uploadScanFileApi(ticketId, form)
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
      await confirmScanFileApi(ticketId, { notes: 'Confirmado desde starter frontend' })
      setMessage('Archivo confirmado correctamente')
      await load()
    } catch (err) {
      setMessage(err?.response?.data?.detail || 'Error al confirmar archivo')
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
          <div className="enrichment-split" ref={splitRef} style={isResizing ? { userSelect: 'none' } : undefined}>
            <div className="enrichment-left" style={{ width: `${leftWidth}%` }}>
              <div className="stack-sm">
                <div><strong>Archivo:</strong> {scanFile.fileName}</div>
                <div><strong>Versión:</strong> {scanFile.versionNumber}</div>
                <div><strong>MimeType:</strong> {scanFile.mimeType}</div>
                <div><strong>Confirmado:</strong> {scanFile.isConfirmed ? 'Sí' : 'No'}</div>
                <div className="row gap-8 mt-16">
                  {canConfirm && <button className="btn btn-success" onClick={handleConfirm}>Confirmar</button>}
                  {scanFile.isConfirmed && (
                    <Link to={`/tickets/${ticketId}/enrichment-review`} className="btn">Enriquecer</Link>
                  )}
                </div>
              </div>
            </div>

            <div className="enrichment-divider" onMouseDown={handleMouseDown} />

            <div className="enrichment-right" style={{ width: `${100 - leftWidth}%` }}>
              <img
                src={scanImageUrl(ticketId)}
                alt={scanFile.fileName}
                className="enrichment-image"
              />
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
