/**
 * TORQ Federation Console - Router Configuration
 * Phase 1B - Route definitions and navigation
 */

import { Routes, Route } from 'react-router-dom'
import { DashboardPage } from '../pages/DashboardPage'
import { EnvelopePage } from '../pages/EnvelopePage'
import { ValidationPage } from '../pages/ValidationPage'
import { NodesPage } from '../pages/NodesPage'
import { StatusPage } from '../pages/StatusPage'

export function AppRouter() {
  return (
    <Routes>
      <Route path="/" element={<DashboardPage />} />
      <Route path="/dashboard" element={<DashboardPage />} />
      <Route path="/envelope" element={<EnvelopePage />} />
      <Route path="/validation" element={<ValidationPage />} />
      <Route path="/nodes" element={<NodesPage />} />
      <Route path="/status" element={<StatusPage />} />
    </Routes>
  )
}
