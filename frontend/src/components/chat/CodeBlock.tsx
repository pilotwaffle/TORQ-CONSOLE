import React, { useState } from 'react';
import { CodeViewer } from '../editor/CodeViewer';
import { Download, ChevronDown, ChevronUp } from 'lucide-react';

export interface CodeBlockProps {
  code: string;
  language?: string;
  fileName?: string;
  filePath?: string;
  maxHeight?: string | number;
  collapsible?: boolean;
  defaultCollapsed?: boolean;
}

export const CodeBlock: React.FC<CodeBlockProps> = ({
  code,
  language,
  fileName,
  filePath,
  maxHeight = '400px',
  collapsible = true,
  defaultCollapsed = false,
}) => {
  const [isCollapsed, setIsCollapsed] = useState(defaultCollapsed);
  const lineCount = code.split('\n').length;
  const shouldBeCollapsible = collapsible && lineCount > 20;

  const handleDownload = () => {
    try {
      const blob = new Blob([code], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = fileName || getDefaultFileName(language);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to download code:', error);
    }
  };

  const toggleCollapse = () => {
    setIsCollapsed(!isCollapsed);
  };

  const displayHeight = isCollapsed ? '150px' : maxHeight;
  const title = fileName || filePath ? (fileName || filePath) : undefined;

  return (
    <div className="code-block-container my-2 rounded-md overflow-hidden border border-border bg-bg-tertiary">
      {/* Header */}
      <div className="flex items-center justify-between bg-bg-secondary px-3 py-2 border-b border-border">
        <div className="flex items-center gap-2 flex-1 min-w-0">
          {/* File info */}
          <div className="flex items-center gap-2 min-w-0">
            {title && (
              <span className="text-small font-mono text-text-primary truncate max-w-md">
                {title}
              </span>
            )}
            {language && (
              <span className="text-xs font-mono px-2 py-0.5 bg-bg-tertiary text-text-muted rounded border border-border flex-shrink-0">
                {language}
              </span>
            )}
          </div>

          {/* Line count badge */}
          <span className="text-xs text-text-muted flex-shrink-0">
            {lineCount} {lineCount === 1 ? 'line' : 'lines'}
          </span>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-1 ml-2">
          <button
            onClick={handleDownload}
            className="p-1.5 hover:bg-bg-tertiary rounded transition-colors text-text-muted hover:text-text-primary"
            title="Download code"
            aria-label="Download code as file"
          >
            <Download className="w-4 h-4" />
          </button>

          {shouldBeCollapsible && (
            <button
              onClick={toggleCollapse}
              className="p-1.5 hover:bg-bg-tertiary rounded transition-colors text-text-muted hover:text-text-primary"
              title={isCollapsed ? 'Expand code' : 'Collapse code'}
              aria-label={isCollapsed ? 'Expand code block' : 'Collapse code block'}
            >
              {isCollapsed ? (
                <ChevronDown className="w-4 h-4" />
              ) : (
                <ChevronUp className="w-4 h-4" />
              )}
            </button>
          )}
        </div>
      </div>

      {/* Code viewer */}
      <div className="relative">
        <CodeViewer
          code={code}
          language={language}
          height={displayHeight}
          showLineNumbers={true}
          enableCopy={true}
          enableExpand={true}
          className="rounded-none border-0"
        />

        {/* Collapse indicator */}
        {shouldBeCollapsible && isCollapsed && (
          <div className="absolute bottom-0 left-0 right-0 h-12 bg-gradient-to-t from-bg-tertiary to-transparent pointer-events-none" />
        )}
      </div>

      {/* Expand prompt for collapsed code */}
      {shouldBeCollapsible && isCollapsed && (
        <button
          onClick={toggleCollapse}
          className="w-full py-2 text-xs text-text-muted hover:text-text-primary hover:bg-bg-secondary transition-colors border-t border-border"
        >
          Click to expand {lineCount - 10} more lines
        </button>
      )}
    </div>
  );
};

/**
 * Get default file name based on language
 */
function getDefaultFileName(language?: string): string {
  const extensions: Record<string, string> = {
    javascript: 'code.js',
    typescript: 'code.ts',
    python: 'code.py',
    java: 'Code.java',
    cpp: 'code.cpp',
    c: 'code.c',
    go: 'code.go',
    rust: 'code.rs',
    ruby: 'code.rb',
    php: 'code.php',
    html: 'index.html',
    css: 'styles.css',
    json: 'data.json',
    yaml: 'config.yaml',
    sql: 'query.sql',
    shell: 'script.sh',
    markdown: 'README.md',
    plaintext: 'code.txt',
  };

  return extensions[language || 'plaintext'] || 'code.txt';
}

export default CodeBlock;
