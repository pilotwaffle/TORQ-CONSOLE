/**
 * InsightsCard - Displays insights from workspace reasoning
 */

import { SynthesisType, useLatestSynthesis } from "../api";

interface Props {
  workspaceId: string;
  className?: string;
}

export function InsightsCard({ workspaceId, className = "" }: Props) {
  const { data: synthesis, isLoading } = useLatestSynthesis(workspaceId, SynthesisType.INSIGHTS, {
    enabled: !!workspaceId,
  });

  if (isLoading) {
    return (
      <div className={`p-4 bg-gray-50 rounded-lg ${className}`}>
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-2"></div>
          <div className="h-3 bg-gray-200 rounded w-1/2 mb-1"></div>
          <div className="h-3 bg-gray-200 rounded w-2/3"></div>
        </div>
      </div>
    );
  }

  const insights = synthesis?.content?.insights || [];

  if (!insights.length) {
    return null;
  }

  return (
    <div className={`p-4 bg-white rounded-lg border border-gray-200 ${className}`}>
      <h3 className="text-sm font-medium text-gray-700 mb-3">Key Insights</h3>
      <ul className="space-y-2">
        {insights.map((insight: string, i: number) => (
          <li key={i} className="flex items-start">
            <span className="text-purple-500 mr-2">•</span>
            <span className="text-sm text-gray-600">{insight}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
