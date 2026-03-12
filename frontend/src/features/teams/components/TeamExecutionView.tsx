/**
 * Team Execution View
 *
 * Phase 5.2B: Observability + UI
 *
 * Complete view of a team execution with all observability components.
 * Combines Card, Roles, Timeline, and Decision Summary.
 */

import { TeamExecutionCard } from './TeamExecutionCard';
import { RoleRoster } from './RoleRoster';
import { RoundTimeline } from './RoundTimeline';
import { DecisionSummary } from './DecisionSummary';

interface TeamExecutionViewProps {
  executionId: string;
  live?: boolean;
}

export function TeamExecutionView({ executionId, live = false }: TeamExecutionViewProps) {
  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Team Execution
        </h1>
        {live && (
          <span className="px-3 py-1 bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300 rounded-full text-sm font-medium">
            Live
          </span>
        )}
      </div>

      {/* Top Row: Card and Roles */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <TeamExecutionCard executionId={executionId} />
        <RoleRoster executionId={executionId} />
      </div>

      {/* Middle: Timeline */}
      <RoundTimeline executionId={executionId} live={live} />

      {/* Bottom: Decision Summary */}
      <DecisionSummary executionId={executionId} />
    </div>
  );
}

// Export individual components for granular usage
export { TeamExecutionCard } from './TeamExecutionCard';
export { RoleRoster } from './RoleRoster';
export { RoundTimeline } from './RoundTimeline';
export { DecisionSummary } from './DecisionSummary';
