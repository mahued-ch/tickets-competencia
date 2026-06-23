import { useEffect, useState, useCallback, useRef } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  getEnrichmentPreviewApi,
  triggerEnrichmentApi,
  updateEnrichmentItemsApi,
  confirmEnrichmentApi,
  rejectEnrichmentApi,
} from '../services/api'
import StatusBadge from '../ui/StatusBadge'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

function authToken() {
  const token = localStorage.getItem('tickets_competencia_token')
  if (token) return token
  const demo = localStorage.getItem('tickets_competencia_demo_user')
  if (demo) return null
  return null
}

function imageUrl(ticketId) {
  const base = `${API_BASE}/tickets/${ticketId}/scan-file/download`
  const token = authToken()
  if (token) return `${base}?token=${token}`
  const demo = localStorage.getItem('tickets_competencia_demo_user')
  if (demo) return `${base}?x-demo-user=${demo}`
  return base
}

export default function EnrichmentReviewPage() {
  const { ticketId } = useParams()
  const [preview, setPreview] = useState(null)
  const [items, setItems] = useState([])
  const [suggestions, setSuggestions] = useState([])
  const [nearbyStores, setNearbyStores] = useState([])
  const [status, setStatus] = useState(null)
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState('')
  const [notes, setNotes] = useState('')
  const [imgError, setImgError] = useState(false)
  const [leftWidth, setLeftWidth] = useState(35)
  const [isResizing, setIsResizing] = useState(false)
  const splitRef = useRef(null)

  const handleMouseDown = useCallback((e) => {
    e.preventDefault()
    setIsResizing(true)
  }, [])

  const handleMouseMove = useCallback((e) => {
    if (!isResizing || !splitRef.current) return
    const rect = splitRef.current.getBoundingClientRect()
    let pct = ((e.clientX - rect.left) / rect.width) * 100
    if (pct < 20) pct = 20
    if (pct > 60) pct = 60
    setLeftWidth(pct)
  }, [isResizing])

  const handleMouseUp = useCallback(() => {
    setIsResizing(false)
  }, [])

  useEffect(() => {
    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove)
      document.addEventListener('mouseup', handleMouseUp)
      document.body.style.cursor = 'col-resize'
      document.body.style.userSelect = 'none'
    }
    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }
  }, [isResizing, handleMouseMove, handleMouseUp])

  const load = useCallback(async () => {
    setLoading(true)
    setMessage('')
    try {
      const res = await getEnrichmentPreviewApi(ticketId)
      const d = res.data?.data
      if (d) {
        setPreview(d)
        setItems(d.extractedItems || [])
        setSuggestions(d.suggestions || [])
        setNearbyStores(d.nearbyStoreCodes || [])
        setStatus(d.status)
      } else {
        setItems([])
        setSuggestions([])
        setNearbyStores([])
        setStatus(null)
      }
    } catch {
      setItems([])
      setSuggestions([])
      setNearbyStores([])
      setStatus(null)
    } finally {
      setLoading(false)
    }
  }, [ticketId])

  useEffect(() => { load() }, [load])

  const handleTriggerEnrichment = async () => {
    setMessage('')
    try {
      const res = await triggerEnrichmentApi(ticketId)
      const d = res.data?.data
      setPreview(d)
      setItems(d.extractedItems || [])
      setSuggestions(d.suggestions || [])
      setNearbyStores(d.nearbyStoreCodes || [])
      setStatus(d.status)
    } catch (err) {
      setMessage(err?.response?.data?.detail || 'Error al iniciar enriquecimiento')
    }
  }

  const handleFieldChange = (idx, field, value) => {
    setItems((prev) => {
      const next = [...prev]
      next[idx] = { ...next[idx], [field]: value }
      return next
    })
  }

  const handleAddRow = () => {
    setItems((prev) => [...prev, { code: '', description: '', quantity: 1, unitPrice: 0, lineAmount: 0, sku: '', upc: '' }])
    setSuggestions((prev) => [...prev, {}])
  }

  const handleDeleteRow = (idx) => {
    setItems((prev) => prev.filter((_, i) => i !== idx))
    setSuggestions((prev) => prev.filter((_, i) => i !== idx))
  }

  const handleSaveItems = async () => {
    setMessage('')
    try {
      const payload = items.map((it, idx) => ({
        itemIndex: idx,
        sku: it.sku || null,
        upc: it.upc || null,
        description: it.description || null,
        quantity: it.quantity ?? null,
        unitPrice: it.unitPrice ?? null,
        lineAmount: it.lineAmount ?? null,
      }))
      const res = await updateEnrichmentItemsApi(ticketId, payload)
      const d = res.data?.data
      setItems(d.extractedItems || [])
      setSuggestions(d.suggestions || [])
      setMessage('Items guardados correctamente')
    } catch (err) {
      setMessage(err?.response?.data?.detail || 'Error al guardar items')
    }
  }

  const handleConfirm = async () => {
    if (!confirm('¿Confirmar enriquecimiento? Los items se grabarán definitivamente en el ticket.')) return
    setMessage('')
    try {
      const payload = {
        notes: notes || null,
        items: items.map((it, idx) => ({
          itemIndex: idx,
          sku: it.sku || null,
          upc: it.upc || null,
          description: it.description || null,
          quantity: it.quantity ?? null,
          unitPrice: it.unitPrice ?? null,
          lineAmount: it.lineAmount ?? null,
        })),
      }
      await confirmEnrichmentApi(ticketId, payload)
      setStatus('COMPLETED')
      setMessage('Enriquecimiento confirmado exitosamente')
    } catch (err) {
      setMessage(err?.response?.data?.detail || 'Error al confirmar')
    }
  }

  const handleReject = async () => {
    if (!confirm('¿Rechazar enriquecimiento?')) return
    setMessage('')
    try {
      await rejectEnrichmentApi(ticketId, { notes: notes || null })
      setStatus('REJECTED')
      setMessage('Enriquecimiento rechazado')
    } catch (err) {
      setMessage(err?.response?.data?.detail || 'Error al rechazar')
    }
  }

  if (loading) return <div className="page"><p>Cargando revisión...</p></div>

  const needsReview = items.length === 0 && status === null

  return (
    <div className="page">
      <div className="breadcrumbs">
        <Link to="/tickets">Tickets</Link> /{' '}
        <Link to={`/tickets/${ticketId}`}>Ticket #{ticketId}</Link> /{' '}
        <span className="breadcrumb-current">Revisión Enriquecimiento</span>
      </div>

      <div className="enrichment-header">
        <h1>Revisión de Enriquecimiento — Ticket #{ticketId}</h1>
        <div className="enrichment-status-bar">
          <span>Estado: <StatusBadge value={status || 'PENDING'} /></span>
          {preview?.enrichmentId && <span className="muted">Enrichment ID: {preview.enrichmentId}</span>}
        </div>
      </div>

      {needsReview ? (
        <div className="card" style={{ textAlign: 'center', padding: '40px' }}>
          <p>Este ticket no tiene un resultado de OCR para enriquecer.</p>
          <p className="muted">Asegúrate de que el ticket tenga un archivo escaneado y un resultado de OCR.</p>
          <button className="btn" onClick={handleTriggerEnrichment}>Iniciar Enriquecimiento</button>
        </div>
      ) : status === 'COMPLETED' || status === 'REJECTED' ? (
        <div className="card" style={{ textAlign: 'center', padding: '40px' }}>
          <p>Enriquecimiento {status === 'COMPLETED' ? 'completado' : 'rechazado'}.</p>
          <p className="muted">{preview?.notes || notes}</p>
          <Link to={`/tickets/${ticketId}`} className="btn">Volver al ticket</Link>
        </div>
      ) : (
        <div className="enrichment-split" ref={splitRef} style={isResizing ? { userSelect: 'none' } : undefined}>
          <div className="enrichment-left" style={{ width: `${leftWidth}%` }}>
            <div className="card">
              <div className="section-title">Imagen del Ticket</div>
              {imgError ? (
                <p className="error-text">No se pudo cargar la imagen</p>
              ) : (
                <img
                  src={imageUrl(ticketId)}
                  alt="Ticket escaneado"
                  className="enrichment-image"
                  onError={() => setImgError(true)}
                />
              )}
            </div>

            {nearbyStores.length > 0 && (
              <div className="card mt-16">
                <div className="section-title">Tiendas Cercanas</div>
                <div className="enrichment-stores">
                  {nearbyStores.map((code) => (
                    <span key={code} className="badge badge-neutral">{code}</span>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="enrichment-divider" onMouseDown={handleMouseDown} />

          <div className="enrichment-right" style={{ width: `${100 - leftWidth}%` }}>
            <div className="card">
              <div className="section-title">Items Extraídos</div>
              <p className="muted">Edita los campos directamente antes de confirmar.</p>
              <div className="row gap-8 mb-8">
                <button className="btn btn-sm" onClick={handleAddRow}>+ Agregar fila</button>
              </div>
              <div className="enrichment-table-wrap">
                <table className="table enrichment-table">
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>Código</th>
                      <th>Descripción</th>
                      <th>Cant</th>
                      <th>P. Unit</th>
                      <th>Importe</th>
                      <th>SKU</th>
                      <th>UPC</th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    {items.length === 0 ? (
                      <tr><td colSpan={9} className="empty-cell">Sin items extraídos</td></tr>
                    ) : (
                      items.map((it, idx) => {
                        const sug = suggestions[idx]
                        const highlight = sug?.requiresReview
                        return (
                          <tr key={idx} className={highlight ? 'enrichment-row-review' : ''}>
                            <td>{idx + 1}</td>
                            <td>
                              <input value={it.code || ''} onChange={(e) => handleFieldChange(idx, 'code', e.target.value)} />
                            </td>
                            <td>
                              <input value={it.description || ''} onChange={(e) => handleFieldChange(idx, 'description', e.target.value)} style={{ minWidth: 180 }} />
                              {sug?.matchType && <div className="match-label">{sug.matchType} {sug.confidence ? `${(sug.confidence * 100).toFixed(0)}%` : ''}</div>}
                            </td>
                            <td>
                              <input type="number" step="any" value={it.quantity ?? ''} onChange={(e) => handleFieldChange(idx, 'quantity', e.target.value ? Number(e.target.value) : null)} />
                            </td>
                            <td>
                              <input type="number" step="any" value={it.unitPrice ?? ''} onChange={(e) => handleFieldChange(idx, 'unitPrice', e.target.value ? Number(e.target.value) : null)} />
                            </td>
                            <td>
                              <input type="number" step="any" value={it.lineAmount ?? ''} onChange={(e) => handleFieldChange(idx, 'lineAmount', e.target.value ? Number(e.target.value) : null)} />
                            </td>
                            <td>
                              <input value={it.sku || sug?.suggestedSku || ''} onChange={(e) => handleFieldChange(idx, 'sku', e.target.value)} />
                            </td>
                            <td>
                              <input value={it.upc || sug?.suggestedUpc || ''} onChange={(e) => handleFieldChange(idx, 'upc', e.target.value)} />
                            </td>
                            <td>
                              <button className="btn btn-sm btn-danger" onClick={() => handleDeleteRow(idx)} title="Eliminar fila">×</button>
                            </td>
                          </tr>
                        )
                      })
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="card mt-16">
              <div className="section-title">Notas</div>
              <textarea
                placeholder="Comentarios opcionales"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                style={{ marginBottom: 16 }}
              />
              <div className="section-title">Acciones</div>
              <div className="row gap-8">
                <button className="btn" onClick={handleSaveItems}>Guardar Cambios</button>
                <button className="btn btn-success" onClick={handleConfirm}>Confirmar Enriquecimiento</button>
                <button className="btn btn-danger" onClick={handleReject}>Rechazar</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {message && <p className="mt-16 info-box">{message}</p>}
    </div>
  )
}
