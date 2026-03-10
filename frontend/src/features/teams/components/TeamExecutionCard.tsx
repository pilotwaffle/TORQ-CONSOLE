/**
 * Team Execution Card Component
 *
 * Phase 5.2B: Observability + UI
 *
 * Displays team execution summary for control surface dashboard.
 * Reads from backend view model - no local computation.
 */

import { useState, useEffect } from 'react';

interface TeamExecutionCardProps {
  executionId: string;
}

interface TeamExecutionCardData {
  execution_id: string;
  team_id: string;
  team_name: string;
  pattern: string;
  rounds_total: number;
  rounds_completed: number;
  status: string;
  confidence: number;
  started_at: string | null;
  completed_at: string | null;
}

export function TeamExecutionCard({ executionId }: TeamExecutionCardProps) {
  const [data, setData] = useState<TeamExecutionCardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    async function loadCard() {
      try {
        setLoading(true);
        setError(null);

        const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
        const response = await fetch(`${apiUrl}/api/teams/executions/${executionId}/card`);

        if (!response.ok) {
          throw new Error(`Failed to load card: ${response.statusText}`);
        }

        const result: TeamExecutionCardData = await response.json();

        if (mounted) {
          setData(result);
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

    loadCard();

    return () => {
      mounted = false;
    };
  }, [executionId]);

  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 border border-gray-200 dark:border-gray-700">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/3 mb-3"></div>
          <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/2 mb-2"></div>
          <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/4"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 rounded-lg shadow p-4 border border-red-200 dark:border-red-800">
        <p className="text-red-600 dark:text-red-400 text-sm">Error loading execution card: {error}</p>
      </div>
    );
  }

  if (!data) {
    return null;
  }

  // Status badge color
  const statusColors: Record<string, string> = {
    created: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
    initialized: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300',
    running: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300',
    completed: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
    failed: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300',
    blocked: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300',
  };

  const statusBadge = statusColors[data.status] || statusColors.created;

  // Confidence color
  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.85) return 'text-green-600 dark:text-green-400';
    if (confidence >= 0.70) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-red-600 dark:text-red-400';
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 border border-gray-200 dark:border-gray-700">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          {data.team_name}
        </h3>
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusBadge}`}>
          {data.status}
        </span>
      </div>

      {/* Pattern */}
      <div className="text-xs text-gray-500 dark:text-gray-400 mb-3">
        Pattern: <span className="font-medium">{data.pattern}</span>
      </div>

      {/* Rounds Progress */}
      <div className="mb-3">
        <div className="flex justify-between text-xs text-gray-600 dark:text-gray-400 mb-1">
          <span>Progress</span>
          <span>{data.rounds_completed} / {data.rounds_total} rounds</span>
        </div>
        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
          <div
            className="bg-blue-500 h-2 rounded-full transition-all"
            style={{ width: `${(data.rounds_completed / data.rounds_total) * 100}%` }}
          />
        </div>
      </div>

      {/* Confidence */}
      <div className="flex items-center justify-between">
        <span className="text-sm text-gray-600 dark:text-gray-400">Confidence</span>
        <span className={`text-lg font-bold ${getConfidenceColor(data.confidence)}`}>
          {(data.confidence * 100).toFixed(0)}%
        </span>
      </div>

      {/* Timestamps */}
      {(data.started_at || data.completed_at) && (
        <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700 text-xs text-gray-500 dark:text-gray-400">
          {data.started_at && (
            <div>Started: {new Date(data.started_at).toLocaleTimeString()}</div>
          )}
          {data.completed_at && (
            <div>Completed: {new Date(data.completed_at).toLocaleTimeString()}</div>
          )}
        </div>
      )}

      {/* Execution ID */}
      <div className="mt-2 text-xs text-gray-400 dark:text-gray-500 font-mono">
        {data.execution_id.slice(0, 8)}...
      </div>
    </div>
  );
}
