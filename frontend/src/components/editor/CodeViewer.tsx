import React, { useState } from 'react';
import { MonacoEditor } from './MonacoEditor';
import { Copy, Check, Maximize2, Minimize2 } from 'lucide-react';

export interface CodeViewerProps {
  code: string;
  language?: string;
  title?: string;
  height?: string | number;
  showLineNumbers?: boolean;
  enableCopy?: boolean;
  enableExpand?: boolean;
  className?: string;
}

export const CodeViewer: React.FC<CodeViewerProps> = ({
  code,
  language = 'javascript',
  title,
  height = '400px',
  showLineNumbers = true,
  enableCopy = true,
  enableExpand = true,
  className = '',
}) => {
  const [copied, setCopied] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('Failed to copy code:', error);
    }
  };

  const toggleExpand = () => {
    setIsExpanded(!isExpanded);
  };

  const detectedLanguage = language || detectLanguage(code);
  const displayHeight = isExpanded ? '80vh' : height;

  return (
    <div className={`code-viewer-container ${className}`}>
      {/* Header */}
      {(title || enableCopy || enableExpand) && (
        <div className="flex items-center justify-between bg-bg-tertiary border border-border border-b-0 rounded-t-md px-4 py-2">
          <div className="flex items-center gap-2">
            {title && (
              <h3 className="text-body font-medium text-text-primary">{title}</h3>
            )}
            {detectedLanguage && (
              <span className="text-xs font-mono px-2 py-0.5 bg-bg-secondary text-text-muted rounded border border-border">
                {detectedLanguage}
              </span>
            )}
          </div>

          <div className="flex items-center gap-2">
            {enableExpand && (
              <button
                onClick={toggleExpand}
                className="p-1.5 hover:bg-bg-secondary rounded transition-colors text-text-muted hover:text-text-primary"
                title={isExpanded ? 'Minimize' : 'Maximize'}
                aria-label={isExpanded ? 'Minimize code viewer' : 'Maximize code viewer'}
              >
                {isExpanded ? (
                  <Minimize2 className="w-4 h-4" />
                ) : (
                  <Maximize2 className="w-4 h-4" />
                )}
              </button>
            )}

            {enableCopy && (
              <button
                onClick={handleCopy}
                className="flex items-center gap-1.5 px-2 py-1.5 hover:bg-bg-secondary rounded transition-colors text-text-muted hover:text-text-primary"
                title="Copy code"
                aria-label="Copy code to clipboard"
              >
                {copied ? (
                  <>
                    <Check className="w-4 h-4 text-agent-success" />
                    <span className="text-xs text-agent-success">Copied!</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-4 h-4" />
                    <span className="text-xs">Copy</span>
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      )}

      {/* Monaco Editor (Read-Only) */}
      <MonacoEditor
        value={code}
        language={detectedLanguage}
        readOnly={true}
        height={displayHeight}
        options={{
          lineNumbers: showLineNumbers ? 'on' : 'off',
          minimap: { enabled: false },
          scrollBeyondLastLine: false,
          renderLineHighlight: 'none',
          contextmenu: true,
          folding: true,
          glyphMargin: false,
          lineDecorationsWidth: 0,
          lineNumbersMinChars: 3,
        }}
      />
    </div>
  );
};

/**
 * Detect programming language from code content
 * This is a simple heuristic-based detection
 */
function detectLanguage(code: string): string {
  const trimmedCode = code.trim();

  // Python
  if (
    /^(import |from |def |class |if __name__|@\w+|\s*#)/.test(trimmedCode) ||
    /:\s*$/.test(trimmedCode.split('\n')[0])
  ) {
    return 'python';
  }

  // TypeScript/JavaScript
  if (
    /^(import |export |const |let |var |function |class |interface |type |async |await)/.test(
      trimmedCode
    ) ||
    /\b(React|useState|useEffect|console\.log)\b/.test(trimmedCode)
  ) {
    if (
      /^(interface |type |enum |namespace |declare |as |:\s*\w+)/.test(trimmedCode) ||
      /:\s*\w+(\[\])?(\s*[=|;])/.test(trimmedCode)
    ) {
      return 'typescript';
    }
    return 'javascript';
  }

  // JSON
  if (/^[\s]*[{\[]/.test(trimmedCode) && /[}\]]\s*$/.test(trimmedCode)) {
    try {
      JSON.parse(trimmedCode);
      return 'json';
    } catch {
      // Not valid JSON
    }
  }

  // HTML/XML
  if (/^<(!DOCTYPE|html|xml|\?xml)/.test(trimmedCode)) {
    return 'html';
  }

  // CSS/SCSS
  if (/^(@import|@media|\.[\w-]+\s*{|#[\w-]+\s*{)/.test(trimmedCode)) {
    return 'css';
  }

  // SQL
  if (/^(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP)\b/i.test(trimmedCode)) {
    return 'sql';
  }

  // Shell/Bash
  if (/^(#!\/bin\/(ba)?sh|export |alias |source )/.test(trimmedCode)) {
    return 'shell';
  }

  // Markdown
  if (/^(#{1,6}\s|```|\*\*|__|\[.*\]\(.*\))/.test(trimmedCode)) {
    return 'markdown';
  }

  // Java
  if (
    /^(package |import |public class |private |protected |@Override)/.test(trimmedCode)
  ) {
    return 'java';
  }

  // C/C++
  if (/^(#include|using namespace|int main\(|void )/.test(trimmedCode)) {
    return 'cpp';
  }

  // Go
  if (/^(package |import \(|func |type |var |const )/.test(trimmedCode)) {
    return 'go';
  }

  // Rust
  if (/^(use |fn |pub |mod |struct |impl |trait )/.test(trimmedCode)) {
    return 'rust';
  }

  // Ruby
  if (/^(require |class |module |def |end$)/.test(trimmedCode)) {
    return 'ruby';
  }

  // PHP
  if (/^<\?php/.test(trimmedCode)) {
    return 'php';
  }

  // YAML
  if (/^[\w-]+:\s*$/.test(trimmedCode.split('\n')[0])) {
    return 'yaml';
  }

  // Default to plaintext
  return 'plaintext';
}

export default CodeViewer;
