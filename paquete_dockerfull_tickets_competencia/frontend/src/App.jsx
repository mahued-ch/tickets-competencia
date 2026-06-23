import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './state/AuthContext'
import AppLayout from './ui/AppLayout'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import TicketsPage from './pages/TicketsPage'
import TicketDetailPage from './pages/TicketDetailPage'
import BatchesPage from './pages/BatchesPage'
import BatchDetailPage from './pages/BatchDetailPage'
import UsersPage from './pages/UsersPage'
import SupervisorDashboardPage from './pages/SupervisorDashboardPage'
import AuditPage from './pages/AuditPage'
import CatalogsPage from './pages/CatalogsPage'
import EnrichmentReviewPage from './pages/EnrichmentReviewPage'
import ScanTicketsPage from './pages/ScanTicketsPage'
import ScanTicketNewPage from './pages/ScanTicketNewPage'
import ScanTicketEditPage from './pages/ScanTicketEditPage'

function ProtectedRoute({ children }) {
  const { currentUser } = useAuth()
  if (!currentUser) return <Navigate to="/login" replace />
  return children
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="tickets" element={<TicketsPage />} />
        <Route path="tickets/:ticketId" element={<TicketDetailPage />} />
        <Route path="coverage" element={<SupervisorDashboardPage />} />
        <Route path="integration/batches" element={<BatchesPage />} />
        <Route path="integration/batches/:batchId" element={<BatchDetailPage />} />
        <Route path="admin/users" element={<UsersPage />} />
        <Route path="audit" element={<AuditPage />} />
        <Route path="admin/catalogs" element={<CatalogsPage />} />
        <Route path="tickets/:ticketId/enrichment-review" element={<EnrichmentReviewPage />} />
        <Route path="scan-tickets" element={<ScanTicketsPage />} />
        <Route path="scan-tickets/new" element={<ScanTicketNewPage />} />
        <Route path="scan-tickets/:ticketId" element={<ScanTicketEditPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}
