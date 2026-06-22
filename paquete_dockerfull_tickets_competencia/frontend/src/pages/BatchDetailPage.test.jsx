import { render, screen, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import BatchDetailPage from './BatchDetailPage'

const mockGetBatch = vi.fn()
const mockGetFiles = vi.fn()
const mockGetErrors = vi.fn()
const mockSearchTickets = vi.fn()
const mockUseAuth = vi.fn()

vi.mock('../state/AuthContext', () => ({
  useAuth: () => mockUseAuth(),
}))

vi.mock('../services/api', () => ({
  getBatchApi: () => mockGetBatch(),
  getBatchFilesApi: () => mockGetFiles(),
  getBatchErrorsApi: () => mockGetErrors(),
  searchTicketsApi: () => mockSearchTickets(),
}))

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return { ...actual, useParams: () => ({ batchId: '42' }) }
})

const mockBatch = {
  batchId: 42, batchCode: 'BATCH_001', status: 'ARCHIVED',
  insertedTicketCount: 10, skippedTicketCount: 2, errorCount: 1,
}

const mockFiles = [
  { fileType: 'HEADER', fileName: 'header.json', recordCount: 10, status: 'PROCESSED' },
]

const mockErrors = [
  { entityType: 'ITEM', sourceTicketKey: 'K1', errorCode: 'PARSE', errorMessage: 'Bad field' },
]

const mockTickets = [
  { ticketId: 1, sourceBusinessCode: 'WMT', sourceStoreCode: '001', sourceTicketKey: 'K1', scanStatus: 'NO_FILE' },
]

describe('BatchDetailPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockUseAuth.mockReturnValue({ currentUser: { roleCode: 'ADMIN' } })
    mockGetBatch.mockResolvedValue({ data: { data: mockBatch } })
    mockGetFiles.mockResolvedValue({ data: { data: mockFiles } })
    mockGetErrors.mockResolvedValue({ data: { data: mockErrors } })
    mockSearchTickets.mockResolvedValue({ data: { data: mockTickets } })
  })

  it('renders batch summary', async () => {
    render(<MemoryRouter><BatchDetailPage /></MemoryRouter>)
    expect(await screen.findByText(/BATCH_001/)).toBeInTheDocument()
    expect(screen.getByText('ARCHIVED')).toBeInTheDocument()
    expect(screen.getByText('Insertados:')).toBeInTheDocument()
    expect(screen.getByText('Omitidos:')).toBeInTheDocument()
    expect(screen.getByText('Errores:')).toBeInTheDocument()
  })

  it('renders files section', async () => {
    render(<MemoryRouter><BatchDetailPage /></MemoryRouter>)
    expect(await screen.findByText('HEADER')).toBeInTheDocument()
    expect(screen.getByText('header.json')).toBeInTheDocument()
  })

  it('renders errors section', async () => {
    render(<MemoryRouter><BatchDetailPage /></MemoryRouter>)
    expect(await screen.findByText('ITEM')).toBeInTheDocument()
    expect(screen.getByText('Bad field')).toBeInTheDocument()
  })

  it('renders tickets section', async () => {
    render(<MemoryRouter><BatchDetailPage /></MemoryRouter>)
    expect(await screen.findByText('WMT')).toBeInTheDocument()
    expect(screen.getByText('001')).toBeInTheDocument()
  })

  it('shows loading state', () => {
    mockGetBatch.mockReturnValue(new Promise(() => {}))
    render(<MemoryRouter><BatchDetailPage /></MemoryRouter>)
    expect(screen.getByText('Cargando...')).toBeInTheDocument()
  })

  it('handles API errors', async () => {
    mockGetBatch.mockRejectedValue({ response: { data: { detail: 'Not found' } } })
    render(<MemoryRouter><BatchDetailPage /></MemoryRouter>)
    expect(await screen.findByText('Not found')).toBeInTheDocument()
  })
})
