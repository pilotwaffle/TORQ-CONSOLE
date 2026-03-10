/**
 * Decision Summary Component
 *
 * Phase 5.2B: Observability + UI
 *
 * Displays final decision with confidence breakdown and dissent info.
 * Reads from backend decision endpoint - no local computation.
 */

import { useState, useEffect } from 'react';

interface DecisionSummaryProps {
  executionId: string;
}

interface DecisionData {
  execution_id: string;
  decision_policy: string;
  final_confidence: number;
  validator_status: string;
  validator_notes: string | null;
  has_dissent: boolean;
  dissenting_roles: string[];
  revision_count: number;
  escalation_count: number;
  confidence_breakdown: Record<string, number>;
}

export function DecisionSummary({ executionId }: DecisionSummaryProps) {
  const [decision, setDecision] = useState<DecisionData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    async function loadDecision() {
      try {
        setLoading(true);
        setError(null);

        const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
        const response = await fetch(`${apiUrl}/api/teams/executions/${executionId}/decision`);

        if (!response.ok) {
          throw new Error(`Failed to load decision: ${response.statusText}`);
        }

        const result: DecisionData = await response.json();

        if (mounted) {
          setDecision(result);
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

    loadDecision();

    return () => {
      mounted = false;
    };
  }, [executionId]);

  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 border border-gray-200 dark:border-gray-700">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/3 mb-3"></div>
          <div className="space-y-2">
            <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-full"></div>
            <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-2/3"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 rounded-lg shadow p-4 border border-red-200 dark:border-red-800">
        <p className="text-red-600 dark:text-red-400 text-sm">Error loading decision: {error}</p>
      </div>
    );
  }

  if (!decision) {
    return (
      <div className="bg-gray-50 dark:bg-gray-900 rounded-lg shadow p-4 border border-gray-200 dark:border-gray-700">
        <p className="text-sm text-gray-500 dark:text-gray-400">Decision pending...</p>
      </div>
    );
  }

  // Validator status color
  const getValidatorStatusColor = (status: string) => {
    switch (status) {
      case 'approved':
        return 'text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20';
      case 'blocked':
        return 'text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20';
      case 'escalated':
        return 'text-orange-600 dark:text-orange-400 bg-orange-50 dark:bg-orange-900/20';
      default:
        return 'text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-800';
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 border border-gray-200 dark:border-gray-700">
      <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
        Decision Summary
      </h3>

      {/* Final Confidence */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-1">
          <span className="text-sm text-gray-600 dark:text-gray-400">Final Confidence</span>
          <span className="text-2xl font-bold text-gray-900 dark:text-white">
            {(decision.final_confidence * 100).toFixed(0)}%
          </span>
        </div>
        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
          <div
            className="bg-blue-500 h-2 rounded-full transition-all"
            style={{ width: `${decision.final_confidence * 100}%` }}
          />
        </div>
      </div>

      {/* Validator Status */}
      <div className={`mb-4 p-3 rounded-lg ${getValidatorStatusColor(decision.validator_status)}`}>
        <div className="text-sm font-medium mb-1">Validator Status</div>
        <div className="text-lg font-semibold capitalize">{decision.validator_status}</div>
        {decision.validator_notes && (
          <div className="text-sm mt-2 opacity-80">{decision.validator_notes}</div>
        )}
      </div>

      {/* Decision Policy */}
      <div className="mb-4">
        <div className="text-sm text-gray-600 dark:text-gray-400">Decision Policy</div>
        <div className="text-sm font-medium text-gray-900 dark:text-white capitalize">
          {decision.decision_policy.replace('_', ' ')}
        </div>
      </div>

      {/* Confidence Breakdown */}
      {Object.keys(decision.confidence_breakdown).length > 0 && (
        <div className="mb-4">
          <div className="text-sm text-gray-600 dark:text-gray-400 mb-2">Confidence by Role</div>
          <div className="space-y-2">
            {Object.entries(decision.confidence_breakdown).map(([role, conf]) => (
              <div key={role} className="flex items-center justify-between">
                <span className="text-sm text-gray-700 dark:text-gray-300 capitalize">{role}</span>
                <span className="text-sm font-medium text-gray-900 dark:text-white">
                  {(conf * 100).toFixed(1)}%
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Dissent Warning */}
      {decision.has_dissent && (
        <div className="mb-4 p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded border border-yellow-200 dark:border-yellow-800">
          <div className="text-sm font-medium text-yellow-800 dark:text-yellow-300 mb-1">
            Dissent Registered
          </div>
          {decision.dissenting_roles.length > 0 && (
            <div className="text-xs text-yellow-700 dark:text-yellow-400">
              Dissenting roles: {decision.dissenting_roles.join(', ')}
            </div>
          )}
        </div>
      )}

      {/* Metadata */}
      <div className="flex gap-4 text-xs text-gray-500 dark:text-gray-400 pt-3 border-t border-gray-200 dark:border-gray-700">
        <span>Revisions: {decision.revision_count}</span>
        <span>Escalations: {decision.escalation_count}</span>
      </div>
    </div>
  );
}
