import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import StatusBadge from './StatusBadge'

describe('StatusBadge', () => {
  it('renders the value text', () => {
    render(<StatusBadge value="ACTIVE" />)
    expect(screen.getByText('ACTIVE')).toBeInTheDocument()
  })

  it('renders fallback for null as N/A', () => {
    render(<StatusBadge value={null} />)
    expect(screen.getByText('N/A')).toBeInTheDocument()
  })

  it('renders fallback for empty string as N/A', () => {
    render(<StatusBadge value="" />)
    expect(screen.getByText('N/A')).toBeInTheDocument()
  })

  it('has a span element', () => {
    render(<StatusBadge value="OK" />)
    const el = screen.getByText('OK')
    expect(el.tagName).toBe('SPAN')
  })
})
