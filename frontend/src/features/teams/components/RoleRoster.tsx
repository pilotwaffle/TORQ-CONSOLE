/**
 * Role Roster Component
 *
 * Phase 5.2B: Observability + UI
 *
 * Displays status of each role (Lead, Researcher, Critic, Validator).
 * Reads from backend - no local state computation.
 */

import { useState, useEffect } from 'react';

interface RoleRosterProps {
  executionId: string;
}

interface RoleItem {
  role: string;
  display_name: string;
  status: 'pending' | 'active' | 'completed';
  last_action: string | null;
  last_action_round: number | null;
  confidence: number | null;
}

export function RoleRoster({ executionId }: RoleRosterProps) {
  const [roles, setRoles] = useState<RoleItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    async function loadRoles() {
      try {
        setLoading(true);
        setError(null);

        const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
        const response = await fetch(`${apiUrl}/api/teams/executions/${executionId}/roles`);

        if (!response.ok) {
          throw new Error(`Failed to load roles: ${response.statusText}`);
        }

        const result: RoleItem[] = await response.json();

        if (mounted) {
          setRoles(result);
        }
      } catch (err) {
        if (mounted) {
          setError(err instanceof Error ? err.message : 'Unknown error');
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }

    loadRoles();

    return () => {
      mounted = false;
    };
  }, [executionId]);

  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 border border-gray-200 dark:border-gray-700">
        <div className="space-y-3">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="animate-pulse flex items-center justify-between">
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-24"></div>
              <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-16"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 rounded-lg shadow p-4 border border-red-200 dark:border-red-800">
        <p className="text-red-600 dark:text-red-400 text-sm">Error loading role roster: {error}</p>
      </div>
    );
  }

  // Status icon
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return (
          <svg className="w-5 h-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
        );
      case 'active':
        return (
          <svg className="w-5 h-5 text-blue-500 animate-pulse" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001 1h1a1 1 0 001-1V8a1 1 0 00-.555-.894l-1-2A1 1 0 009.555 7.168z" clipRule="evenodd" />
          </svg>
        );
      default:
        return (
          <svg className="w-5 h-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm0-2a6 6 0 100-12 6 6 0 000 12z" clipRule="evenodd" />
          </svg>
        );
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 border border-gray-200 dark:border-gray-700">
      <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
        Team Roles
      </h3>

      <div className="space-y-2">
        {roles.map((role) => (
          <div
            key={role.role}
            className="flex items-center justify-between p-2 rounded bg-gray-50 dark:bg-gray-900"
          >
            {/* Role Name and Status */}
            <div className="flex items-center gap-3">
              {getStatusIcon(role.status)}
              <div>
                <div className="text-sm font-medium text-gray-900 dark:text-white">
                  {role.display_name}
                </div>
                {role.last_action && (
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    {role.last_action}
                  </div>
                )}
              </div>
            </div>

            {/* Confidence */}
            {role.confidence !== null && (
              <div className="text-right">
                <div className="text-xs text-gray-500 dark:text-gray-400">Confidence</div>
                <div className="text-sm font-semibold text-gray-900 dark:text-white">
                  {(role.confidence * 100).toFixed(0)}%
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
