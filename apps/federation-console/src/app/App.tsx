/**
 * TORQ Federation Console - Main App Component
 * Phase 1B - Application root with routing and providers
 */

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useFederationStore } from './store'

// Pages
import { DashboardPage } from '../pages/DashboardPage'
import { EnvelopePage } from '../pages/EnvelopePage'
import { ValidationPage } from '../pages/ValidationPage'
import { NodesPage } from '../pages/NodesPage'
import { StatusPage } from '../pages/StatusPage'
import { ProcessingPage } from '../pages/ProcessingPage'
import { ExchangeSimulatorPage } from '../pages/ExchangeSimulatorPage'

// Layout
import { AppLayout } from './AppLayout'

export default function App() {
  return (
    <BrowserRouter>
      <AppLayout>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/envelope" element={<EnvelopePage />} />
          <Route path="/validation" element={<ValidationPage />} />
          <Route path="/processing" element={<ProcessingPage />} />
          <Route path="/simulator" element={<ExchangeSimulatorPage />} />
          <Route path="/nodes" element={<NodesPage />} />
          <Route path="/status" element={<StatusPage />} />
        </Routes>
      </AppLayout>
    </BrowserRouter>
  )
}
