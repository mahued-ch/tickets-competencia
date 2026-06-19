import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import DataTable from './DataTable'

describe('DataTable', () => {
  const columns = [
    { key: 'name', title: 'Name' },
    { key: 'age', title: 'Age' },
  ]

  it('renders headers', () => {
    render(<DataTable columns={columns} rows={[]} />)
    expect(screen.getByText('Name')).toBeInTheDocument()
    expect(screen.getByText('Age')).toBeInTheDocument()
  })

  it('renders empty message when no rows', () => {
    render(<DataTable columns={columns} rows={[]} emptyMessage="No data" />)
    expect(screen.getByText('No data')).toBeInTheDocument()
  })

  it('renders rows', () => {
    const rows = [
      { id: 1, name: 'Alice', age: 30 },
      { id: 2, name: 'Bob', age: 25 },
    ]
    render(<DataTable columns={columns} rows={rows} />)
    expect(screen.getByText('Alice')).toBeInTheDocument()
    expect(screen.getByText('Bob')).toBeInTheDocument()
    expect(screen.getByText('30')).toBeInTheDocument()
  })

  it('uses custom render function', () => {
    const cols = [
      { key: 'name', title: 'Name', render: (r) => <strong>{r.name}</strong> },
    ]
    render(<DataTable columns={cols} rows={[{ id: 1, name: 'Alice' }]} />)
    expect(screen.getByText('Alice').tagName).toBe('STRONG')
  })
})
