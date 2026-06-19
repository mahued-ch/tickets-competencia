import { useEffect, useState } from 'react'
import { useAuth } from '../state/AuthContext'
import { adminSetPasswordApi, assignStoreApi, createUserApi, removeStoreApi, listUserStoresApi, listUsersApi } from '../services/api'
import DataTable from '../ui/DataTable'

export default function UsersPage() {
  const { currentUser } = useAuth()
  const [users, setUsers] = useState([])
  const [selectedUser, setSelectedUser] = useState(null)
  const [stores, setStores] = useState([])
  const [newStore, setNewStore] = useState('')
  const [msg, setMsg] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [createForm, setCreateForm] = useState({ login_name: '', display_name: '', password: '', role_code: 'STORE_USER', email: '' })

  const loadUsers = () => {
    listUsersApi()
      .then((res) => setUsers(res.data?.data || []))
      .catch((err) => setMsg(err?.response?.data?.detail || 'Error al cargar usuarios'))
  }

  const loadStores = (userId) => {
    listUserStoresApi(userId)
      .then((res) => setStores(res.data?.data || []))
      .catch((err) => setMsg(err?.response?.data?.detail || 'Error al cargar tiendas'))
  }

  useEffect(() => { loadUsers() }, [])

  if (currentUser?.roleCode !== 'ADMIN') {
    return <div className="page"><p>No tiene permisos para este modulo.</p></div>
  }

  const handleSelectUser = (user) => {
    setSelectedUser(user)
    setNewPassword('')
    loadStores(user.userId)
  }

  const handleAssignStore = async () => {
    if (!selectedUser || !newStore) return
    setMsg('')
    try {
      await assignStoreApi(selectedUser.userId, { storeCode: newStore })
      setNewStore('')
      loadStores(selectedUser.userId)
      setMsg('Tienda asignada correctamente')
    } catch (err) {
      setMsg(err?.response?.data?.detail || 'Error al asignar tienda')
    }
  }

  const handleRemoveStore = async (storeCode) => {
    if (!selectedUser) return
    if (!confirm(`¿Eliminar tienda ${storeCode} del usuario ${selectedUser.displayName}?`)) return
    setMsg('')
    try {
      await removeStoreApi(selectedUser.userId, storeCode)
      loadStores(selectedUser.userId)
      setMsg('Tienda eliminada correctamente')
    } catch (err) {
      setMsg(err?.response?.data?.detail || 'Error al eliminar tienda')
    }
  }

  const handleCreateUser = async (e) => {
    e.preventDefault()
    setMsg('')
    try {
      await createUserApi(createForm)
      setShowCreateForm(false)
      setCreateForm({ login_name: '', display_name: '', password: '', role_code: 'STORE_USER', email: '' })
      loadUsers()
      setMsg('Usuario creado correctamente')
    } catch (err) {
      setMsg(err?.response?.data?.detail || 'Error al crear usuario')
    }
  }

  const handleSetPassword = async () => {
    if (!selectedUser || !newPassword) return
    if (newPassword.length < 6) {
      setMsg('La contraseña debe tener al menos 6 caracteres')
      return
    }
    setMsg('')
    try {
      await adminSetPasswordApi(selectedUser.userId, newPassword)
      setNewPassword('')
      setMsg('Contraseña actualizada correctamente')
    } catch (err) {
      setMsg(err?.response?.data?.detail || 'Error al cambiar contraseña')
    }
  }

  return (
    <div className="page">
      <h1>Usuarios</h1>
      {msg && <p className={msg.includes('correctamente') ? 'info-box' : 'error-text'}>{msg}</p>}
      <div className="grid two-cols">
        <div className="card">
          <div className="section-title">Lista de usuarios</div>
          <div className="row gap-8 mb-16" style={{ marginBottom: 12 }}>
            <button className="btn" onClick={() => setShowCreateForm(!showCreateForm)}>
              {showCreateForm ? 'Cancelar' : '+ Nuevo usuario'}
            </button>
          </div>
          {showCreateForm && (
            <form onSubmit={handleCreateUser} className="stack-sm" style={{ marginBottom: 16, padding: 12, border: '1px solid #e5e7eb', borderRadius: 8 }}>
              <input placeholder="Usuario" value={createForm.login_name} onChange={(e) => setCreateForm((s) => ({ ...s, login_name: e.target.value }))} required />
              <input placeholder="Nombre completo" value={createForm.display_name} onChange={(e) => setCreateForm((s) => ({ ...s, display_name: e.target.value }))} required />
              <input placeholder="Email" type="email" value={createForm.email} onChange={(e) => setCreateForm((s) => ({ ...s, email: e.target.value }))} />
              <input placeholder="Contraseña" type="password" value={createForm.password} onChange={(e) => setCreateForm((s) => ({ ...s, password: e.target.value }))} required />
              <select value={createForm.role_code} onChange={(e) => setCreateForm((s) => ({ ...s, role_code: e.target.value }))}>
                <option value="STORE_USER">Usuario de tienda</option>
                <option value="SUPERVISOR">Supervisor</option>
                <option value="ADMIN">Administrador</option>
              </select>
              <button type="submit" className="btn btn-success" disabled={!createForm.login_name || !createForm.display_name || !createForm.password}>Crear usuario</button>
            </form>
          )}
          <DataTable
            columns={[
              { key: 'loginName', title: 'Login' },
              { key: 'displayName', title: 'Nombre' },
              { key: 'roleCode', title: 'Rol' },
              { key: 'isActive', title: 'Activo', render: (r) => r.isActive ? 'Sí' : 'No' },
              { key: 'actions', title: 'Acciones', render: (r) => <button className="btn btn-secondary btn-sm" onClick={() => handleSelectUser(r)}>Ver tiendas</button> },
            ]}
            rows={users}
            emptyMessage="Sin usuarios"
          />
        </div>

        <div className="card">
          <div className="section-title">Tiendas del usuario</div>
          {!selectedUser ? (
            <p className="muted">Seleccione un usuario</p>
          ) : (
            <>
              <p><strong>{selectedUser.displayName}</strong> ({selectedUser.loginName})</p>
              <DataTable
                columns={[
                  { key: 'storeCode', title: 'Tienda' },
                  { key: 'isActive', title: 'Activa', render: (r) => r.isActive ? 'Sí' : 'No' },
                  { key: 'actions', title: '', render: (r) => <button className="btn btn-secondary btn-sm" onClick={() => handleRemoveStore(r.storeCode)}>Eliminar</button> },
                ]}
                rows={stores}
                emptyMessage="Sin tiendas asignadas"
              />
              <div className="row gap-8 mt-16">
                <input placeholder="Nueva tienda" value={newStore} onChange={(e) => setNewStore(e.target.value)} />
                <button className="btn" onClick={handleAssignStore}>Asignar tienda</button>
              </div>

              <div className="upload-box mt-16">
                <div className="section-subtitle">Cambiar contraseña</div>
                <div className="row gap-8">
                  <input type="password" placeholder="Nueva contraseña" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} />
                  <button className="btn" onClick={handleSetPassword} disabled={!newPassword}>Guardar</button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
