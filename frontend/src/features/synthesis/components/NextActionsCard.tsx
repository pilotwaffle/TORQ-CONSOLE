/**
 * NextActionsCard - Displays recommended next actions
 */

import { SynthesisType, useLatestSynthesis } from "../api";

interface Props {
  workspaceId: string;
  className?: string;
}

const priorityColors = {
  high: "bg-red-50 text-red-700 border-red-200",
  medium: "bg-yellow-50 text-yellow-700 border-yellow-200",
  low: "bg-green-50 text-green-700 border-green-200",
};

export function NextActionsCard({ workspaceId, className = "" }: Props) {
  const { data: synthesis, isLoading } = useLatestSynthesis(
    workspaceId,
    SynthesisType.NEXT_ACTIONS,
    { enabled: !!workspaceId }
  );

  if (isLoading) {
    return (
      <div className={`p-4 bg-gray-50 rounded-lg ${className}`}>
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-2"></div>
          <div className="h-3 bg-gray-200 rounded w-3/4 mb-1"></div>
        </div>
      </div>
    );
  }

  const actions = synthesis?.content?.next_actions || [];

  if (!actions.length) {
    return null;
  }

  return (
    <div className={`p-4 bg-white rounded-lg border border-gray-200 ${className}`}>
      <h3 className="text-sm font-medium text-gray-700 mb-3">Recommended Actions</h3>
      <div className="space-y-2">
        {actions.map((action: any, i: number) => (
          <div
            key={i}
            className={`p-3 rounded border ${
              priorityColors[action.priority as keyof typeof priorityColors] ||
              priorityColors.medium
            }`}
          >
            <div className="flex items-start justify-between">
              <span className="text-sm font-medium">{action.action}</span>
              <span className="text-xs uppercase px-2 py-0.5 rounded bg-white bg-opacity-50">
                {action.priority}
              </span>
            </div>
            <p className="text-xs mt-1 opacity-75">{action.reason}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
