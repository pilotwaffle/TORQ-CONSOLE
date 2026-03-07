/**
 * Graph Controls
 *
 * Additional controls for the workflow graph visualization.
 * Includes layout toggle, fit view, and other display options.
 */

import { useCallback } from "react";
import { Maximize2, Minimize2, RotateCw, Download, LayoutGrid } from "lucide-react";
import { useWorkflowUiStore } from "@workflows/stores/workflowUiStore";

interface GraphControlsProps {
  onFitView?: () => void;
  onZoomIn?: () => void;
  onZoomOut?: () => void;
  onExport?: () => void;
  className?: string;
}

export function GraphControls({ onFitView, onZoomIn, onZoomOut, onExport, className = "" }: GraphControlsProps) {
  const { graphLayout, setGraphLayout, setShowMiniMap } = useWorkflowUiStore();

  const toggleLayout = useCallback(() => {
    setGraphLayout(graphLayout === "horizontal" ? "vertical" : "horizontal");
  }, [graphLayout, setGraphLayout]);

  return (
    <div className={`graph-controls ${className}`}>
      <div className="flex items-center gap-2 p-2 bg-white border border-gray-200 rounded-lg shadow-sm">
        {/* Layout Toggle */}
        <button
          onClick={toggleLayout}
          className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded transition"
          title={`Switch to ${graphLayout === "horizontal" ? "vertical" : "horizontal"} layout`}
        >
          <LayoutGrid className="w-4 h-4" />
        </button>

        {/* Separator */}
        <div className="w-px h-6 bg-gray-200" />

        {/* Zoom Controls */}
        {onZoomOut && (
          <button
            onClick={onZoomOut}
            className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded transition"
            title="Zoom out"
          >
            <Minimize2 className="w-4 h-4" />
          </button>
        )}
        {onZoomIn && (
          <button
            onClick={onZoomIn}
            className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded transition"
            title="Zoom in"
          >
            <Maximize2 className="w-4 h-4" />
          </button>
        )}
        {onFitView && (
          <button
            onClick={onFitView}
            className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded transition"
            title="Fit view"
          >
            <RotateCw className="w-4 h-4" />
          </button>
        )}

        {/* Separator */}
        {(onZoomIn || onZoomOut || onFitView) && onExport && <div className="w-px h-6 bg-gray-200" />}

        {/* Export */}
        {onExport && (
          <button
            onClick={onExport}
            className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded transition"
            title="Export graph"
          >
            <Download className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Layout Indicator */}
      <div className="mt-2 text-xs text-gray-500 text-center">
        Current: <span className="font-medium">{graphLayout}</span> layout
      </div>
    </div>
  );
}
