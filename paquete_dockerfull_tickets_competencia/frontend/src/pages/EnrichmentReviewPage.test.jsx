import { render, screen, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import EnrichmentReviewPage from './EnrichmentReviewPage'

const mockGetPreview = vi.fn()
const mockTrigger = vi.fn()
const mockUpdateItems = vi.fn()
const mockConfirm = vi.fn()
const mockReject = vi.fn()
const mockUseAuth = vi.fn()

vi.mock('../state/AuthContext', () => ({
  useAuth: () => mockUseAuth(),
}))

vi.mock('../services/api', () => ({
  getEnrichmentPreviewApi: () => mockGetPreview(),
  triggerEnrichmentApi: () => mockTrigger(),
  updateEnrichmentItemsApi: () => mockUpdateItems(),
  confirmEnrichmentApi: () => mockConfirm(),
  rejectEnrichmentApi: () => mockReject(),
}))

const mockPreviewData = {
  enrichmentId: 1,
  ticketId: 1,
  ocrResultId: 1,
  status: 'REVIEW',
  rawText: 'MOCK OCR',
  extractedItems: [
    { code: 'P01', description: 'LECHE LALA 1L', quantity: 2, unitPrice: 25.5, lineAmount: 51.0 },
    { code: null, description: 'PAN BIMBO', quantity: 1, unitPrice: 42.0, lineAmount: 42.0 },
  ],
  suggestions: [
    { itemIndex: 0, matchType: 'CODE', confidence: 0.98, requiresReview: false },
    { itemIndex: 1, matchType: null, confidence: 0.0, requiresReview: true },
  ],
  nearbyStoreCodes: ['CHD001'],
}

describe('EnrichmentReviewPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockUseAuth.mockReturnValue({ currentUser: { roleCode: 'ADMIN', displayName: 'Admin' } })
  })

  it('shows loading then triggers enrichment when no preview', async () => {
    mockGetPreview.mockRejectedValue(new Error('Not found'))
    mockTrigger.mockResolvedValue({ data: { data: mockPreviewData } })

    render(<MemoryRouter initialEntries={['/tickets/1/enrichment-review']}>
      <Routes>
        <Route path="/tickets/:ticketId/enrichment-review" element={<EnrichmentReviewPage />} />
      </Routes>
    </MemoryRouter>)
    expect(screen.getByText('Cargando revisión...')).toBeInTheDocument()
    await waitFor(() => expect(screen.getByText('Revisión de Enriquecimiento — Ticket #1')).toBeInTheDocument())
  })

  it('renders preview with items and suggestions', async () => {
    mockGetPreview.mockResolvedValue({ data: { data: mockPreviewData } })

    render(<MemoryRouter initialEntries={['/tickets/1/enrichment-review']}>
      <Routes>
        <Route path="/tickets/:ticketId/enrichment-review" element={<EnrichmentReviewPage />} />
      </Routes>
    </MemoryRouter>)
    expect(await screen.findByDisplayValue('LECHE LALA 1L')).toBeInTheDocument()
    expect(screen.getByDisplayValue('PAN BIMBO')).toBeInTheDocument()
    expect(screen.getByText('CHD001')).toBeInTheDocument()
  })

  it('shows status COMPLETED when enrichment is done', async () => {
    const completedData = { ...mockPreviewData, status: 'COMPLETED' }
    mockGetPreview.mockResolvedValue({ data: { data: completedData } })

    render(<MemoryRouter initialEntries={['/tickets/1/enrichment-review']}>
      <Routes>
        <Route path="/tickets/:ticketId/enrichment-review" element={<EnrichmentReviewPage />} />
      </Routes>
    </MemoryRouter>)
    expect(await screen.findByText('Enriquecimiento completado.')).toBeInTheDocument()
  })

  it('shows status REJECTED when enrichment is rejected', async () => {
    const rejectedData = { ...mockPreviewData, status: 'REJECTED' }
    mockGetPreview.mockResolvedValue({ data: { data: rejectedData } })

    render(<MemoryRouter initialEntries={['/tickets/1/enrichment-review']}>
      <Routes>
        <Route path="/tickets/:ticketId/enrichment-review" element={<EnrichmentReviewPage />} />
      </Routes>
    </MemoryRouter>)
    expect(await screen.findByText('Enriquecimiento rechazado.')).toBeInTheDocument()
  })

  it('shows trigger button when no enrichment exists', async () => {
    mockGetPreview.mockRejectedValue(new Error('Not found'))
    mockTrigger.mockResolvedValue({ data: { data: mockPreviewData } })

    render(<MemoryRouter initialEntries={['/tickets/1/enrichment-review']}>
      <Routes>
        <Route path="/tickets/:ticketId/enrichment-review" element={<EnrichmentReviewPage />} />
      </Routes>
    </MemoryRouter>)
    await waitFor(() => expect(screen.getByText('Iniciar Enriquecimiento')).toBeInTheDocument())
  })
})
