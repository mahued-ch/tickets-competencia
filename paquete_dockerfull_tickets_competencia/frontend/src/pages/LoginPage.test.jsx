import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import LoginPage from './LoginPage'

const mockLogin = vi.fn()
const mockNavigate = vi.fn()
const mockUseAuth = vi.fn()

vi.mock('../state/AuthContext', () => ({
  useAuth: () => mockUseAuth(),
}))

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return { ...actual, useNavigate: () => mockNavigate }
})

function defaultAuth() {
  return { currentUser: null, login: mockLogin, loading: false, error: '' }
}

describe('LoginPage', () => {
  beforeEach(() => {
    mockLogin.mockReset()
    mockNavigate.mockReset()
    mockUseAuth.mockReturnValue(defaultAuth())
  })

  it('renders login form', () => {
    render(<MemoryRouter><LoginPage /></MemoryRouter>)
    expect(screen.getByPlaceholderText('Usuario')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Contraseña')).toBeInTheDocument()
    expect(screen.getByText('Ingresar')).toBeInTheDocument()
  })

  it('submit button is disabled when fields are empty', () => {
    render(<MemoryRouter><LoginPage /></MemoryRouter>)
    expect(screen.getByText('Ingresar')).toBeDisabled()
  })

  it('enables submit when both fields have values', () => {
    render(<MemoryRouter><LoginPage /></MemoryRouter>)
    fireEvent.change(screen.getByPlaceholderText('Usuario'), { target: { value: 'admin' } })
    fireEvent.change(screen.getByPlaceholderText('Contraseña'), { target: { value: 'demo123' } })
    expect(screen.getByText('Ingresar')).toBeEnabled()
  })

  it('calls login and navigates on success', async () => {
    mockLogin.mockResolvedValue(true)
    render(<MemoryRouter><LoginPage /></MemoryRouter>)
    fireEvent.change(screen.getByPlaceholderText('Usuario'), { target: { value: 'admin' } })
    fireEvent.change(screen.getByPlaceholderText('Contraseña'), { target: { value: 'demo123' } })
    fireEvent.click(screen.getByText('Ingresar'))
    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith('admin', 'demo123')
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard')
    })
  })

  it('disables inputs and shows loading text during login', () => {
    mockUseAuth.mockReturnValue({ ...defaultAuth(), loading: true })
    render(<MemoryRouter><LoginPage /></MemoryRouter>)
    expect(screen.getByPlaceholderText('Usuario')).toBeDisabled()
    expect(screen.getByPlaceholderText('Contraseña')).toBeDisabled()
    expect(screen.getByText('Ingresando...')).toBeDisabled()
  })

  it('displays error message from context', () => {
    mockUseAuth.mockReturnValue({ ...defaultAuth(), error: 'Credenciales inválidas' })
    render(<MemoryRouter><LoginPage /></MemoryRouter>)
    expect(screen.getByText('Credenciales inválidas')).toBeInTheDocument()
  })

  it('does not submit when fields are empty', () => {
    render(<MemoryRouter><LoginPage /></MemoryRouter>)
    fireEvent.click(screen.getByText('Ingresar'))
    expect(mockLogin).not.toHaveBeenCalled()
  })

  it('redirects to dashboard if already authenticated', () => {
    mockUseAuth.mockReturnValue({
      currentUser: { roleCode: 'ADMIN', loginName: 'admin' },
      login: mockLogin, loading: false, error: '',
    })
    render(<MemoryRouter><LoginPage /></MemoryRouter>)
    expect(mockNavigate).toHaveBeenCalledWith('/dashboard')
  })
})
