import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { AuthProvider, useAuth } from './AuthContext'

function TestConsumer() {
  const { currentUser, loading } = useAuth()
  return <div data-testid="consumer">{loading ? 'loading' : currentUser ? `user: ${currentUser.loginName}` : 'no user'}</div>
}

describe('AuthContext', () => {
  it('provides no user initially', () => {
    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    )
    expect(screen.getByTestId('consumer')).toHaveTextContent('no user')
  })

  it('throws when used outside provider', () => {
    expect(() => render(<TestConsumer />)).toThrow()
  })
})
