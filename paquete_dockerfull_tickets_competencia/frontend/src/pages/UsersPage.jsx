import { useEffect, useState } from 'react'
import { useAuth } from '../state/AuthContext'
import { adminSetPasswordApi, assignStoreApi, createUserApi, deleteUserApi, removeStoreApi, listUserStoresApi, listUsersApi, updateUserApi } from '../services/api'
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
  const [editUser, setEditUser] = useState(null)
  const [editForm, setEditForm] = useState({})

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

  const handleOpenEdit = (user) => {
    setEditUser(user)
    setEditForm({ login_name: user.loginName, display_name: user.displayName, email: user.email || '', role_code: user.roleCode, is_active: user.isActive })
    setMsg('')
  }

  const handleEditUser = async (e) => {
    e.preventDefault()
    setMsg('')
    try {
      const payload = {}
      if (editForm.login_name !== editUser.loginName) payload.login_name = editForm.login_name
      if (editForm.display_name !== editUser.displayName) payload.display_name = editForm.display_name
      if (editForm.email !== (editUser.email || '')) payload.email = editForm.email || null
      if (editForm.role_code !== editUser.roleCode) payload.role_code = editForm.role_code
      if (editForm.is_active !== editUser.isActive) payload.is_active = editForm.is_active
      if (Object.keys(payload).length === 0) { setEditUser(null); return }
      await updateUserApi(editUser.userId, payload)
      setEditUser(null)
      loadUsers()
      setMsg('Usuario actualizado correctamente')
    } catch (err) {
      setMsg(err?.response?.data?.detail || 'Error al actualizar usuario')
    }
  }

  const handleDeleteUser = async (user) => {
    if (!confirm(`¿Eliminar al usuario "${user.displayName}" (${user.loginName})?`)) return
    setMsg('')
    try {
      await deleteUserApi(user.userId)
      if (selectedUser?.userId === user.userId) setSelectedUser(null)
      loadUsers()
      setMsg('Usuario desactivado correctamente')
    } catch (err) {
      setMsg(err?.response?.data?.detail || 'Error al eliminar usuario')
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
              { key: 'loginName', title: 'Login', sortable: true },
              { key: 'displayName', title: 'Nombre', sortable: true },
              { key: 'roleCode', title: 'Rol', sortable: true },
              { key: 'isActive', title: 'Activo', render: (r) => r.isActive ? 'Sí' : 'No' },
              { key: 'actions', title: 'Acciones', render: (r) => (
                <div className="row gap-8">
                  <button className="btn btn-secondary btn-sm" onClick={() => handleSelectUser(r)}>Tiendas</button>
                  <button className="btn btn-sm" onClick={() => handleOpenEdit(r)}>Editar</button>
                  <button className="btn btn-sm btn-danger" onClick={() => handleDeleteUser(r)}>Eliminar</button>
                </div>
              ) },
            ]}
            rows={users}
            emptyMessage="Sin usuarios"
            defaultSortKey="loginName"
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
                  { key: 'storeCode', title: 'Tienda', sortable: true },
                  { key: 'isActive', title: 'Activa', render: (r) => r.isActive ? 'Sí' : 'No' },
                  { key: 'actions', title: '', render: (r) => <button className="btn btn-secondary btn-sm" onClick={() => handleRemoveStore(r.storeCode)}>Eliminar</button> },
                ]}
                rows={stores}
                emptyMessage="Sin tiendas asignadas"
                defaultSortKey="storeCode"
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

      {editUser && (
        <div className="modal-overlay" onClick={() => setEditUser(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>Editar usuario</h2>
            <p className="muted">{editUser.loginName}</p>
            <form onSubmit={handleEditUser} className="stack">
              <label>Usuario</label>
              <input value={editForm.login_name || ''} onChange={(e) => setEditForm((s) => ({ ...s, login_name: e.target.value }))} required />
              <label>Nombre completo</label>
              <input value={editForm.display_name || ''} onChange={(e) => setEditForm((s) => ({ ...s, display_name: e.target.value }))} required />
              <label>Email</label>
              <input type="email" value={editForm.email || ''} onChange={(e) => setEditForm((s) => ({ ...s, email: e.target.value }))} />
              <label>Rol</label>
              <select value={editForm.role_code || 'STORE_USER'} onChange={(e) => setEditForm((s) => ({ ...s, role_code: e.target.value }))}>
                <option value="STORE_USER">Usuario de tienda</option>
                <option value="SUPERVISOR">Supervisor</option>
                <option value="ADMIN">Administrador</option>
              </select>
              <label className="row gap-8" style={{ alignItems: 'center' }}>
                <input type="checkbox" checked={editForm.is_active ?? true} onChange={(e) => setEditForm((s) => ({ ...s, is_active: e.target.checked }))} />
                Usuario activo
              </label>
              <div className="row gap-8">
                <button type="submit" className="btn" disabled={!editForm.login_name || !editForm.display_name}>Guardar</button>
                <button type="button" className="btn btn-secondary" onClick={() => setEditUser(null)}>Cancelar</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
