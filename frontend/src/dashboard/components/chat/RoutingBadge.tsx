/**
 * RoutingBadge — Collapsible per-message routing transparency
 * 
 * Shows which agent handled the query, confidence level,
 * capabilities used, and orchestration mode.
 * 
 * PRD Section 6h: Below each assistant message.
 * Collapsed: [▸ agent_name │ confidence]
 * Expanded: intent, complexity, capabilities, model, response_time
 */

import { useState } from 'react';
import type { ChatMetadata, RoutingDecision } from '@/types/api';

interface RoutingBadgeProps {
  routing: RoutingDecision | null;
  metadata?: ChatMetadata;
}

export default function RoutingBadge({ routing, metadata }: RoutingBadgeProps) {
  const [expanded, setExpanded] = useState(false);

  if (!routing && !metadata) return null;

  const agentName = metadata?.agent_used || routing?.primary_agent || 'unknown';
  const capabilities = routing?.capabilities || metadata?.capabilities || [];
  const mode = metadata?.mode || 'single_agent';
  const success = metadata?.success !== false;
  const usedTools = metadata?.used_tools || false;

  // Format agent display name
  const displayName = agentName
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c: string) => c.toUpperCase())
    .replace('Marvin ', '')
    .replace(' (With Tools)', ' ⚡')
    .replace(' (Fallback)', ' ⚠');

  return (
    <div className="torq-routing-badge">
      <button
        onClick={() => setExpanded(!expanded)}
        className="torq-routing-toggle"
      >
        <span className="torq-routing-chevron">{expanded ? '▾' : '▸'}</span>
        <span className="torq-routing-agent">{displayName}</span>
        <span className="torq-routing-divider">│</span>
        <span className={`torq-routing-status ${success ? 'success' : 'error'}`}>
          {success ? '✓' : '✗'}
        </span>
        {usedTools && <span className="torq-routing-tools">🔧</span>}
        <span className="torq-routing-mode">{mode.replace(/_/g, ' ')}</span>
      </button>

      {expanded && (
        <div className="torq-routing-details">
          {capabilities.length > 0 && (
            <div className="torq-routing-row">
              <span className="torq-routing-label">Capabilities</span>
              <div className="torq-routing-caps">
                {capabilities.map((cap: string) => (
                  <span key={cap} className="torq-routing-cap-tag">
                    {cap.replace(/_/g, ' ')}
                  </span>
                ))}
              </div>
            </div>
          )}
          <div className="torq-routing-row">
            <span className="torq-routing-label">Mode</span>
            <span className="torq-routing-value">{mode.replace(/_/g, ' ')}</span>
          </div>
          {metadata?.agent_used && (
            <div className="torq-routing-row">
              <span className="torq-routing-label">Agent</span>
              <span className="torq-routing-value">{metadata.agent_used}</span>
            </div>
          )}
          {usedTools && (
            <div className="torq-routing-row">
              <span className="torq-routing-label">Tools</span>
              <span className="torq-routing-value">Web search / research tools active</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
