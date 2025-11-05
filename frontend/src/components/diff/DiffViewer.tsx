import React, { useState, useMemo } from 'react';
import { DiffEditor } from '@monaco-editor/react';
import { ChevronLeft, ChevronRight, SplitSquareHorizontal, AlignJustify } from 'lucide-react';
import { Button } from '@/components/ui/Button';

export interface DiffViewerProps {
  original: string;
  modified: string;
  language?: string;
  viewMode?: 'split' | 'unified';
  showMinimap?: boolean;
  readOnly?: boolean;
  height?: string;
  className?: string;
  onViewModeChange?: (mode: 'split' | 'unified') => void;
}

interface DiffChange {
  lineNumber: number;
  type: 'add' | 'remove' | 'modify';
}

/**
 * DiffViewer Component
 *
 * Advanced diff viewer using Monaco editor with TORQ styling.
 * Supports side-by-side and unified diff views with navigation between changes.
 *
 * @example
 * ```tsx
 * <DiffViewer
 *   original="const x = 1;"
 *   modified="const x = 2;"
 *   language="typescript"
 *   viewMode="split"
 * />
 * ```
 */
export const DiffViewer: React.FC<DiffViewerProps> = ({
  original,
  modified,
  language = 'plaintext',
  viewMode: initialViewMode = 'split',
  showMinimap = false,
  readOnly = true,
  height = '400px',
  className = '',
  onViewModeChange,
}) => {
  const [viewMode, setViewMode] = useState<'split' | 'unified'>(initialViewMode);
  const [currentChangeIndex, setCurrentChangeIndex] = useState<number>(0);
  const [editorInstance, setEditorInstance] = useState<any>(null);

  // Calculate changes between original and modified
  const changes = useMemo<DiffChange[]>(() => {
    const originalLines = original.split('\n');
    const modifiedLines = modified.split('\n');
    const detectedChanges: DiffChange[] = [];

    // Simple diff algorithm - detect additions, removals, and modifications
    const maxLength = Math.max(originalLines.length, modifiedLines.length);
    for (let i = 0; i < maxLength; i++) {
      const origLine = originalLines[i];
      const modLine = modifiedLines[i];

      if (origLine !== modLine) {
        if (origLine === undefined) {
          detectedChanges.push({ lineNumber: i + 1, type: 'add' });
        } else if (modLine === undefined) {
          detectedChanges.push({ lineNumber: i + 1, type: 'remove' });
        } else {
          detectedChanges.push({ lineNumber: i + 1, type: 'modify' });
        }
      }
    }

    return detectedChanges;
  }, [original, modified]);

  const handleViewModeToggle = () => {
    const newMode = viewMode === 'split' ? 'unified' : 'split';
    setViewMode(newMode);
    onViewModeChange?.(newMode);
  };

  const handlePreviousChange = () => {
    if (changes.length === 0) return;
    const newIndex = currentChangeIndex === 0 ? changes.length - 1 : currentChangeIndex - 1;
    setCurrentChangeIndex(newIndex);
    navigateToChange(changes[newIndex]);
  };

  const handleNextChange = () => {
    if (changes.length === 0) return;
    const newIndex = (currentChangeIndex + 1) % changes.length;
    setCurrentChangeIndex(newIndex);
    navigateToChange(changes[newIndex]);
  };

  const navigateToChange = (change: DiffChange) => {
    if (!editorInstance) return;

    try {
      // Get the modified editor (right side in split view)
      const modifiedEditor = editorInstance.getModifiedEditor?.() || editorInstance;

      if (modifiedEditor) {
        // Reveal the line and center it in the view
        modifiedEditor.revealLineInCenter(change.lineNumber);

        // Set cursor position
        modifiedEditor.setPosition({
          lineNumber: change.lineNumber,
          column: 1,
        });

        // Focus the editor
        modifiedEditor.focus();
      }
    } catch (error) {
      console.error('Failed to navigate to change:', error);
    }
  };

  const handleEditorDidMount = (editor: any) => {
    setEditorInstance(editor);
  };

  // Monaco editor options with TORQ theme
  const editorOptions = {
    readOnly,
    minimap: { enabled: showMinimap },
    fontSize: 14,
    fontFamily: 'JetBrains Mono, Fira Code, Source Code Pro, monospace',
    lineHeight: 20,
    renderSideBySide: viewMode === 'split',
    renderOverviewRuler: true,
    scrollBeyondLastLine: false,
    wordWrap: 'off' as const,
    automaticLayout: true,
    diffWordWrap: 'off' as const,
    renderIndicators: true,
    renderMarginRevertIcon: !readOnly,
    // TORQ colors for diff highlighting
    theme: 'vs-dark',
    ignoreTrimWhitespace: false,
    renderWhitespace: 'selection' as const,
  };

  return (
    <div className={`flex flex-col bg-bg-tertiary rounded-lg border border-border overflow-hidden ${className}`}>
      {/* Toolbar */}
      <div className="flex items-center justify-between px-3 py-2 bg-bg-secondary border-b border-border">
        <div className="flex items-center gap-2">
          <span className="text-small text-text-muted font-mono">
            {changes.length} {changes.length === 1 ? 'change' : 'changes'}
          </span>
          {changes.length > 0 && (
            <span className="text-small text-text-muted">
              ({currentChangeIndex + 1} / {changes.length})
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          {/* Navigation buttons */}
          <Button
            variant="ghost"
            size="icon"
            onClick={handlePreviousChange}
            disabled={changes.length === 0}
            title="Previous change (Shift+F7)"
            className="h-8 w-8"
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={handleNextChange}
            disabled={changes.length === 0}
            title="Next change (F7)"
            className="h-8 w-8"
          >
            <ChevronRight className="h-4 w-4" />
          </Button>

          {/* View mode toggle */}
          <div className="w-px h-6 bg-border mx-1" />
          <Button
            variant="ghost"
            size="sm"
            onClick={handleViewModeToggle}
            title={`Switch to ${viewMode === 'split' ? 'unified' : 'split'} view`}
            className="gap-2"
          >
            {viewMode === 'split' ? (
              <>
                <SplitSquareHorizontal className="h-4 w-4" />
                <span className="text-small">Split</span>
              </>
            ) : (
              <>
                <AlignJustify className="h-4 w-4" />
                <span className="text-small">Unified</span>
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Diff Editor */}
      <div className="relative" style={{ height }}>
        <DiffEditor
          original={original}
          modified={modified}
          language={language}
          options={editorOptions}
          onMount={handleEditorDidMount}
          theme="vs-dark"
          loading={
            <div className="flex items-center justify-center h-full bg-bg-tertiary">
              <div className="text-text-muted">Loading diff editor...</div>
            </div>
          }
        />
      </div>

      {/* Custom CSS for TORQ diff colors */}
      <style>{`
        /* TORQ diff colors - additions (green) */
        .monaco-diff-editor .line-insert,
        .monaco-editor .line-insert {
          background-color: rgba(16, 185, 129, 0.15) !important;
        }

        .monaco-diff-editor .char-insert,
        .monaco-editor .char-insert {
          background-color: rgba(16, 185, 129, 0.3) !important;
        }

        /* TORQ diff colors - deletions (red) */
        .monaco-diff-editor .line-delete,
        .monaco-editor .line-delete {
          background-color: rgba(239, 68, 68, 0.15) !important;
        }

        .monaco-diff-editor .char-delete,
        .monaco-editor .char-delete {
          background-color: rgba(239, 68, 68, 0.3) !important;
        }

        /* Diff gutter indicators */
        .monaco-diff-editor .insert-sign,
        .monaco-editor .insert-sign {
          background-color: #10b981 !important;
        }

        .monaco-diff-editor .delete-sign,
        .monaco-editor .delete-sign {
          background-color: #ef4444 !important;
        }

        /* Scrollbar styling to match TORQ theme */
        .monaco-editor .decorationsOverviewRuler {
          opacity: 0.7;
        }

        .monaco-diff-editor .diffOverview {
          background-color: #2d2d30;
        }

        /* Line numbers in TORQ colors */
        .monaco-diff-editor .line-numbers,
        .monaco-editor .line-numbers {
          color: #808080 !important;
        }

        .monaco-diff-editor .current-line,
        .monaco-editor .current-line {
          border-color: #0078d4 !important;
        }
      `}</style>
    </div>
  );
};

export default DiffViewer;
