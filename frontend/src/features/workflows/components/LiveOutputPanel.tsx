/**
 * Live Output Panel
 *
 * Shows real-time output from executing workflow nodes.
 * Supports streaming text and structured data.
 */

import { useState, useEffect, useRef } from "react";
import { Play, Pause, Trash2, Maximize2, Download, Copy, Check } from "lucide-react";
import type { ExecutionNodeResult } from "@workflows/api";

interface LiveOutputPanelProps {
  nodeId: string;
  nodeName: string;
  output?: unknown;
  status?: string;
  isStreaming?: boolean;
  className?: string;
}

export function LiveOutputPanel({
  nodeId,
  nodeName,
  output,
  status = "pending",
  isStreaming = false,
  className = "",
}: LiveOutputPanelProps) {
  const [isPaused, setIsPaused] = useState(false);
  const [copied, setCopied] = useState(false);
  const outputRef = useRef<HTMLDivElement>(null);
  const [isExpanded, setIsExpanded] = useState(false);

  // Auto-scroll to bottom when streaming
  useEffect(() => {
    if (!isPaused && isStreaming && outputRef.current) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight;
    }
  }, [output, isPaused, isStreaming]);

  const handleCopy = () => {
    const text = typeof output === "string" ? output : JSON.stringify(output, null, 2);
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const text = typeof output === "string" ? output : JSON.stringify(output, null, 2);
    const blob = new Blob([text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${nodeId}-output.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const formatOutput = (data: unknown): string => {
    if (data === undefined || data === null) return "No output yet";
    if (typeof data === "string") return data;
    if (typeof data === "object") return JSON.stringify(data, null, 2);
    return String(data);
  };

  const hasOutput = output !== undefined && output !== null;
  const isRunning = status === "running";
  const isComplete = status === "completed";
  const isFailed = status === "failed";

  return (
    <div className={`live-output-panel ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 bg-gray-50 border-b border-gray-200">
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${
            isRunning ? "bg-blue-500 animate-pulse" : isComplete ? "bg-green-500" : isFailed ? "bg-red-500" : "bg-gray-400"
          }`} />
          <h3 className="font-medium text-gray-900">{nodeName}</h3>
          {isStreaming && (
            <span className="text-xs text-blue-600 bg-blue-50 px-2 py-0.5 rounded">
              Streaming
            </span>
          )}
        </div>

        <div className="flex items-center gap-1">
          {isStreaming && (
            <button
              onClick={() => setIsPaused(!isPaused)}
              className="p-1.5 text-gray-500 hover:text-gray-700 hover:bg-gray-200 rounded"
              title={isPaused ? "Resume" : "Pause"}
            >
              {isPaused ? <Play className="w-4 h-4" /> : <Pause className="w-4 h-4" />}
            </button>
          )}

          {hasOutput && (
            <>
              <button
                onClick={handleCopy}
                className="p-1.5 text-gray-500 hover:text-gray-700 hover:bg-gray-200 rounded"
                title="Copy"
              >
                {copied ? <Check className="w-4 h-4 text-green-600" /> : <Copy className="w-4 h-4" />}
              </button>
              <button
                onClick={handleDownload}
                className="p-1.5 text-gray-500 hover:text-gray-700 hover:bg-gray-200 rounded"
                title="Download"
              >
                <Download className="w-4 h-4" />
              </button>
            </>
          )}

          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1.5 text-gray-500 hover:text-gray-700 hover:bg-gray-200 rounded"
            title={isExpanded ? "Collapse" : "Expand"}
          >
            <Maximize2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Output Content */}
      <div
        ref={outputRef}
        className={`p-4 overflow-auto font-mono text-sm ${
          isExpanded ? "fixed inset-0 z-50 bg-white m-0" : "max-h-64 bg-gray-900"
        }`}
      >
        {!hasOutput ? (
          <div className="text-gray-500 text-center py-8">
            {isRunning ? (
              <>
                <div className="animate-pulse mb-2">Waiting for output...</div>
                <div className="flex justify-center gap-1">
                  <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                  <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                  <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                </div>
              </>
            ) : (
              "No output available"
            )}
          </div>
        ) : (
          <pre className={isExpanded ? "text-green-400 text-xs" : "text-green-400 whitespace-pre-wrap break-all"}>
            {formatOutput(output)}
          </pre>
        )}
      </div>

      {/* Footer with stats */}
      {hasOutput && (
        <div className="px-4 py-2 bg-gray-50 border-t border-gray-200 text-xs text-gray-500 flex items-center justify-between">
          <span>{typeof output === "string" ? `${output.length} chars` : `${JSON.stringify(output).length} chars`}</span>
          {isComplete && <span className="text-green-600">Complete</span>}
        </div>
      )}
    </div>
  );
}
