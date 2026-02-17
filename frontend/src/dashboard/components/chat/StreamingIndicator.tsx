/**
 * StreamingIndicator — Pulsing dot for TopNav
 * Shows when the backend is processing a query.
 */

interface StreamingIndicatorProps {
  isActive: boolean;
  label?: string;
}

export default function StreamingIndicator({ isActive, label }: StreamingIndicatorProps) {
  if (!isActive) return null;

  return (
    <div className="torq-streaming-indicator">
      <span className="torq-streaming-dot" />
      <span className="torq-streaming-label">{label || 'Processing...'}</span>
    </div>
  );
}
