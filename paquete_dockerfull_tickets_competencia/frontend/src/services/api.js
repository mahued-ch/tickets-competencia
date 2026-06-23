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

export function clearTicketsApi() {
  return api.post('/admin/clear-tickets', {}, authHeaders())
}

// ── Catalog APIs ────────────────────────────────────────────

export function listCompetitorStoresApi() {
  return api.get('/catalogs/competitor-stores', authHeaders())
}

export function createCompetitorStoreApi(payload) {
  return api.post('/catalogs/competitor-stores', payload, authHeaders())
}

export function updateCompetitorStoreApi(id, payload) {
  return api.put(`/catalogs/competitor-stores/${id}`, payload, authHeaders())
}

export function deleteCompetitorStoreApi(id) {
  return api.delete(`/catalogs/competitor-stores/${id}`, authHeaders())
}

export function listChedrauiProductsApi() {
  return api.get('/catalogs/chedraui-products', authHeaders())
}

export function createChedrauiProductApi(payload) {
  return api.post('/catalogs/chedraui-products', payload, authHeaders())
}

export function updateChedrauiProductApi(id, payload) {
  return api.put(`/catalogs/chedraui-products/${id}`, payload, authHeaders())
}

export function deleteChedrauiProductApi(id) {
  return api.delete(`/catalogs/chedraui-products/${id}`, authHeaders())
}

export function listCompetitorMappingsApi() {
  return api.get('/catalogs/competitor-mappings', authHeaders())
}

export function createCompetitorMappingApi(payload) {
  return api.post('/catalogs/competitor-mappings', payload, authHeaders())
}

export function updateCompetitorMappingApi(id, payload) {
  return api.put(`/catalogs/competitor-mappings/${id}`, payload, authHeaders())
}

export function deleteCompetitorMappingApi(id) {
  return api.delete(`/catalogs/competitor-mappings/${id}`, authHeaders())
}

export function listNearbyStoresApi() {
  return api.get('/catalogs/nearby-stores', authHeaders())
}

export function createNearbyStoreApi(payload) {
  return api.post('/catalogs/nearby-stores', payload, authHeaders())
}

export function updateNearbyStoreApi(id, payload) {
  return api.put(`/catalogs/nearby-stores/${id}`, payload, authHeaders())
}

export function deleteNearbyStoreApi(id) {
  return api.delete(`/catalogs/nearby-stores/${id}`, authHeaders())
}

// ── Enrichment APIs ──────────────────────────────────────────

export function triggerEnrichmentApi(ticketId) {
  return api.post(`/tickets/${ticketId}/enrichment`, {}, authHeaders())
}

export function getEnrichmentPreviewApi(ticketId) {
  return api.get(`/tickets/${ticketId}/enrichment-preview`, authHeaders())
}

export function updateEnrichmentItemsApi(ticketId, items) {
  return api.put(`/tickets/${ticketId}/enrichment-items`, items, authHeaders())
}

export function confirmEnrichmentApi(ticketId, payload) {
  return api.post(`/tickets/${ticketId}/enrichment-confirm`, payload, authHeaders())
}

export function rejectEnrichmentApi(ticketId, payload) {
  return api.post(`/tickets/${ticketId}/enrichment-reject`, payload, authHeaders())
}

// ── Scan Ticket APIs ──────────────────────────────────────────

export function createScanTicketApi(formData) {
  const headers = {
    ...authHeaders().headers,
    'Content-Type': 'multipart/form-data'
  }
  return api.post('/scan-tickets', formData, { headers })
}

export function listScanTicketsApi(params) {
  return api.get('/scan-tickets', { ...authHeaders(), params })
}

export function getScanTicketApi(ticketId) {
  return api.get(`/scan-tickets/${ticketId}`, authHeaders())
}

export function updateScanTicketItemsApi(ticketId, payload) {
  return api.put(`/scan-tickets/${ticketId}/items`, payload, authHeaders())
}

export function finalizeScanTicketApi(ticketId, payload) {
  return api.post(`/scan-tickets/${ticketId}/finalize`, payload, authHeaders())
}
