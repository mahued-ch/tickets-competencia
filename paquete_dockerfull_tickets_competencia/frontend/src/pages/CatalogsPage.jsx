import { useEffect, useState, useCallback } from 'react'
import {
  listCompetitorStoresApi, createCompetitorStoreApi, updateCompetitorStoreApi, deleteCompetitorStoreApi,
  listChedrauiProductsApi, createChedrauiProductApi, updateChedrauiProductApi, deleteChedrauiProductApi,
  listCompetitorMappingsApi, createCompetitorMappingApi, updateCompetitorMappingApi, deleteCompetitorMappingApi,
  listNearbyStoresApi, createNearbyStoreApi, updateNearbyStoreApi, deleteNearbyStoreApi,
} from '../services/api'
import DataTable from '../ui/DataTable'
import StatusBadge from '../ui/StatusBadge'

const TABS = [
  { key: 'competitor-stores', label: 'Tiendas Competencia' },
  { key: 'chedraui-products', label: 'Productos Chedraui' },
  { key: 'competitor-mappings', label: 'Mapeo Productos' },
  { key: 'nearby-stores', label: 'Tiendas Cercanas' },
]

function buildColumns(fields) {
  return fields.map((f) => {
    if (typeof f === 'string') return { key: f, title: f }
    return f
  })
}

function CrudTable({ columns, fetchFn, createFn, updateFn, deleteFn, formFields }) {
  const [rows, setRows] = useState([])
  const [error, setError] = useState('')
  const [editing, setEditing] = useState(null)
  const [form, setForm] = useState({})

  const load = useCallback(() => {
    fetchFn()
      .then((res) => setRows(res.data?.data || []))
      .catch((e) => setError(e?.response?.data?.detail || 'Error al cargar'))
  }, [fetchFn])

  useEffect(() => { load() }, [load])

  function resetForm() {
    setForm({})
    setEditing(null)
  }

  function handleEdit(row) {
    setForm({ ...row })
    setEditing(row[Object.keys(formFields[0])[0]] || row[formFields[0].key])
  }

  function handleSave() {
    const payload = { ...form }
    delete payload[formFields.find((f) => f.pk)?.key]
    const promise = editing
      ? updateFn(editing, payload)
      : createFn(payload)
    promise.then(() => { resetForm(); load() })
      .catch((e) => setError(e?.response?.data?.detail || 'Error al guardar'))
  }

  function handleDelete(id) {
    if (!confirm('¿Eliminar este registro?')) return
    deleteFn(id).then(load).catch((e) => setError(e?.response?.data?.detail || 'Error al eliminar'))
  }

  const colDefs = buildColumns(columns)
  const pkField = formFields.find((f) => f.pk)

  return (
    <div>
      {error && <p className="error-text">{error}</p>}
      <div className="card" style={{ marginBottom: 16, padding: 16 }}>
        <div className="section-title">{editing ? 'Editar' : 'Nuevo'}</div>
        <div className="row gap-8" style={{ flexWrap: 'wrap' }}>
          {formFields.map((f) => (
            <input
              key={f.key}
              placeholder={f.label}
              value={form[f.key] ?? ''}
              onChange={(e) => setForm({ ...form, [f.key]: f.type === 'number' ? Number(e.target.value) || null : e.target.value })}
              type={f.type === 'number' ? 'number' : 'text'}
              step={f.step}
              style={{ width: f.width || 150 }}
              disabled={f.pk}
            />
          ))}
          <button className="btn btn-primary btn-sm" onClick={handleSave} disabled={!formFields.some((f) => !f.pk && (form[f.key] ?? '') !== '')}>
            {editing ? 'Actualizar' : 'Crear'}
          </button>
          {editing && <button className="btn btn-secondary btn-sm" onClick={resetForm}>Cancelar</button>}
        </div>
      </div>
      <DataTable
        columns={colDefs}
        rows={rows}
        emptyMessage="Sin registros"
        actions={(r) => (
          <div className="row gap-4">
            <button className="link-btn" onClick={() => handleEdit(r)}>Editar</button>
            <button className="link-btn" style={{ color: '#b91c1c' }} onClick={() => handleDelete(pkField ? r[pkField.key] : r[columns[0]])}>Eliminar</button>
          </div>
        )}
      />
    </div>
  )
}

