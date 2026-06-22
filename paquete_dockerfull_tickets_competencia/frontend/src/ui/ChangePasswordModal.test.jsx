import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import ChangePasswordModal from './ChangePasswordModal'

const mockChangePassword = vi.fn()
const mockOnClose = vi.fn()

vi.mock('../services/api', () => ({
  changeOwnPasswordApi: () => mockChangePassword(),
}))

describe('ChangePasswordModal', () => {
  beforeEach(() => {
    mockChangePassword.mockReset()
    mockOnClose.mockReset()
  })

  it('renders all fields and buttons', () => {
    render(<ChangePasswordModal onClose={mockOnClose} />)
    expect(screen.getByPlaceholderText('Contraseña actual')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Nueva contraseña')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Confirmar nueva contraseña')).toBeInTheDocument()
    expect(screen.getByText('Guardar')).toBeInTheDocument()
    expect(screen.getByText('Cancelar')).toBeInTheDocument()
  })

  it('shows error when passwords do not match', () => {
    render(<ChangePasswordModal onClose={mockOnClose} />)
    fireEvent.change(screen.getByPlaceholderText('Contraseña actual'), { target: { value: 'old' } })
    fireEvent.change(screen.getByPlaceholderText('Nueva contraseña'), { target: { value: 'new123' } })
    fireEvent.change(screen.getByPlaceholderText('Confirmar nueva contraseña'), { target: { value: 'different' } })
    fireEvent.click(screen.getByText('Guardar'))
    expect(screen.getByText('Las contraseñas nuevas no coinciden')).toBeInTheDocument()
  })

  it('shows error when password is too short', () => {
    render(<ChangePasswordModal onClose={mockOnClose} />)
    fireEvent.change(screen.getByPlaceholderText('Contraseña actual'), { target: { value: 'old' } })
    fireEvent.change(screen.getByPlaceholderText('Nueva contraseña'), { target: { value: 'ab' } })
    fireEvent.change(screen.getByPlaceholderText('Confirmar nueva contraseña'), { target: { value: 'ab' } })
    fireEvent.click(screen.getByText('Guardar'))
    expect(screen.getByText('La contraseña debe tener al menos 6 caracteres')).toBeInTheDocument()
  })

  it('calls API and shows success, then closes', async () => {
    mockChangePassword.mockResolvedValue({})
    render(<ChangePasswordModal onClose={mockOnClose} />)
    fireEvent.change(screen.getByPlaceholderText('Contraseña actual'), { target: { value: 'old' } })
    fireEvent.change(screen.getByPlaceholderText('Nueva contraseña'), { target: { value: 'newpass123' } })
    fireEvent.change(screen.getByPlaceholderText('Confirmar nueva contraseña'), { target: { value: 'newpass123' } })
    fireEvent.click(screen.getByText('Guardar'))
    await waitFor(() => {
      expect(screen.getByText('Contraseña actualizada correctamente')).toBeInTheDocument()
    })
    await waitFor(() => {
      expect(mockOnClose).toHaveBeenCalled()
    }, { timeout: 2000 })
  })

  it('shows error on API failure', async () => {
    mockChangePassword.mockRejectedValue({
      response: { data: { detail: 'Token inválido' } },
    })
    render(<ChangePasswordModal onClose={mockOnClose} />)
    fireEvent.change(screen.getByPlaceholderText('Contraseña actual'), { target: { value: 'old' } })
    fireEvent.change(screen.getByPlaceholderText('Nueva contraseña'), { target: { value: 'newpass123' } })
    fireEvent.change(screen.getByPlaceholderText('Confirmar nueva contraseña'), { target: { value: 'newpass123' } })
    fireEvent.click(screen.getByText('Guardar'))
    await waitFor(() => {
      expect(screen.getByText('Token inválido')).toBeInTheDocument()
    })
  })

  it('calls onClose when clicking overlay', () => {
    const { container } = render(<ChangePasswordModal onClose={mockOnClose} />)
    fireEvent.click(container.querySelector('.modal-overlay'))
    expect(mockOnClose).toHaveBeenCalled()
  })

  it('disables submit when fields are empty', () => {
    render(<ChangePasswordModal onClose={mockOnClose} />)
    expect(screen.getByText('Guardar')).toBeDisabled()
  })
})
