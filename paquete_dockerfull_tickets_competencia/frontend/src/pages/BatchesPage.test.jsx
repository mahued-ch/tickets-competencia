import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import BatchesPage from './BatchesPage'

const mockListBatches = vi.fn()
const mockRunImport = vi.fn()
const mockUseAuth = vi.fn()

vi.mock('../state/AuthContext', () => ({
  useAuth: () => mockUseAuth(),
}))

vi.mock('../services/api', () => ({
  listBatchesApi: () => mockListBatches(),
  runImportApi: () => mockRunImport(),
}))

describe('BatchesPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockUseAuth.mockReturnValue({ currentUser: { roleCode: 'ADMIN' } })
    mockListBatches.mockResolvedValue({ data: { data: [
      { batchId: 1, batchCode: 'BATCH_001', status: 'ARCHIVED', insertedTicketCount: 10, skippedTicketCount: 2, errorCount: 0, importedAt: '2025-01-15T10:00:00Z' },
      { batchId: 2, batchCode: 'BATCH_002', status: 'PENDING', insertedTicketCount: 0, skippedTicketCount: 0, errorCount: 0, importedAt: null },
    ] } })
  })

  it('renders batch list', async () => {
    render(<MemoryRouter><BatchesPage /></MemoryRouter>)
    expect(await screen.findByText('BATCH_001')).toBeInTheDocument()
    expect(screen.getByText('BATCH_002')).toBeInTheDocument()
  })

  it('shows import button for ADMIN', async () => {
    render(<MemoryRouter><BatchesPage /></MemoryRouter>)
    expect(await screen.findByText('Importar ahora')).toBeInTheDocument()
  })

  it('calls runImportApi and shows success', async () => {
    mockRunImport.mockResolvedValue({ data: { data: [{ batchCode: 'BATCH_001', status: 'OK', inserted: 5, errors: 0 }] } })
    render(<MemoryRouter><BatchesPage /></MemoryRouter>)
    fireEvent.click(await screen.findByText('Importar ahora'))
    await waitFor(() => {
      expect(mockRunImport).toHaveBeenCalled()
    })
    expect(await screen.findByText(/Procesado:/)).toBeInTheDocument()
  })

  it('shows error on import failure', async () => {
    mockRunImport.mockRejectedValue({ response: { data: { detail: 'Error al importar' } } })
    render(<MemoryRouter><BatchesPage /></MemoryRouter>)
    fireEvent.click(await screen.findByText('Importar ahora'))
    await waitFor(() => {
      expect(screen.getByText('Error al importar')).toBeInTheDocument()
    })
  })

  it('hides import button for STORE_USER', () => {
    mockUseAuth.mockReturnValue({ currentUser: { roleCode: 'STORE_USER' } })
    render(<MemoryRouter><BatchesPage /></MemoryRouter>)
    expect(screen.queryByText('Importar ahora')).not.toBeInTheDocument()
  })

  it('shows "Sin lotes" when empty', async () => {
    mockListBatches.mockResolvedValue({ data: { data: [] } })
    render(<MemoryRouter><BatchesPage /></MemoryRouter>)
    expect(await screen.findByText('Sin lotes')).toBeInTheDocument()
  })
})
