/**
 * Phase 2 - Chat System Integrity
 *
 * Typing indicator component that shows when an agent is processing.
 * Displays a pulsing animation with agent name.
 */

import { useEffect, useState } from 'react';
import type { TypingState } from '@/types/chat';

interface TypingIndicatorProps {
  typingState: TypingState | null;
  className?: string;
}

/**
 * Single dot animation for typing indicator
 */
function TypingDot({ delay = 0 }: { delay?: number }) {
  return (
    <div
      className="w-2 h-2 bg-gray-400 rounded-full animate-pulse"
      style={{
        animationDelay: `${delay}ms`,
        animationDuration: '800ms',
      }}
    />
  );
}

/**
 * Typing Indicator Component
 *
 * Shows "Agent is thinking..." with animated dots
 */
export function TypingIndicator({ typingState, className = '' }: TypingIndicatorProps) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (typingState?.isTyping) {
      // Small delay before showing to avoid flicker
      const timer = setTimeout(() => setVisible(true), 300);
      return () => clearTimeout(timer);
    } else {
      setVisible(false);
    }
  }, [typingState?.isTyping]);

  if (!visible || !typingState?.isTyping) {
    return null;
  }

  return (
    <div className={`flex items-center gap-2 text-sm text-gray-500 py-2 ${className}`}>
      {/* Agent name */}
      <span className="font-medium">
        {typingState.agentName || 'Agent'} is thinking
      </span>

      {/* Animated dots */}
      <div className="flex items-center gap-1">
        <TypingDot delay={0} />
        <TypingDot delay={150} />
        <TypingDot delay={300} />
      </div>
    </div>
  );
}

/**
 * Compact typing indicator (for inline use)
 */
export function CompactTypingIndicator({
  typingState,
  className = '',
}: TypingIndicatorProps) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (typingState?.isTyping) {
      const timer = setTimeout(() => setVisible(true), 300);
      return () => clearTimeout(timer);
    } else {
      setVisible(false);
    }
  }, [typingState?.isTyping]);

  if (!visible || !typingState?.isTyping) {
    return null;
  }

  return (
    <div className={`inline-flex items-center gap-1.5 px-3 py-1.5 bg-gray-100 rounded-full ${className}`}>
      <div className="flex gap-0.5">
        <TypingDot delay={0} />
        <TypingDot delay={150} />
        <TypingDot delay={300} />
      </div>
      <span className="text-xs text-gray-600 ml-1">
        {typingState.agentName || 'Agent'}
      </span>
    </div>
  );
}

/**
 * Streaming content indicator (for active streaming)
 */
export function StreamingIndicator({
  active,
  className = '',
}: {
  active: boolean;
  className?: string;
}) {
  if (!active) {
    return null;
  }

  return (
    <div className={`flex items-center gap-2 text-xs text-gray-500 ${className}`}>
      <span className="relative flex h-2 w-2">
        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
        <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
      </span>
      <span>Streaming response...</span>
    </div>
  );
}

export default TypingIndicator;
