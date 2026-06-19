import { useState } from 'react'
import { changeOwnPasswordApi } from '../services/api'

export default function ChangePasswordModal({ onClose }) {
  const [current, setCurrent] = useState('')
  const [newPass, setNewPass] = useState('')
  const [confirm, setConfirm] = useState('')
  const [msg, setMsg] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setMsg('')
    if (newPass !== confirm) {
      setMsg('Las contraseñas nuevas no coinciden')
      return
    }
    if (newPass.length < 6) {
      setMsg('La contraseña debe tener al menos 6 caracteres')
      return
    }
    setLoading(true)
    try {
      await changeOwnPasswordApi(current, newPass)
      setMsg('Contraseña actualizada correctamente')
      setCurrent('')
      setNewPass('')
      setConfirm('')
      setTimeout(onClose, 1500)
    } catch (err) {
      setMsg(err?.response?.data?.detail || 'Error al cambiar contraseña')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h2>Cambiar contraseña</h2>
        <form onSubmit={handleSubmit} className="stack">
          <input type="password" placeholder="Contraseña actual" value={current} onChange={(e) => setCurrent(e.target.value)} disabled={loading} />
          <input type="password" placeholder="Nueva contraseña" value={newPass} onChange={(e) => setNewPass(e.target.value)} disabled={loading} />
          <input type="password" placeholder="Confirmar nueva contraseña" value={confirm} onChange={(e) => setConfirm(e.target.value)} disabled={loading} />
          {msg && <p className={msg.includes('correctamente') ? 'info-box' : 'error-text'}>{msg}</p>}
          <div className="row gap-8">
            <button type="submit" className="btn" disabled={loading || !current || !newPass || !confirm}>
              {loading ? 'Guardando...' : 'Guardar'}
            </button>
            <button type="button" className="btn btn-secondary" onClick={onClose}>Cancelar</button>
          </div>
        </form>
      </div>
    </div>
  )
}
