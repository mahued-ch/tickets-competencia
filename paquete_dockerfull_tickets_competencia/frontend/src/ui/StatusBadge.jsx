export default function StatusBadge({ value }) {
  const cls = value === 'FILE_CONFIRMED' || value === 'ARCHIVED'
    ? 'badge badge-success'
    : value === 'FILE_UPLOADED' || value === 'PROCESSING'
    ? 'badge badge-warning'
    : value === 'NO_FILE' || value === 'RECEIVED'
    ? 'badge badge-neutral'
    : 'badge badge-danger'
  return <span className={cls}>{value || 'N/A'}</span>
}
