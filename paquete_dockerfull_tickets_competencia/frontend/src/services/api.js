import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'
})

function authHeaders() {
  const token = localStorage.getItem('tickets_competencia_token')
  if (token) {
    return { headers: { Authorization: `Bearer ${token}` } }
  }
  const demo = localStorage.getItem('tickets_competencia_demo_user')
  if (demo) {
    return { headers: { 'X-Demo-User': demo } }
  }
  return {}
}

export function loginApi(loginName, password) {
  return api.post('/auth/login', { login_name: loginName, password })
}

export function logoutApi(token) {
  return api.post('/auth/logout', { token })
}

export function meApi() {
  return api.get('/me', authHeaders())
}

export function getHealth() {
  return api.get('/health')
}

export function searchTicketsApi(params) {
  return api.get('/tickets', { ...authHeaders(), params })
}

export function getTicketApi(ticketId) {
  return api.get(`/tickets/${ticketId}`, authHeaders())
}

export function getTicketItemsApi(ticketId) {
  return api.get(`/tickets/${ticketId}/items`, authHeaders())
}

export function getTicketStoresApi(ticketId) {
  return api.get(`/tickets/${ticketId}/stores`, authHeaders())
}

export function getActiveScanFileApi(ticketId) {
  return api.get(`/tickets/${ticketId}/scan-file`, authHeaders())
}

export function uploadScanFileApi(ticketId, formData) {
  const headers = {
    ...authHeaders().headers,
    'Content-Type': 'multipart/form-data'
  }
  return api.post(`/tickets/${ticketId}/scan-file`, formData, { headers })
}

export function confirmScanFileApi(ticketId, payload) {
  return api.put(`/tickets/${ticketId}/scan-file/confirm`, payload, authHeaders())
}

export async function fetchScanFileBlob(ticketId) {
  const h = authHeaders().headers || {}
  const res = await fetch(`${api.defaults.baseURL}/tickets/${ticketId}/scan-file/content`, { headers: h })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  const blob = await res.blob()
  return blob
}

export function listBatchesApi() {
  return api.get('/integration/batches', authHeaders())
}

export function runImportApi() {
  return api.post('/integration/import', {}, authHeaders())
}

export function getBatchApi(batchId) {
  return api.get(`/integration/batches/${batchId}`, authHeaders())
}

export function getBatchFilesApi(batchId) {
  return api.get(`/integration/batches/${batchId}/files`, authHeaders())
}

export function getBatchErrorsApi(batchId) {
  return api.get(`/integration/batches/${batchId}/errors`, authHeaders())
}

export function getCoverageApi() {
  return api.get('/tickets/coverage', authHeaders())
}

export function searchAuditEventsApi(params) {
  return api.get('/audit/events', { ...authHeaders(), params })
}

export function listUsersApi() {
  return api.get('/admin/users', authHeaders())
}

export function listUserStoresApi(userId) {
  return api.get(`/admin/users/${userId}/stores`, authHeaders())
}

export function assignStoreApi(userId, payload) {
  return api.post(`/admin/users/${userId}/stores`, payload, authHeaders())
}

export function removeStoreApi(userId, storeCode) {
  return api.delete(`/admin/users/${userId}/stores/${storeCode}`, authHeaders())
}

export function changeOwnPasswordApi(currentPassword, newPassword) {
  return api.put('/auth/password', { current_password: currentPassword, new_password: newPassword }, authHeaders())
}

export function adminSetPasswordApi(userId, newPassword) {
  return api.put(`/admin/users/${userId}/password`, { new_password: newPassword }, authHeaders())
}

export function createUserApi(payload) {
  return api.post('/admin/users', payload, authHeaders())
}

export function updateUserApi(userId, payload) {
  return api.put(`/admin/users/${userId}`, payload, authHeaders())
}

export function deleteUserApi(userId) {
  return api.delete(`/admin/users/${userId}`, authHeaders())
}
