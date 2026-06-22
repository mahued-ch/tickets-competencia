import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import Breadcrumbs from './Breadcrumbs'

function renderAt(path) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Breadcrumbs />
    </MemoryRouter>,
  )
}

describe('Breadcrumbs', () => {
  it('returns null on dashboard', () => {
    const { container } = renderAt('/dashboard')
    expect(container.innerHTML).toBe('')
  })

  it('shows Inicio and Tickets for /tickets', () => {
    renderAt('/tickets')
    expect(screen.getByText('Inicio')).toBeInTheDocument()
    expect(screen.getByText('Tickets')).toBeInTheDocument()
  })

  it('shows Detalle for numeric segment', () => {
    renderAt('/tickets/42')
    expect(screen.getByText('Detalle')).toBeInTheDocument()
  })

  it('shows raw segment names for paths not in LABEL_MAP', () => {
    renderAt('/admin/users')
    expect(screen.getByText('admin')).toBeInTheDocument()
    expect(screen.getByText('users')).toBeInTheDocument()
  })

  it('shows raw segment names for integration/batches', () => {
    renderAt('/integration/batches')
    expect(screen.getByText('integration')).toBeInTheDocument()
    expect(screen.getByText('batches')).toBeInTheDocument()
  })

  it('marks last segment as current', () => {
    renderAt('/tickets')
    const current = screen.getByText('Tickets')
    expect(current.className).toContain('breadcrumb-current')
  })
})
