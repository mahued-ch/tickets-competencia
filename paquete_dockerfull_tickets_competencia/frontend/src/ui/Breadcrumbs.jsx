import { Link, useLocation } from 'react-router-dom'

const LABEL_MAP = {
  dashboard: 'Dashboard',
  tickets: 'Tickets',
  'integration/batches': 'Lotes',
  'admin/users': 'Usuarios',
}

function segmentLabel(segment, isNumeric) {
  if (isNumeric) return 'Detalle'
  return LABEL_MAP[segment] || segment
}

export default function Breadcrumbs() {
  const { pathname } = useLocation()
  if (pathname === '/dashboard') return null

  const parts = pathname.split('/').filter(Boolean)
  const crumbs = []
  let acc = ''

  for (let i = 0; i < parts.length; i++) {
    acc += '/' + parts[i]
    const isNumeric = /^\d+$/.test(parts[i])
    const label = segmentLabel(parts[i], isNumeric)
    const isLast = i === parts.length - 1

    if (isLast && isNumeric) {
      crumbs.push({ path: acc, label, isLast: true })
    } else {
      crumbs.push({ path: acc, label, isLast })
    }
  }

  return (
    <nav className="breadcrumbs">
      <Link to="/dashboard">Inicio</Link>
      {crumbs.map((c) => (
        <span key={c.path}>
          {' / '}
          {c.isLast ? <span className="breadcrumb-current">{c.label}</span> : <Link to={c.path}>{c.label}</Link>}
        </span>
      ))}
    </nav>
  )
}
