/**
 * Operator Control Surface - Utility Functions
 *
 * Helper functions for formatting dates, times, percentages,
 * and other display values for the control surface UI.
 */

// ============================================================================
// Date/Time Formatting
// ============================================================================

/**
 * Format a timestamp to a human-readable date and time
 */
export function formatDateTime(isoString: string | null | undefined): string {
  if (!isoString) return "-";

  const date = new Date(isoString);

  // Check for invalid date
  if (isNaN(date.getTime())) return "-";

  return date.toLocaleString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/**
 * Format a timestamp to a relative time (e.g., "2 hours ago")
 */
export function formatRelativeTime(isoString: string | null | undefined): string {
  if (!isoString) return "-";

  const date = new Date(isoString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffSecs < 60) return "just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return formatDateTime(isoString);
}

/**
 * Format a duration in seconds to human-readable form
 */
export function formatDuration(seconds: number | null | undefined): string {
  if (!seconds) return "-";

  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);

  if (hours > 0) {
    return `${hours}h ${minutes}m ${secs}s`;
  } else if (minutes > 0) {
    return `${minutes}m ${secs}s`;
  } else {
    return `${secs}s`;
  }
}

// ============================================================================
// Progress Formatting
// ============================================================================

/**
 * Format progress as a percentage
 */
export function formatProgressPercent(
  completed: number,
  total: number
): string {
  if (!total || total === 0) return "0%";
  return `${Math.round((completed / total) * 100)}%`;
}

/**
 * Format progress as "X/Y"
 */
export function formatProgressCount(completed: number, total: number): string {
  return total ? `${completed}/${total}` : "0/0";
}

/**
 * Get color class based on progress percentage
 */
export function getProgressColor(percent: number): string {
  if (percent >= 100) return "text-green-600";
  if (percent >= 75) return "text-blue-600";
  if (percent >= 50) return "text-yellow-600";
  if (percent >= 25) return "text-orange-600";
  return "text-red-600";
}

// ============================================================================
// Status Formatting
// ============================================================================

/**
 * Get status badge styling
 */
export function getStatusBadgeStyle(status: string): {
  bgColor: string;
  textColor: string;
  label: string;
} {
  const statusMap: Record<string, { bgColor: string; textColor: string; label: string }> = {
    draft: { bgColor: "bg-gray-100", textColor: "text-gray-700", label: "Draft" },
    planned: { bgColor: "bg-blue-100", textColor: "text-blue-700", label: "Planned" },
    scheduled: { bgColor: "bg-purple-100", textColor: "text-purple-700", label: "Scheduled" },
    running: { bgColor: "bg-yellow-100", textColor: "text-yellow-700", label: "Running" },
    paused: { bgColor: "bg-orange-100", textColor: "text-orange-700", label: "Paused" },
    completed: { bgColor: "bg-green-100", textColor: "text-green-700", label: "Completed" },
    failed: { bgColor: "bg-red-100", textColor: "text-red-700", label: "Failed" },
    cancelled: { bgColor: "bg-gray-100", textColor: "text-gray-700", label: "Cancelled" },
  };

  return (
    statusMap[status] || {
      bgColor: "bg-gray-100",
      textColor: "text-gray-700",
      label: status,
    }
  );
}

/**
 * Get workstream health badge styling
 */
export function getHealthBadgeStyle(health: string): {
  bgColor: string;
  textColor: string;
  icon: string;
} {
  const healthMap: Record<string, { bgColor: string; textColor: string; icon: string }> = {
    healthy: {
      bgColor: "bg-green-100",
      textColor: "text-green-700",
      icon: "✓",
    },
    at_risk: {
      bgColor: "bg-yellow-100",
      textColor: "text-yellow-700",
      icon: "⚠",
    },
    failed: {
      bgColor: "bg-red-100",
      textColor: "text-red-700",
      icon: "✗",
    },
    idle: {
      bgColor: "bg-gray-100",
      textColor: "text-gray-700",
      icon: "○",
    },
  };

  return (
    healthMap[health] || {
      bgColor: "bg-gray-100",
      textColor: "text-gray-700",
      icon: "?",
    }
  );
}

/**
 * Get event severity badge styling
 */
export function getSeverityBadgeStyle(severity: string): {
  bgColor: string;
  textColor: string;
  icon: string;
} {
  const severityMap: Record<
    string,
    { bgColor: string; textColor: string; icon: string }
  > = {
    info: {
      bgColor: "bg-blue-100",
      textColor: "text-blue-700",
      icon: "ⓘ",
    },
    warning: {
      bgColor: "bg-yellow-100",
      textColor: "text-yellow-700",
      icon: "⚠",
    },
    error: {
      bgColor: "bg-red-100",
      textColor: "text-red-700",
      icon: "✖",
    },
  };

  return (
    severityMap[severity] || {
      bgColor: "bg-gray-100",
      textColor: "text-gray-700",
      icon: "•",
    }
  );
}

// ============================================================================
// Text Truncation
// ============================================================================

/**
 * Truncate text to a maximum length with ellipsis
 */
export function truncateText(text: string | null | undefined, maxLength: number = 60): string {
  if (!text) return "";
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength - 3) + "...";
}

/**
 * Truncate words to a maximum word count
 */
export function truncateWords(text: string | null | undefined, maxWords: number = 20): string {
  if (!text) return "";
  const words = text.split(" ");
  if (words.length <= maxWords) return text;
  return words.slice(0, maxWords).join(" ") + "...";
}

// ============================================================================
// ID Formatting
// ============================================================================

/**
 * Shorten a UUID for display
 */
export function shortenId(id: string | null | undefined, length: number = 8): string {
  if (!id) return "-";
  return id.substring(0, length);
}

/**
 * Format a node type for display
 */
export function formatNodeType(type: string): string {
  const typeMap: Record<string, string> = {
    objective: "Objective",
    task: "Task",
    decision: "Decision",
    evidence: "Evidence",
    deliverable: "Deliverable",
  };
  return typeMap[type] || type;
}

/**
 * Format a mission type for display
 */
export function formatMissionType(type: string): string {
  const typeMap: Record<string, string> = {
    analysis: "Analysis",
    planning: "Planning",
    evaluation: "Evaluation",
    design: "Design",
    transformation: "Transformation",
  };
  return typeMap[type] || type;
}

// ============================================================================
// Confidence Formatting
// ============================================================================

/**
 * Format confidence score as percentage
 */
export function formatConfidence(confidence: number): string {
  return `${Math.round(confidence * 100)}%`;
}

/**
 * Get confidence color based on score
 */
export function getConfidenceColor(confidence: number): string {
  if (confidence >= 0.9) return "text-green-600";
  if (confidence >= 0.7) return "text-blue-600";
  if (confidence >= 0.5) return "text-yellow-600";
  return "text-red-600";
}

// ============================================================================
// Array Utilities
// ============================================================================

/**
 * Safely get array length
 */
export function getArrayLength<T>(arr: T[] | null | undefined): number {
  return arr?.length || 0;
}

/**
 * Check if array is empty
 */
export function isEmptyArray<T>(arr: T[] | null | undefined): boolean {
  return !arr || arr.length === 0;
}
