/**
 * Standalone Mode Badge
 *
 * Indicates when TORQ Console is running without the Marvin AI agent runtime.
 * Basic chat is available via HTTP fallback, but advanced multi-agent research is disabled.
 */

import React from 'react';
import { AlertTriangle, CloudOff } from 'lucide-react';

interface StandaloneModeBadgeProps {
  visible?: boolean;
}

export function StandaloneModeBadge({ visible = true }: StandaloneModeBadgeProps) {
  if (!visible) return null;

  return (
    <div className="flex items-center gap-2 px-3 py-1.5 bg-amber-500/10 border border-amber-500/30 rounded-lg">
      <CloudOff className="w-3.5 h-3.5 text-amber-400" />
      <span className="text-xs font-medium text-amber-200">Standalone Mode</span>
      <span className="text-xs text-amber-300/70">•</span>
      <span className="text-xs text-amber-300/70">AI Runtime Unavailable</span>
    </div>
  );
}

/**
 * Compact inline standalone mode indicator
 */
interface StandaloneModeInlineProps {
  visible?: boolean;
}

export function StandaloneModeInline({ visible = true }: StandaloneModeInlineProps) {
  if (!visible) return null;

  return (
    <div className="flex items-center gap-2 px-3 py-2 bg-amber-500/5 border border-amber-500/20 rounded-lg">
      <AlertTriangle className="w-4 h-4 text-amber-400" />
      <div className="flex-1">
        <p className="text-xs font-medium text-amber-200">
          TORQ Console is running in standalone mode
        </p>
        <p className="text-xs text-amber-300/70 mt-0.5">
          Basic chat is available, but advanced multi-agent research requires Marvin AI runtime.
        </p>
      </div>
    </div>
  );
}
