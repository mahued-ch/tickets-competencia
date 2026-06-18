import { useEffect, useState } from 'react'
import { useAuth } from '../state/AuthContext'
import { assignStoreApi, listUserStoresApi, listUsersApi } from '../services/api'
import DataTable from '../ui/DataTable'

export default function UsersPage() {
  const { demoUser, currentUser } = useAuth()
  const [users, setUsers] = useState([])
  const [selectedUser, setSelectedUser] = useState(null)
  const [stores, setStores] = useState([])
  const [newStore, setNewStore] = useState('')
  const [msg, setMsg] = useState('')

  const loadUsers = () => {
    listUsersApi(demoUser)
      .then((res) => setUsers(res.data?.data || []))
      .catch((err) => setMsg(err?.response?.data?.detail || 'Error al cargar usuarios'))
  }

  const loadStores = (userId) => {
    listUserStoresApi(demoUser, userId)
      .then((res) => setStores(res.data?.data || []))
      .catch((err) => setMsg(err?.response?.data?.detail || 'Error al cargar tiendas'))
  }

  useEffect(() => { loadUsers() }, [demoUser])

  if (currentUser?.roleCode !== 'ADMIN') {
    return <div className="page"><p>No tiene permisos para este modulo.</p></div>
  }

  const handleSelectUser = (user) => {
    setSelectedUser(user)
    loadStores(user.userId)
  }

  const handleAssignStore = async () => {
    if (!selectedUser || !newStore) return
    setMsg('')
    try {
      await assignStoreApi(demoUser, selectedUser.userId, { storeCode: newStore })
      setNewStore('')
      loadStores(selectedUser.userId)
      setMsg('Tienda asignada correctamente')
    } catch (err) {
      setMsg(err?.response?.data?.detail || 'Error al asignar tienda')
    }
  }

  return (
    <div className="page">
      <h1>Usuarios</h1>
      {msg && <p className="info-box">{msg}</p>}
      <div className="grid two-cols">
        <div className="card">
          <div className="section-title">Lista de usuarios</div>
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
                ]}
                rows={stores}
                emptyMessage="Sin tiendas asignadas"
              />
              <div className="row gap-8 mt-16">
                <input placeholder="Nueva tienda" value={newStore} onChange={(e) => setNewStore(e.target.value)} />
                <button className="btn" onClick={handleAssignStore}>Asignar tienda</button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
