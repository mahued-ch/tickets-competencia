import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { createScanTicketApi } from '../services/api'
import { listCompetitorStoresApi } from '../services/api'

export default function ScanTicketNewPage() {
  const navigate = useNavigate()
  const [file, setFile] = useState(null)
  const [businessCode, setBusinessCode] = useState('')
  const [storeCode, setStoreCode] = useState('')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  const [competitorStores, setCompetitorStores] = useState([])

  useState(() => {
    listCompetitorStoresApi()
      .then((res) => setCompetitorStores(res.data?.data || []))
      .catch(() => {})
  }, [])

  const businessCodes = [...new Set(
    (competitorStores || []).map((s) => s.businessCode || s.business_code)
  )].sort()
  const filteredStores = (competitorStores || []).filter(
    (s) => (s.businessCode || s.business_code) === businessCode
  )

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!file || !businessCode || !storeCode) {
      setMessage('Completa todos los campos')
      return
    }
    setLoading(true)
    setMessage('')
    const formData = new FormData()
    formData.append('file', file)
    formData.append('business_code', businessCode)
    formData.append('store_code', storeCode)
    try {
      const res = await createScanTicketApi(formData)
      const ticketId = res.data?.data?.ticketId
      if (ticketId) {
        navigate(`/scan-tickets/${ticketId}`)
      } else {
        setMessage('Error: no se recibió el ID del ticket')
      }
    } catch (err) {
      setMessage(err?.response?.data?.detail || 'Error al crear ticket desde escaneo')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page">
      <div className="breadcrumbs">
        <Link to="/scan-tickets">Escaneo</Link> / <span className="breadcrumb-current">Nuevo escaneo</span>
      </div>

      <h1>Nuevo Escaneo de Ticket</h1>

      <form onSubmit={handleSubmit} className="card" style={{ maxWidth: 500 }}>
        <div className="form-group">
          <label>Imagen del ticket</label>
          <input
            type="file"
            accept="image/*,.pdf"
            onChange={(e) => setFile(e.target.files[0])}
            required
          />
        </div>

        <div className="form-group">
          <label>Competidor</label>
          <select value={businessCode} onChange={(e) => { setBusinessCode(e.target.value); setStoreCode('') }} required>
            <option value="">Seleccionar...</option>
            {businessCodes.map((bc) => (
              <option key={bc} value={bc}>{bc}</option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label>Tienda del competidor</label>
          <select value={storeCode} onChange={(e) => setStoreCode(e.target.value)} required disabled={!businessCode}>
            <option value="">Seleccionar...</option>
            {filteredStores.map((s) => (
              <option key={s.storeId || s.store_code} value={s.storeCode || s.store_code}>
                {s.storeCode || s.store_code} — {s.storeName || s.store_name || ''}
              </option>
            ))}
          </select>
        </div>

        <button className="btn btn-success" type="submit" disabled={loading}>
          {loading ? 'Procesando...' : 'Subir y procesar'}
        </button>

        {message && <p className="mt-16 info-box">{message}</p>}
      </form>
    </div>
  )
}
