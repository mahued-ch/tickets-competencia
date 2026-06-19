import { useState, useMemo } from 'react'

export default function DataTable({ columns, rows, emptyMessage = 'Sin datos', defaultSortKey }) {
  const [sortKey, setSortKey] = useState(defaultSortKey || null)
  const [sortDir, setSortDir] = useState('asc')

  const sorted = useMemo(() => {
    if (!sortKey) return rows
    const col = columns.find((c) => c.key === sortKey)
    if (!col || !col.sortable) return rows
    const compare = col.compare || ((a, b) => String(a != null ? a : '').localeCompare(String(b != null ? b : ''), 'es', { sensitivity: 'base' }))
    return [...rows].sort((a, b) => {
      const va = col.render ? col.render(a) : a[sortKey]
      const vb = col.render ? col.render(b) : b[sortKey]
      return sortDir === 'asc' ? compare(va, vb) : compare(vb, va)
    })
  }, [rows, sortKey, sortDir, columns])

  const handleSort = (key) => {
    if (sortKey === key) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortKey(key)
      setSortDir('asc')
    }
  }

  return (
    <div className="table-wrap">
      <table className="table">
        <thead>
          <tr>
            {columns.map((c) => (
              <th key={c.key} className={c.sortable ? 'sortable' : ''} onClick={() => c.sortable && handleSort(c.key)}>
                {c.title}
                {sortKey === c.key && <span className="sort-arrow">{sortDir === 'asc' ? ' ▲' : ' ▼'}</span>}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="empty-cell">{emptyMessage}</td>
            </tr>
          ) : (
            sorted.map((row, idx) => (
              <tr key={row.id || idx}>
                {columns.map((c) => (
                  <td key={c.key}>{c.render ? c.render(row) : row[c.key]}</td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  )
}
