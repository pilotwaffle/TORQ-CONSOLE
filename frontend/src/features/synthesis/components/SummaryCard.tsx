/**
 * SummaryCard - Displays workspace summary synthesis
 */

import { SynthesisType, useLatestSynthesis, useLazySynthesis } from "../api";

interface Props {
  workspaceId: string;
  className?: string;
}

export function SummaryCard({ workspaceId, className = "" }: Props) {
  const { synthesis, isLoading, generate } = useLazySynthesis(
    workspaceId,
    SynthesisType.SUMMARY,
    { autoGenerate: true }
  );

  if (isLoading) {
    return (
      <div className={`p-4 bg-gray-50 rounded-lg ${className}`}>
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-2"></div>
          <div className="h-3 bg-gray-200 rounded w-3/4"></div>
        </div>
      </div>
    );
  }

  const summary = synthesis?.content?.summary || synthesis?.content?.text;

  if (!summary) {
    return (
      <div className={`p-4 bg-gray-50 rounded-lg ${className}`}>
        <h3 className="text-sm font-medium text-gray-500 mb-2">Summary</h3>
        <p className="text-sm text-gray-400">No summary available yet.</p>
        <button
          onClick={() => generate()}
          className="mt-2 text-xs text-purple-600 hover:text-purple-700"
        >
          Generate Summary
        </button>
      </div>
    );
  }

  return (
    <div className={`p-4 bg-white rounded-lg border border-gray-200 ${className}`}>
      <h3 className="text-sm font-medium text-gray-700 mb-2">Summary</h3>
      <p className="text-sm text-gray-600 whitespace-pre-wrap">{summary}</p>
      {synthesis && (
        <div className="mt-2 text-xs text-gray-400">
          v{synthesis.version} • {new Date(synthesis.created_at).toLocaleTimeString()}
        </div>
      )}
    </div>
  );
}
