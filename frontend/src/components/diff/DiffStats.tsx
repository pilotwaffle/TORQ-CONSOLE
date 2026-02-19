import React from 'react';
import { Plus, Minus, FileCode } from 'lucide-react';
import { Badge } from '@/components/ui/Badge.tsx';

export interface DiffStatsProps {
  additions: number;
  deletions: number;
  fileName?: string;
  fileCount?: number;
  showBar?: boolean;
  showFileIcon?: boolean;
  className?: string;
}

/**
 * DiffStats Component
 *
 * Displays diff statistics with visual indicators for additions and deletions.
 * Uses TORQ green/red colors for additions/deletions with a visual ratio bar.
 *
 * @example
 * ```tsx
 * <DiffStats
 *   additions={42}
 *   deletions={15}
 *   fileName="src/components/App.tsx"
 *   showBar={true}
 * />
 * ```
 */
export const DiffStats: React.FC<DiffStatsProps> = ({
  additions,
  deletions,
  fileName,
  fileCount = 1,
  showBar = true,
  showFileIcon = true,
  className = '',
}) => {
  const totalChanges = additions + deletions;
  const additionsPercent = totalChanges > 0 ? (additions / totalChanges) * 100 : 50;
  const deletionsPercent = totalChanges > 0 ? (deletions / totalChanges) * 100 : 50;

  // Format large numbers with commas
  const formatNumber = (num: number): string => {
    return num.toLocaleString('en-US');
  };

  // Get color intensity based on change magnitude
  const getChangeColor = (count: number, type: 'add' | 'delete'): string => {
    if (count === 0) return 'text-text-muted';
    if (type === 'add') return 'text-torq-green';
    return 'text-torq-red';
  };

  return (
    <div className={`flex flex-col gap-2 ${className}`}>
      {/* File name header */}
      {fileName && (
        <div className="flex items-center gap-2">
          {showFileIcon && <FileCode className="h-4 w-4 text-text-muted" />}
          <span className="text-body font-mono text-text-primary truncate" title={fileName}>
            {fileName}
          </span>
        </div>
      )}

      {/* Stats summary */}
      <div className="flex items-center gap-3 flex-wrap">
        {/* File count badge (if multiple files) */}
        {fileCount > 1 && (
          <Badge variant="secondary" className="text-xs">
            {fileCount} {fileCount === 1 ? 'file' : 'files'} changed
          </Badge>
        )}

        {/* Additions */}
        <div className="flex items-center gap-1.5">
          <Plus className={`h-4 w-4 ${getChangeColor(additions, 'add')}`} />
          <span className={`text-body font-medium ${getChangeColor(additions, 'add')}`}>
            {formatNumber(additions)}
          </span>
          <span className="text-small text-text-muted">
            {additions === 1 ? 'addition' : 'additions'}
          </span>
        </div>

        {/* Deletions */}
        <div className="flex items-center gap-1.5">
          <Minus className={`h-4 w-4 ${getChangeColor(deletions, 'delete')}`} />
          <span className={`text-body font-medium ${getChangeColor(deletions, 'delete')}`}>
            {formatNumber(deletions)}
          </span>
          <span className="text-small text-text-muted">
            {deletions === 1 ? 'deletion' : 'deletions'}
          </span>
        </div>
      </div>

      {/* Visual bar showing addition/deletion ratio */}
      {showBar && totalChanges > 0 && (
        <div className="flex items-center gap-2">
          <div className="flex-1 h-2 bg-bg-tertiary rounded-full overflow-hidden flex">
            {/* Additions bar */}
            {additions > 0 && (
              <div
                className="bg-torq-green transition-all duration-300"
                style={{ width: `${additionsPercent}%` }}
                title={`${additions} additions (${additionsPercent.toFixed(1)}%)`}
              />
            )}
            {/* Deletions bar */}
            {deletions > 0 && (
              <div
                className="bg-torq-red transition-all duration-300"
                style={{ width: `${deletionsPercent}%` }}
                title={`${deletions} deletions (${deletionsPercent.toFixed(1)}%)`}
              />
            )}
          </div>

          {/* Total changes */}
          <span className="text-small text-text-muted font-mono whitespace-nowrap">
            {formatNumber(totalChanges)} {totalChanges === 1 ? 'change' : 'changes'}
          </span>
        </div>
      )}

      {/* Additional context for large diffs */}
      {totalChanges > 1000 && (
        <div className="flex items-center gap-1.5 text-small text-agent-thinking">
          <Badge variant="warning" className="text-xs">
            Large diff
          </Badge>
          <span>Review carefully</span>
        </div>
      )}

      {/* Net change indicator */}
      {totalChanges > 0 && (
        <div className="text-small text-text-muted">
          Net change:{' '}
          <span className={additions > deletions ? 'text-torq-green' : additions < deletions ? 'text-torq-red' : 'text-text-muted'}>
            {additions > deletions ? '+' : ''}
            {formatNumber(additions - deletions)} lines
          </span>
        </div>
      )}
    </div>
  );
};

/**
 * CompactDiffStats Component
 *
 * Compact inline version of DiffStats for use in tight spaces.
 *
 * @example
 * ```tsx
 * <CompactDiffStats additions={42} deletions={15} />
 * ```
 */
export const CompactDiffStats: React.FC<{
  additions: number;
  deletions: number;
  className?: string;
}> = ({ additions, deletions, className = '' }) => {
  return (
    <div className={`inline-flex items-center gap-2 ${className}`}>
      <span className="text-small text-torq-green font-mono">+{additions}</span>
      <span className="text-small text-torq-red font-mono">-{deletions}</span>
    </div>
  );
};

/**
 * DiffStatsList Component
 *
 * Displays stats for multiple files in a list format.
 *
 * @example
 * ```tsx
 * <DiffStatsList
 *   files={[
 *     { fileName: 'app.tsx', additions: 42, deletions: 15 },
 *     { fileName: 'utils.ts', additions: 10, deletions: 5 }
 *   ]}
 * />
 * ```
 */
export interface DiffFileStats {
  fileName: string;
  additions: number;
  deletions: number;
}

export const DiffStatsList: React.FC<{
  files: DiffFileStats[];
  className?: string;
}> = ({ files, className = '' }) => {
  const totalAdditions = files.reduce((sum, file) => sum + file.additions, 0);
  const totalDeletions = files.reduce((sum, file) => sum + file.deletions, 0);

  return (
    <div className={`flex flex-col gap-3 ${className}`}>
      {/* Total summary */}
      <DiffStats
        additions={totalAdditions}
        deletions={totalDeletions}
        fileCount={files.length}
        showFileIcon={false}
      />

      {/* Individual file stats */}
      {files.length > 1 && (
        <div className="flex flex-col gap-2 pl-4 border-l-2 border-border">
          {files.map((file, index) => (
            <div key={index} className="flex items-center justify-between gap-4">
              <span className="text-small font-mono text-text-secondary truncate flex-1" title={file.fileName}>
                {file.fileName}
              </span>
              <CompactDiffStats additions={file.additions} deletions={file.deletions} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default DiffStats;
