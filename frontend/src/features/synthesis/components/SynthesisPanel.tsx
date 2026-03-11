/**
 * SynthesisPanel - Main container for all synthesis cards
 */

import { SummaryCard } from "./SummaryCard";
import { InsightsCard } from "./InsightsCard";
import { NextActionsCard } from "./NextActionsCard";

interface Props {
  workspaceId: string;
  className?: string;
}

export function SynthesisPanel({ workspaceId, className = "" }: Props) {
  return (
    <div className={`space-y-4 ${className}`}>
      <SummaryCard workspaceId={workspaceId} />
      <InsightsCard workspaceId={workspaceId} />
      <NextActionsCard workspaceId={workspaceId} />
    </div>
  );
}
