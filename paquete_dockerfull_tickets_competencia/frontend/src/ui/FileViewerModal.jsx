import { useEffect, useRef, useState, useCallback } from 'react'

export default function FileViewerModal({ blob, fileName, mimeType, onClose }) {
  const [url, setUrl] = useState(null)
  const [zoom, setZoom] = useState(1)
  const [panX, setPanX] = useState(0)
  const [panY, setPanY] = useState(0)
  const [dragging, setDragging] = useState(false)
  const overlayRef = useRef(null)
  const imageWrapRef = useRef(null)
  const dragRef = useRef({ startX: 0, startY: 0, startPanX: 0, startPanY: 0 })
  const panRef = useRef({ x: 0, y: 0 })
  const zoomRef = useRef(1)
  const isImage = mimeType?.startsWith('image/')
  const isPdf = mimeType === 'application/pdf'

  panRef.current.x = panX
  panRef.current.y = panY
  zoomRef.current = zoom

  useEffect(() => {
    const u = URL.createObjectURL(blob)
    setUrl(u)
    return () => URL.revokeObjectURL(u)
  }, [blob])

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Escape') onClose()
  }, [onClose])

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [handleKeyDown])

  useEffect(() => {
    const el = overlayRef.current
    if (!el) return
    const handler = (e) => {
      e.preventDefault()
      if (!isImage) return
      const delta = e.deltaY > 0 ? -0.1 : 0.1
      const prevZoom = zoomRef.current
      const newZoom = Math.max(0.25, Math.min(3, prevZoom + delta))
      const rect = imageWrapRef.current?.getBoundingClientRect()
      if (rect) {
        const x = e.clientX - rect.left
        const y = e.clientY - rect.top
        const scale = newZoom / prevZoom
        setPanX((px) => x - scale * (x - px))
        setPanY((py) => y - scale * (y - py))
      }
      setZoom(newZoom)
    }
    el.addEventListener('wheel', handler, { passive: false })
    return () => el.removeEventListener('wheel', handler)
  }, [isImage, url])

  useEffect(() => {
    if (!dragging) return
    const handleMove = (e) => {
      const dx = e.clientX - dragRef.current.startX
      const dy = e.clientY - dragRef.current.startY
      setPanX(dragRef.current.startPanX + dx)
      setPanY(dragRef.current.startPanY + dy)
    }
    const handleUp = () => setDragging(false)
    document.addEventListener('mousemove', handleMove)
    document.addEventListener('mouseup', handleUp)
    return () => {
      document.removeEventListener('mousemove', handleMove)
      document.removeEventListener('mouseup', handleUp)
    }
  }, [dragging])

  const handleOverlayClick = (e) => {
    if (e.target === overlayRef.current) onClose()
  }

  const clampZoom = (z) => Math.max(0.25, Math.min(3, z))

  const zoomIn = () => setZoom((z) => clampZoom(z + 0.25))
  const zoomOut = () => setZoom((z) => clampZoom(z - 0.25))
  const zoomReset = () => { setZoom(1); setPanX(0); setPanY(0) }

  const handleMouseDown = (e) => {
    if (!isImage || zoomRef.current <= 1) return
    e.preventDefault()
    dragRef.current = { startX: e.clientX, startY: e.clientY, startPanX: panRef.current.x, startPanY: panRef.current.y }
    setDragging(true)
  }

  const handlePrint = () => {
    const printWindow = window.open('', '_blank')
    if (!printWindow) return
    if (isPdf) {
      printWindow.location.href = url
      printWindow.print()
    } else {
      printWindow.document.write(`<img src="${url}" style="max-width:100%"/>`)
      printWindow.document.close()
      printWindow.print()
    }
  }

  const handleDownload = () => {
    const a = document.createElement('a')
    a.href = url
    a.download = fileName || 'archivo'
    a.click()
  }

  if (!url) return null

  return (
    <div className="viewer-overlay" ref={overlayRef} onClick={handleOverlayClick}>
      <div className="viewer-container">
        <div className="viewer-toolbar">
          <div className="viewer-toolbar-left">
            <span className="viewer-filename">{fileName}</span>
            <span className="muted">{isPdf ? 'PDF' : mimeType}</span>
          </div>
          <div className="viewer-toolbar-center">
            {isImage && (
              <>
                <button className="btn btn-sm btn-secondary" onClick={zoomOut} title="Acercar">−</button>
                <span className="viewer-zoom-label">{Math.round(zoom * 100)}%</span>
                <button className="btn btn-sm btn-secondary" onClick={zoomIn} title="Alejar">+</button>
                <button className="btn btn-sm btn-secondary" onClick={zoomReset} title="Restablecer zoom">⊙</button>
              </>
            )}
          </div>
          <div className="viewer-toolbar-right">
            <button className="btn btn-sm btn-secondary" onClick={handlePrint} title="Imprimir">🖨</button>
            <button className="btn btn-sm btn-secondary" onClick={handleDownload} title="Descargar">⬇</button>
            <button className="btn btn-sm btn-secondary" onClick={onClose} title="Cerrar (Esc)">✕</button>
          </div>
        </div>
        <div className="viewer-body">
          {isImage ? (
            <div
              className="viewer-image-wrap"
              ref={imageWrapRef}
              onMouseDown={handleMouseDown}
              style={{
                cursor: zoom > 1 ? (dragging ? 'grabbing' : 'grab') : 'default',
                userSelect: dragging ? 'none' : undefined,
                touchAction: 'none',
              }}
            >
              <img
                src={url}
                alt={fileName}
                draggable={false}
                style={{
                  transform: `translate(${panX}px, ${panY}px) scale(${zoom})`,
                  transformOrigin: '0 0',
                }}
              />
            </div>
          ) : isPdf ? (
            <iframe src={url} title={fileName} className="viewer-pdf" />
          ) : (
            <iframe src={url} title={fileName} className="viewer-pdf" />
          )}
        </div>
      </div>
    </div>
  )
}