export default function CatalogsPage() {
  const [tab, setTab] = useState('competitor-stores')

  const tables = {
    'competitor-stores': {
      columns: ['storeId', 'businessCode', 'storeCode', 'storeName', 'address', { key: 'isActive', title: 'Activo', render: (r) => <StatusBadge value={r.isActive ? 'Si' : 'No'} /> }],
      fetchFn: listCompetitorStoresApi,
      createFn: createCompetitorStoreApi,
      updateFn: updateCompetitorStoreApi,
      deleteFn: deleteCompetitorStoreApi,
      formFields: [
        { key: 'businessCode', label: 'Cadena', width: 100 },
        { key: 'storeCode', label: 'Tienda', width: 100 },
        { key: 'storeName', label: 'Nombre', width: 200 },
        { key: 'address', label: 'Dirección', width: 300 },
        { key: 'storeId', label: 'ID', pk: true },
      ],
    },
    'chedraui-products': {
      columns: ['productId', 'sku', 'upc', 'description', { key: 'listPrice', title: 'Precio' }, 'departmentCode', 'subDepartmentCode', 'classCode', 'subclassCode', { key: 'isActive', title: 'Activo', render: (r) => <StatusBadge value={r.isActive ? 'Si' : 'No'} /> }],
      fetchFn: listChedrauiProductsApi,
      createFn: createChedrauiProductApi,
      updateFn: updateChedrauiProductApi,
      deleteFn: deleteChedrauiProductApi,
      formFields: [
        { key: 'sku', label: 'SKU', width: 100 },
        { key: 'upc', label: 'UPC', width: 120 },
        { key: 'description', label: 'Descripción', width: 250 },
        { key: 'listPrice', label: 'Precio', type: 'number', step: 0.01, width: 100 },
        { key: 'departmentCode', label: 'Depto', type: 'number', width: 70 },
        { key: 'subDepartmentCode', label: 'SubDepto', type: 'number', width: 80 },
        { key: 'classCode', label: 'Clase', type: 'number', width: 70 },
        { key: 'subclassCode', label: 'Subclase', type: 'number', width: 80 },
        { key: 'productId', label: 'ID', pk: true },
      ],
    },
    'competitor-mappings': {
      columns: ['mappingId', 'businessCode', 'competitorCode', 'competitorDescription', 'chedrauiProductId', 'matchType', { key: 'confidence', title: 'Confianza' }, { key: 'isActive', title: 'Activo', render: (r) => <StatusBadge value={r.isActive ? 'Si' : 'No'} /> }],
      fetchFn: listCompetitorMappingsApi,
      createFn: createCompetitorMappingApi,
      updateFn: updateCompetitorMappingApi,
      deleteFn: deleteCompetitorMappingApi,
      formFields: [
        { key: 'businessCode', label: 'Cadena', width: 100 },
        { key: 'competitorCode', label: 'Código Comp.', width: 120 },
        { key: 'competitorDescription', label: 'Descripción Comp.', width: 250 },
        { key: 'chedrauiProductId', label: 'Producto ID', type: 'number', width: 100 },
        { key: 'matchType', label: 'Tipo Match', width: 100 },
        { key: 'confidence', label: 'Confianza', type: 'number', step: 0.01, width: 100 },
        { key: 'mappingId', label: 'ID', pk: true },
      ],
    },
    'nearby-stores': {
      columns: ['nearbyId', 'businessCode', 'storeCode', 'nearbyChedrauiStoreCode', { key: 'distanceKm', title: 'Dist (km)' }, { key: 'isActive', title: 'Activo', render: (r) => <StatusBadge value={r.isActive ? 'Si' : 'No'} /> }],
      fetchFn: listNearbyStoresApi,
      createFn: createNearbyStoreApi,
      updateFn: updateNearbyStoreApi,
      deleteFn: deleteNearbyStoreApi,
      formFields: [
        { key: 'businessCode', label: 'Cadena', width: 100 },
        { key: 'storeCode', label: 'Tienda Comp.', width: 100 },
        { key: 'nearbyChedrauiStoreCode', label: 'Tienda Chedraui', width: 130 },
        { key: 'distanceKm', label: 'Dist (km)', type: 'number', step: 0.1, width: 100 },
        { key: 'nearbyId', label: 'ID', pk: true },
      ],
    },
  }

  const current = tables[tab]

  return (
    <div className="page">
      <h1>Catálogos</h1>
      <div className="row gap-8" style={{ marginBottom: 16 }}>
        {TABS.map((t) => (
          <button
            key={t.key}
            className={tab === t.key ? 'btn' : 'btn btn-secondary'}
            onClick={() => setTab(t.key)}
          >
            {t.label}
          </button>
        ))}
      </div>
      <CrudTable
        key={tab}
        columns={current.columns}
        fetchFn={current.fetchFn}
        createFn={current.createFn}
        updateFn={current.updateFn}
        deleteFn={current.deleteFn}
        formFields={current.formFields}
      />
    </div>
  )
}
