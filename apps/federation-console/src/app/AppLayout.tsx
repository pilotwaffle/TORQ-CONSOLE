/**
 * TORQ Federation Console - Main Layout
 * Phase 1B - App shell with navigation and header
 */

import { Link, useLocation } from 'react-router-dom'
import { clsx } from 'clsx'
import { useFederationStore } from './store'

const navItems = [
  { path: '/dashboard', label: 'Dashboard', icon: '📊' },
  { path: '/envelope', label: 'Envelope', icon: '✉️' },
  { path: '/validation', label: 'Validation', icon: '🛡️' },
  { path: '/processing', label: 'Processing', icon: '⚙️' },
  { path: '/simulator', label: 'Simulator', icon: '🔬' },
  { path: '/nodes', label: 'Nodes', icon: '🔗' },
  { path: '/status', label: 'Status', icon: '📡' },
]

interface AppLayoutProps {
  children: React.ReactNode
}

export function AppLayout({ children }: AppLayoutProps) {
  const location = useLocation()
  const { federationStatus, loading } = useFederationStore()

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-torq-900 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo & Title */}
            <div className="flex items-center gap-3">
              <div className="text-2xl">⚡</div>
              <div>
                <h1 className="text-xl font-bold">TORQ Federation Console</h1>
                <p className="text-xs text-torq-300">Phase 1B</p>
              </div>
            </div>

            {/* Status Badge */}
            <div className="flex items-center gap-4">
              {federationStatus && (
                <div className="text-right text-sm">
                  <div className="text-torq-300">Protocol v{federationStatus.protocolVersion}</div>
                  <div className="flex items-center gap-2">
                    <span>{federationStatus.activeConnections} nodes</span>
                    <span className={clsx(
                      'inline-block w-2 h-2 rounded-full',
                      loading ? 'bg-yellow-400' : 'bg-green-400'
                    )} />
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>
    </div>
  )
}

function NavItem({ path, label, icon, current }: {
  path: string
  label: string
  icon: string
  current: boolean
}) {
  return (
    <Link
      to={path}
      className={clsx(
        'flex items-center gap-2 px-4 py-2 rounded-lg transition-colors',
        current
          ? 'bg-torq-800 text-white'
          : 'text-torq-300 hover:bg-torq-800 hover:text-white'
      )}
    >
      <span>{icon}</span>
      <span>{label}</span>
    </Link>
  )
}
