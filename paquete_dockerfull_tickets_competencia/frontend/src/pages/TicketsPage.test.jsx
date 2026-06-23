import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import TicketsPage from './TicketsPage'

const mockSearch = vi.fn()
const mockUseAuth = vi.fn()

vi.mock('../state/AuthContext', () => ({
  useAuth: () => mockUseAuth(),
}))

vi.mock('../services/api', () => ({
  searchTicketsApi: (p) => mockSearch(p),
}))

function mockResponse(overrides = {}) {
  return {
    data: {
      data: overrides.data || [],
      meta: overrides.meta || { page: 1, pageSize: 50, totalRecords: 0, totalPages: 1 },
    },
  }
}

describe('TicketsPage', () => {
  beforeEach(() => {
    mockSearch.mockReset()
    mockUseAuth.mockReturnValue({ currentUser: { roleCode: 'ADMIN' } })
  })

  it('renders filter inputs and search button', () => {
    mockSearch.mockResolvedValue(mockResponse())
    render(<MemoryRouter><TicketsPage /></MemoryRouter>)
    expect(screen.getByPlaceholderText('Cadena')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Tienda Comp.')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Llave origen')).toBeInTheDocument()
    expect(screen.getByText('Buscar')).toBeInTheDocument()
  })

  it('calls API on mount', async () => {
    mockSearch.mockResolvedValue(mockResponse({ data: [{ ticketId: 1, sourceBusinessCode: 'WMT', sourceStoreCode: '001', sourceTicketKey: 'K1', scanStatus: 'NO_FILE', hasScanFile: false }] }))
    render(<MemoryRouter><TicketsPage /></MemoryRouter>)
    await waitFor(() => {
      expect(mockSearch).toHaveBeenCalled()
    })
    expect(await screen.findByText('WMT')).toBeInTheDocument()
  })

  it('shows empty message when no results', async () => {
    mockSearch.mockResolvedValue(mockResponse())
    render(<MemoryRouter><TicketsPage /></MemoryRouter>)
    expect(await screen.findByText('No se encontraron tickets')).toBeInTheDocument()
  })

  it('shows pagination info', async () => {
    mockSearch.mockResolvedValue(mockResponse({
      data: Array.from({ length: 50 }, (_, i) => ({ ticketId: i + 1, sourceBusinessCode: 'C', sourceStoreCode: 'S', sourceTicketKey: `K${i}`, scanStatus: 'NO_FILE', hasScanFile: false })),
      meta: { page: 1, pageSize: 50, totalRecords: 120, totalPages: 3 },
    }))
    render(<MemoryRouter><TicketsPage /></MemoryRouter>)
    expect(await screen.findByText(/Total: 120 tickets/)).toBeInTheDocument()
    expect(screen.getByText(/Pág 1 de 3/)).toBeInTheDocument()
  })

  it('disables Anterior on first page and Siguiente on last', async () => {
    mockSearch.mockResolvedValue(mockResponse({
      data: [],
      meta: { page: 1, pageSize: 50, totalRecords: 5, totalPages: 1 },
    }))
    render(<MemoryRouter><TicketsPage /></MemoryRouter>)
    await screen.findByText(/Total: 5 tickets/)
    expect(screen.getByText('Anterior')).toBeDisabled()
    expect(screen.getByText('Siguiente')).toBeDisabled()
  })

  it('navigates to next page', async () => {
    let callCount = 0
    mockSearch.mockImplementation(async () => {
      callCount++
      return mockResponse({
        data: [{ ticketId: callCount, sourceBusinessCode: 'C', sourceStoreCode: 'S', sourceTicketKey: `K${callCount}`, scanStatus: 'NO_FILE', hasScanFile: false }],
        meta: { page: callCount, pageSize: 1, totalRecords: 3, totalPages: 3 },
      })
    })
    render(<MemoryRouter><TicketsPage /></MemoryRouter>)
    expect(await screen.findByText('K1')).toBeInTheDocument()
    fireEvent.click(screen.getByText('Siguiente'))
    await waitFor(() => {
      expect(screen.getByText('K2')).toBeInTheDocument()
    })
  })

  it('resets to page 1 on search', async () => {
    let page = 1
    mockSearch.mockImplementation(async (p) => {
      page = p.page
      return mockResponse({
        data: [],
        meta: { page: p.page, pageSize: 50, totalRecords: 120, totalPages: 3 },
      })
    })
    render(<MemoryRouter><TicketsPage /></MemoryRouter>)
    expect(await screen.findByText(/Pág 1 de 3/)).toBeInTheDocument()
    fireEvent.click(screen.getByText('Siguiente'))
    await waitFor(() => {
      expect(screen.getByText(/Pág 2 de 3/)).toBeInTheDocument()
    })
    expect(page).toBe(2)
    fireEvent.change(screen.getByPlaceholderText('Cadena'), { target: { value: 'WMT' } })
    fireEvent.click(screen.getByText('Buscar'))
    await waitFor(() => {
      expect(screen.getByText(/Pág 1 de 3/)).toBeInTheDocument()
    })
    expect(page).toBe(1)
  })
})
