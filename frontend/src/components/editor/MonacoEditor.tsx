import React, { useRef, useEffect } from 'react';
import Editor, { OnMount, OnChange } from '@monaco-editor/react';
import type { editor } from 'monaco-editor';

export interface MonacoEditorProps {
  value: string;
  language?: string;
  onChange?: (value: string) => void;
  readOnly?: boolean;
  height?: string | number;
  theme?: 'vs-dark' | 'light' | 'torq-dark';
  options?: editor.IStandaloneEditorConstructionOptions;
  onMount?: (editor: editor.IStandaloneCodeEditor) => void;
}

export const MonacoEditor: React.FC<MonacoEditorProps> = ({
  value,
  language = 'javascript',
  onChange,
  readOnly = false,
  height = '400px',
  theme = 'torq-dark',
  options = {},
  onMount,
}) => {
  const editorRef = useRef<editor.IStandaloneCodeEditor | null>(null);

  const handleEditorDidMount: OnMount = (editor, monaco) => {
    editorRef.current = editor;

    // Define custom TORQ dark theme
    monaco.editor.defineTheme('torq-dark', {
      base: 'vs-dark',
      inherit: true,
      rules: [
        { token: 'comment', foreground: '6A9955', fontStyle: 'italic' },
        { token: 'keyword', foreground: '569CD6' },
        { token: 'string', foreground: 'CE9178' },
        { token: 'number', foreground: 'B5CEA8' },
        { token: 'function', foreground: 'DCDCAA' },
        { token: 'variable', foreground: '9CDCFE' },
        { token: 'type', foreground: '4EC9B0' },
        { token: 'operator', foreground: 'D4D4D4' },
      ],
      colors: {
        'editor.background': '#1e1e1e',
        'editor.foreground': '#D4D4D4',
        'editor.lineHighlightBackground': '#2d2d30',
        'editor.selectionBackground': '#264F78',
        'editor.inactiveSelectionBackground': '#3A3D41',
        'editorCursor.foreground': '#AEAFAD',
        'editorWhitespace.foreground': '#404040',
        'editorLineNumber.foreground': '#858585',
        'editorLineNumber.activeForeground': '#C6C6C6',
        'editor.selectionHighlightBackground': '#ADD6FF26',
        'editor.wordHighlightBackground': '#575757',
        'editor.findMatchBackground': '#515C6A',
        'editor.findMatchHighlightBackground': '#EA5C0055',
        'editorBracketMatch.background': '#0064001a',
        'editorBracketMatch.border': '#888888',
        'scrollbarSlider.background': '#79797966',
        'scrollbarSlider.hoverBackground': '#646464b3',
        'scrollbarSlider.activeBackground': '#bfbfbf66',
      },
    });

    monaco.editor.setTheme(theme);

    // Configure editor for better experience
    editor.updateOptions({
      fontSize: 14,
      fontFamily: 'JetBrains Mono, Fira Code, Source Code Pro, monospace',
      lineHeight: 20,
      letterSpacing: 0.5,
      smoothScrolling: true,
      cursorBlinking: 'smooth',
      cursorSmoothCaretAnimation: 'on',
      renderWhitespace: 'selection',
      minimap: {
        enabled: !readOnly,
      },
    });

    // Call custom onMount handler if provided
    if (onMount) {
      onMount(editor);
    }
  };

  const handleEditorChange: OnChange = (value) => {
    if (onChange && value !== undefined) {
      onChange(value);
    }
  };

  useEffect(() => {
    // Focus editor on mount if not read-only
    if (editorRef.current && !readOnly) {
      editorRef.current.focus();
    }
  }, [readOnly]);

  const defaultOptions: editor.IStandaloneEditorConstructionOptions = {
    readOnly,
    automaticLayout: true,
    scrollBeyondLastLine: false,
    minimap: {
      enabled: !readOnly,
    },
    lineNumbers: 'on',
    renderLineHighlight: readOnly ? 'none' : 'all',
    scrollbar: {
      vertical: 'auto',
      horizontal: 'auto',
      useShadows: false,
      verticalScrollbarSize: 10,
      horizontalScrollbarSize: 10,
    },
    overviewRulerLanes: 0,
    hideCursorInOverviewRuler: true,
    overviewRulerBorder: false,
    padding: {
      top: 12,
      bottom: 12,
    },
    suggest: {
      enabled: !readOnly,
      showKeywords: true,
      showSnippets: true,
      showClasses: true,
      showFunctions: true,
      showVariables: true,
    },
    quickSuggestions: {
      other: !readOnly,
      comments: false,
      strings: !readOnly,
    },
    parameterHints: {
      enabled: !readOnly,
    },
    acceptSuggestionOnCommitCharacter: !readOnly,
    tabCompletion: readOnly ? 'off' : 'on',
    wordBasedSuggestions: readOnly ? 'off' : 'allDocuments',
    formatOnPaste: !readOnly,
    formatOnType: !readOnly,
    ...options,
  };

  return (
    <div className="monaco-editor-wrapper w-full h-full border border-border rounded-md overflow-hidden">
      <Editor
        height={height}
        language={language}
        value={value}
        theme={theme}
        options={defaultOptions}
        onChange={handleEditorChange}
        onMount={handleEditorDidMount}
        loading={
          <div className="flex items-center justify-center h-full bg-bg-primary">
            <div className="text-text-muted">Loading editor...</div>
          </div>
        }
      />
    </div>
  );
};

export default MonacoEditor;
