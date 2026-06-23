import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import AppLayout from './AppLayout'

const mockUseAuth = vi.fn()
const mockLogout = vi.fn()

vi.mock('../state/AuthContext', () => ({
  useAuth: () => mockUseAuth(),
}))

function renderWithAuth(overrides = {}) {
  mockUseAuth.mockReturnValue({
    currentUser: { roleCode: 'STORE_USER', displayName: 'Alice', loginName: 'alice' },
    logout: mockLogout,
    ...overrides,
  })
  return render(
    <MemoryRouter>
      <AppLayout />
    </MemoryRouter>,
  )
}

describe('AppLayout', () => {
  it('shows Dashboard and Tickets for all roles', () => {
    renderWithAuth()
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    expect(screen.getByText('Tickets')).toBeInTheDocument()
  })

  it('hides Cobertura, Lotes, Auditoria for STORE_USER', () => {
    renderWithAuth()
    expect(screen.queryByText('Cobertura')).not.toBeInTheDocument()
    expect(screen.queryByText('Lotes')).not.toBeInTheDocument()
    expect(screen.queryByText('Auditoria')).not.toBeInTheDocument()
    expect(screen.queryByText('Usuarios')).not.toBeInTheDocument()
  })

  it('shows Cobertura, Lotes, Auditoria for SUPERVISOR', () => {
    renderWithAuth({ currentUser: { roleCode: 'SUPERVISOR', displayName: 'Sup', loginName: 'sup' } })
    expect(screen.getByText('Cobertura')).toBeInTheDocument()
    expect(screen.getByText('Lotes')).toBeInTheDocument()
    expect(screen.getByText('Auditoria')).toBeInTheDocument()
    expect(screen.queryByText('Usuarios')).not.toBeInTheDocument()
  })

  it('shows all menu items including Usuarios and Catálogos for ADMIN', () => {
    renderWithAuth({ currentUser: { roleCode: 'ADMIN', displayName: 'Admin', loginName: 'admin' } })
    expect(screen.getByText('Cobertura')).toBeInTheDocument()
    expect(screen.getByText('Lotes')).toBeInTheDocument()
    expect(screen.getByText('Auditoria')).toBeInTheDocument()
    expect(screen.getByText('Usuarios')).toBeInTheDocument()
    expect(screen.getByText('Catálogos')).toBeInTheDocument()
  })

  it('displays user name and role in topbar', () => {
    renderWithAuth({ currentUser: { roleCode: 'ADMIN', displayName: 'Bob', loginName: 'bob' } })
    expect(screen.getByText('Bob')).toBeInTheDocument()
    expect(screen.getByText('(ADMIN)')).toBeInTheDocument()
  })

  it('calls logout on button click', () => {
    renderWithAuth()
    fireEvent.click(screen.getByText('Salir'))
    expect(mockLogout).toHaveBeenCalledOnce()
  })

  it('shows Cambiar contraseña button', () => {
    renderWithAuth()
    expect(screen.getByText('Cambiar contraseña')).toBeInTheDocument()
  })
})
