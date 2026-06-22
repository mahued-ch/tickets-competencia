import { render, screen, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import DashboardPage from './DashboardPage'

const mockGetCoverage = vi.fn()
const mockListBatches = vi.fn()
const mockUseAuth = vi.fn()

vi.mock('../state/AuthContext', () => ({
  useAuth: () => mockUseAuth(),
}))

vi.mock('../services/api', () => ({
  getCoverageApi: () => mockGetCoverage(),
  listBatchesApi: () => mockListBatches(),
}))

const mockCoverage = {
  totalTickets: 500, withFile: 100, withoutFile: 400, confirmed: 50,
  byBusiness: [{ businessCode: 'WMT', ticketCount: 200 }, { businessCode: 'BRS', ticketCount: 150 }],
  byScanStatus: { NO_FILE: 400, FILE_UPLOADED: 50, FILE_CONFIRMED: 50 },
  byStore: [{ storeCode: '001', ticketCount: 100 }, { storeCode: '002', ticketCount: 80 }],
}

const mockBatches = [
  { batchId: 1, batchCode: 'B1', status: 'ARCHIVED', insertedTicketCount: 10 },
]

describe('DashboardPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockUseAuth.mockReturnValue({ currentUser: { roleCode: 'ADMIN', displayName: 'Admin' } })
    mockGetCoverage.mockResolvedValue({ data: { data: mockCoverage } })
    mockListBatches.mockResolvedValue({ data: { data: mockBatches } })
  })

  it('renders KPI cards', async () => {
    render(<MemoryRouter><DashboardPage /></MemoryRouter>)
    expect(await screen.findByText('500')).toBeInTheDocument()
    expect(screen.getAllByText('100').length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText('400').length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText('50').length).toBeGreaterThanOrEqual(1)
  })

  it('renders bar chart by business', async () => {
    render(<MemoryRouter><DashboardPage /></MemoryRouter>)
    expect(await screen.findByText('WMT')).toBeInTheDocument()
    expect(screen.getByText('BRS')).toBeInTheDocument()
  })

  it('renders status chart', async () => {
    render(<MemoryRouter><DashboardPage /></MemoryRouter>)
    expect(await screen.findByText('NO_FILE')).toBeInTheDocument()
    expect(screen.getByText('FILE_UPLOADED')).toBeInTheDocument()
  })

  it('renders store chart', async () => {
    render(<MemoryRouter><DashboardPage /></MemoryRouter>)
    expect(await screen.findByText('001')).toBeInTheDocument()
    expect(screen.getByText('002')).toBeInTheDocument()
  })

  it('renders recent batches', async () => {
    render(<MemoryRouter><DashboardPage /></MemoryRouter>)
    expect(await screen.findByText('B1')).toBeInTheDocument()
  })

  it('shows loading state', () => {
    mockGetCoverage.mockReturnValue(new Promise(() => {}))
    render(<MemoryRouter><DashboardPage /></MemoryRouter>)
    expect(screen.getByText('Cargando...')).toBeInTheDocument()
  })
})
