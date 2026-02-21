import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Code2, FileCode } from 'lucide-react';
import { DiffViewer } from '@/components/diff/DiffViewer.tsx';
import { DiffStats } from '@/components/diff/DiffStats.tsx';
import { Button } from '@/components/ui/Button.tsx';
import { Badge } from '@/components/ui/Badge.tsx';
import type { DiffBlock } from '@/lib/types';

export interface DiffMessageProps {
  diff: DiffBlock;
  fileName?: string;
  language?: string;
  className?: string;
  defaultExpanded?: boolean;
}

/**
 * DiffMessage Component
 *
 * Displays a diff in chat messages with collapsible viewer.
 * Shows stats by default, expands to full Monaco diff editor on click.
 *
 * @example
 * ```tsx
 * <DiffMessage
 *   diff={{
 *     additions: 42,
 *     deletions: 15,
 *     hunks: [...]
 *   }}
 *   fileName="src/App.tsx"
 *   language="typescript"
 * />
 * ```
 */
export const DiffMessage: React.FC<DiffMessageProps> = ({
  diff,
  fileName,
  language = 'plaintext',
  className = '',
  defaultExpanded = false,
}) => {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  // Convert DiffBlock hunks to original and modified text
  const { original, modified } = React.useMemo(() => {
    let originalText = '';
    let modifiedText = '';

    diff.hunks.forEach((hunk) => {
      hunk.lines.forEach((line) => {
        if (line.type === 'remove' || line.type === 'context') {
          originalText += line.content + '\n';
        }
        if (line.type === 'add' || line.type === 'context') {
          modifiedText += line.content + '\n';
        }
      });
    });

    return {
      original: originalText.trim(),
      modified: modifiedText.trim(),
    };
  }, [diff]);

  const handleToggleExpand = () => {
    setIsExpanded(!isExpanded);
  };

  // Detect if this is a large diff (warn user)
  const isLargeDiff = diff.additions + diff.deletions > 500;
  const totalChanges = diff.additions + diff.deletions;

  return (
    <div className={`flex flex-col bg-bg-secondary rounded-lg border border-border overflow-hidden ${className}`}>
      {/* Header with stats and expand button */}
      <div
        className="flex items-center justify-between px-4 py-3 cursor-pointer hover:bg-bg-tertiary/50 transition-colors"
        onClick={handleToggleExpand}
      >
        <div className="flex items-center gap-3 flex-1 min-w-0">
          {/* Diff icon */}
          <div className="flex-shrink-0">
            {fileName ? (
              <FileCode className="h-5 w-5 text-agent-thinking" />
            ) : (
              <Code2 className="h-5 w-5 text-agent-thinking" />
            )}
          </div>

          {/* Stats */}
          <div className="flex-1 min-w-0">
            <DiffStats
              additions={diff.additions}
              deletions={diff.deletions}
              fileName={fileName}
              showBar={false}
              showFileIcon={false}
            />
          </div>

          {/* Badges */}
          <div className="flex items-center gap-2 flex-shrink-0">
            <Badge variant="warning" className="text-xs">
              diff
            </Badge>
            {isLargeDiff && (
              <Badge variant="secondary" className="text-xs">
                {totalChanges}+ changes
              </Badge>
            )}
          </div>
        </div>

        {/* Expand/collapse button */}
        <Button
          variant="ghost"
          size="icon"
          className="ml-2 flex-shrink-0"
          onClick={(e) => {
            e.stopPropagation();
            handleToggleExpand();
          }}
        >
          {isExpanded ? (
            <ChevronUp className="h-4 w-4" />
          ) : (
            <ChevronDown className="h-4 w-4" />
          )}
        </Button>
      </div>

      {/* Expanded diff viewer */}
      {isExpanded && (
        <div className="border-t border-border">
          {/* Secondary stats bar with visual indicator */}
          <div className="px-4 py-2 bg-bg-tertiary/50 border-b border-border">
            <DiffStats
              additions={diff.additions}
              deletions={diff.deletions}
              showBar={true}
              showFileIcon={false}
            />
          </div>

          {/* Monaco diff editor */}
          <div className="p-2">
            <DiffViewer
              original={original}
              modified={modified}
              language={language}
              viewMode="split"
              height={isLargeDiff ? '600px' : '400px'}
              showMinimap={isLargeDiff}
            />
          </div>

          {/* Footer with actions */}
          <div className="px-4 py-2 bg-bg-tertiary/50 border-t border-border flex items-center justify-between">
            <div className="text-small text-text-muted">
              {fileName && (
                <span className="font-mono">{fileName}</span>
              )}
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={handleToggleExpand}
                className="text-small"
              >
                Collapse
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Collapsed preview (show first few lines) */}
      {!isExpanded && (
        <div className="px-4 py-3 bg-bg-tertiary/30 border-t border-border">
          <DiffPreview hunks={diff.hunks} maxLines={5} />
          <div className="mt-2 text-center">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleToggleExpand}
              className="text-small text-accent-primary hover:text-accent-hover"
            >
              Click to view full diff
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

/**
 * DiffPreview Component
 *
 * Shows a compact preview of the first few diff lines.
 */
const DiffPreview: React.FC<{
  hunks: DiffBlock['hunks'];
  maxLines?: number;
}> = ({ hunks, maxLines = 5 }) => {
  const previewLines: Array<{ content: string; type: 'add' | 'remove' | 'context' }> = [];

  // Collect first N lines from hunks
  for (const hunk of hunks) {
    for (const line of hunk.lines) {
      if (previewLines.length >= maxLines) break;
      previewLines.push(line);
    }
    if (previewLines.length >= maxLines) break;
  }

  const getLineStyle = (type: 'add' | 'remove' | 'context'): string => {
    switch (type) {
      case 'add':
        return 'bg-diff-added text-torq-green';
      case 'remove':
        return 'bg-diff-removed text-torq-red';
      case 'context':
        return 'text-text-secondary';
    }
  };

  const getLinePrefix = (type: 'add' | 'remove' | 'context'): string => {
    switch (type) {
      case 'add':
        return '+';
      case 'remove':
        return '-';
      case 'context':
        return ' ';
    }
  };

  return (
    <div className="font-mono text-code bg-bg-tertiary rounded-md p-3 overflow-x-auto">
      {previewLines.map((line, index) => (
        <div
          key={index}
          className={`px-2 py-0.5 ${getLineStyle(line.type)}`}
        >
          <span className="text-text-muted mr-2">{getLinePrefix(line.type)}</span>
          {line.content || '\u00A0'}
        </div>
      ))}
      {hunks.reduce((total, hunk) => total + hunk.lines.length, 0) > maxLines && (
        <div className="text-text-muted text-small mt-2 text-center">
          ... {hunks.reduce((total, hunk) => total + hunk.lines.length, 0) - maxLines} more lines
        </div>
      )}
    </div>
  );
};

/**
 * InlineDiffMessage Component
 *
 * Compact inline diff for use in message flows without expansion.
 *
 * @example
 * ```tsx
 * <InlineDiffMessage
 *   diff={diffBlock}
 *   fileName="app.tsx"
 * />
 * ```
 */
export const InlineDiffMessage: React.FC<{
  diff: DiffBlock;
  fileName?: string;
  className?: string;
}> = ({ diff, fileName, className = '' }) => {
  return (
    <div className={`flex items-center gap-3 px-3 py-2 bg-bg-secondary rounded-md border border-border ${className}`}>
      <FileCode className="h-4 w-4 text-agent-thinking flex-shrink-0" />
      <div className="flex-1 min-w-0">
        {fileName && (
          <div className="text-small font-mono text-text-primary truncate mb-1">
            {fileName}
          </div>
        )}
        <div className="flex items-center gap-3">
          <span className="text-small text-torq-green font-mono">+{diff.additions}</span>
          <span className="text-small text-torq-red font-mono">-{diff.deletions}</span>
        </div>
      </div>
      <Badge variant="warning" className="text-xs flex-shrink-0">
        diff
      </Badge>
    </div>
  );
};

export default DiffMessage;
