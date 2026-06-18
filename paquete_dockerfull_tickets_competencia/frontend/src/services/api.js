import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'
})

function configWithUser(demoUser) {
  return {
    headers: {
      'X-Demo-User': demoUser
    }
  }
}

export function meApi(demoUser) {
  return api.get('/me', configWithUser(demoUser))
}

export function getHealth() {
  return api.get('/health')
}

export function searchTicketsApi(demoUser, params) {
  return api.get('/tickets', { ...configWithUser(demoUser), params })
}

export function getTicketApi(demoUser, ticketId) {
  return api.get(`/tickets/${ticketId}`, configWithUser(demoUser))
}

export function getTicketItemsApi(demoUser, ticketId) {
  return api.get(`/tickets/${ticketId}/items`, configWithUser(demoUser))
}

export function getTicketStoresApi(demoUser, ticketId) {
  return api.get(`/tickets/${ticketId}/stores`, configWithUser(demoUser))
}

export function getActiveScanFileApi(demoUser, ticketId) {
  return api.get(`/tickets/${ticketId}/scan-file`, configWithUser(demoUser))
}

export function uploadScanFileApi(demoUser, ticketId, formData) {
  return api.post(`/tickets/${ticketId}/scan-file`, formData, {
    ...configWithUser(demoUser),
    headers: {
      ...configWithUser(demoUser).headers,
      'Content-Type': 'multipart/form-data'
    }
  })
}

export function confirmScanFileApi(demoUser, ticketId, payload) {
  return api.put(`/tickets/${ticketId}/scan-file/confirm`, payload, configWithUser(demoUser))
}

export async function fetchScanFileBlob(demoUser, ticketId) {
  const res = await fetch(`${api.defaults.baseURL}/tickets/${ticketId}/scan-file/content`, {
    headers: { 'X-Demo-User': demoUser }
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  const blob = await res.blob()
  return blob
}

export function listBatchesApi(demoUser) {
  return api.get('/integration/batches', configWithUser(demoUser))
}

export function getBatchApi(demoUser, batchId) {
  return api.get(`/integration/batches/${batchId}`, configWithUser(demoUser))
}

export function getBatchFilesApi(demoUser, batchId) {
  return api.get(`/integration/batches/${batchId}/files`, configWithUser(demoUser))
}

export function getBatchErrorsApi(demoUser, batchId) {
  return api.get(`/integration/batches/${batchId}/errors`, configWithUser(demoUser))
}

export function listUsersApi(demoUser) {
  return api.get('/admin/users', configWithUser(demoUser))
}

export function listUserStoresApi(demoUser, userId) {
  return api.get(`/admin/users/${userId}/stores`, configWithUser(demoUser))
}

export function assignStoreApi(demoUser, userId, payload) {
  return api.post(`/admin/users/${userId}/stores`, payload, configWithUser(demoUser))
}
