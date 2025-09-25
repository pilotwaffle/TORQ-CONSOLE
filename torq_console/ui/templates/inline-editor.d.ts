/**
 * TORQ CONSOLE Inline Editor TypeScript Definitions v0.70.0
 *
 * Comprehensive type definitions for the inline editing system with
 * Cursor-like functionality, ghost text rendering, and multi-step workflows.
 */

// Core Types
export type EditMode = 'selection' | 'cursor' | 'ghost_text' | 'quick_question' | 'refinement';
export type EditAction = 'generate' | 'refine' | 'explain' | 'complete' | 'transform' | 'review';
export type GhostTextSource = 'ai' | 'completion' | 'snippet';

// Selection Interface
export interface EditSelection {
  start_line: number;
  start_col: number;
  end_line: number;
  end_col: number;
  text?: string;
  file_path?: string;
}

// Ghost Text Suggestion
export interface GhostTextSuggestion {
  id: string;
  text: string;
  position: [number, number]; // [line, column]
  confidence: number;
  source: GhostTextSource;
  metadata?: Record<string, any>;
  timestamp: string;
}

// Edit Request
export interface InlineEditRequest {
  id?: string;
  mode: EditMode;
  action: EditAction;
  prompt: string;
  selection?: EditSelection;
  file_path?: string;
  cursor_position?: [number, number];
  metadata?: Record<string, any>;
}

// Edit Response
export interface InlineEditResponse {
  request_id: string;
  success: boolean;
  content: string;
  ghost_text?: GhostTextSuggestion;
  alternatives?: string[];
  explanation?: string;
  confidence: number;
  metadata?: Record<string, any>;
  timestamp: string;
}

// Workflow Types
export interface WorkflowStep {
  name: string;
  status: 'pending' | 'active' | 'completed' | 'failed';
  progress: number;
  result?: any;
}

export interface RefinementWorkflow {
  steps: WorkflowStep[];
  current_step: number;
  overall_progress: number;
  results: {
    initial?: string;
    critic_review?: any;
    refined_version?: string;
    evaluation?: any;
    final_recommendation?: string;
  };
}

// Context Types
export interface ContextItem {
  type: 'file' | 'text' | 'code' | 'docs';
  name?: string;
  path?: string;
  content?: string;
  full_content?: string;
  metadata?: Record<string, any>;
}

export interface DraggedContext {
  items: ContextItem[];
  total_size: number;
  timestamp: string;
}

// Keyboard Shortcut Types
export interface KeyboardShortcut {
  key: string;
  ctrl?: boolean;
  alt?: boolean;
  shift?: boolean;
  meta?: boolean;
  description: string;
  handler: string;
}

export interface ShortcutMap {
  [combo: string]: KeyboardShortcut;
}

// API Response Types
export interface APIResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
  timestamp: string;
}

export interface GhostActionRequest {
  action: 'accept' | 'dismiss' | 'alternatives';
  ghost_id?: string;
  metadata?: Record<string, any>;
}

export interface InlineEditStats {
  total_requests: number;
  active_requests: number;
  ghost_suggestions: number;
  most_common_actions: Record<string, number>;
  most_common_modes: Record<string, number>;
  shadow_workspace_path: string;
}

// UI State Types
export interface InlineEditorState {
  showInlineEditorPanel: boolean;
  inlineEditMode: EditMode;
  inlineEditAction: EditAction;
  inlineEditPrompt: string;
  inlineEditResult: string;
  inlineEditAlternatives: string[];
  currentSelection: EditSelection | null;
  activeGhostText: GhostTextSuggestion | null;
  draggedContext: ContextItem[];
  workflowStep: number;
  workflowResults?: RefinementWorkflow;
}

// Event Types
export interface InlineEditEvent {
  type: 'inline_edit_request' | 'inline_edit_response' | 'ghost_action' | 'workflow_update';
  data: any;
  timestamp: string;
}

export interface KeyboardEvent extends Event {
  key: string;
  code: string;
  ctrlKey: boolean;
  altKey: boolean;
  shiftKey: boolean;
  metaKey: boolean;
  preventDefault(): void;
  stopPropagation(): void;
}

// Component Props
export interface InlineEditorProps {
  initialMode?: EditMode;
  initialAction?: EditAction;
  onEdit?: (request: InlineEditRequest) => Promise<InlineEditResponse>;
  onGhostAction?: (action: GhostActionRequest) => Promise<any>;
  shortcuts?: ShortcutMap;
  enableRefinement?: boolean;
  enableDragDrop?: boolean;
}

export interface GhostTextProps {
  suggestion: GhostTextSuggestion;
  onAccept: (id: string) => void;
  onDismiss: (id: string) => void;
  position: { x: number; y: number };
  visible: boolean;
}

export interface CodeEditorProps {
  content: string;
  language?: string;
  readOnly?: boolean;
  selection?: EditSelection;
  ghostText?: GhostTextSuggestion;
  onSelectionChange?: (selection: EditSelection) => void;
  onCursorChange?: (position: [number, number]) => void;
  onKeyboardShortcut?: (event: KeyboardEvent) => void;
}

export interface WorkflowDisplayProps {
  workflow: RefinementWorkflow;
  onStepClick?: (step: number) => void;
  showProgress?: boolean;
  compact?: boolean;
}

// Utility Types
export type QuickAction =
  | 'add_docstring'
  | 'add_type_hints'
  | 'refactor'
  | 'explain'
  | 'optimize'
  | 'extract_method'
  | 'rename_variable'
  | 'format_code';

export interface QuickActionDefinition {
  id: QuickAction;
  label: string;
  icon: string;
  prompt: string;
  action: EditAction;
  mode?: EditMode;
}

// Error Types
export interface InlineEditError {
  code: string;
  message: string;
  details?: any;
  timestamp: string;
}

export interface ValidationError extends InlineEditError {
  field: string;
  value: any;
}

// Configuration Types
export interface InlineEditorConfig {
  // Keyboard shortcuts
  shortcuts: ShortcutMap;

  // Ghost text settings
  ghostText: {
    enabled: boolean;
    showDelay: number;
    hideDelay: number;
    maxSuggestions: number;
    confidence_threshold: number;
  };

  // Refinement workflow settings
  refinement: {
    enabled: boolean;
    steps: string[];
    auto_run: boolean;
    timeout: number;
  };

  // Context management
  context: {
    maxItems: number;
    maxSize: number;
    supportedTypes: string[];
    dragDropEnabled: boolean;
  };

  // AI integration
  ai: {
    model: string;
    temperature: number;
    maxTokens: number;
    timeout: number;
  };

  // UI preferences
  ui: {
    theme: 'dark' | 'light' | 'auto';
    animations: boolean;
    showTooltips: boolean;
    compactMode: boolean;
  };
}

// WebSocket Message Types
export interface WebSocketMessage {
  type: string;
  payload: any;
  timestamp: string;
  client_id?: string;
}

export interface InlineEditMessage extends WebSocketMessage {
  type: 'inline_edit_response' | 'ghost_suggestion' | 'workflow_update';
  payload: {
    request_id: string;
    response?: InlineEditResponse;
    ghost_text?: GhostTextSuggestion;
    workflow?: RefinementWorkflow;
  };
}

// Function Types
export type EditHandler = (request: InlineEditRequest) => Promise<InlineEditResponse>;
export type GhostActionHandler = (action: GhostActionRequest) => Promise<any>;
export type KeyboardShortcutHandler = (event: KeyboardEvent) => void;
export type DragDropHandler = (items: ContextItem[]) => void;
export type WorkflowStepHandler = (step: number, workflow: RefinementWorkflow) => void;

// Alpine.js Store Type
export interface TorqConsoleStore {
  // Inline editor state
  showInlineEditorPanel: boolean;
  inlineEditMode: EditMode;
  inlineEditAction: EditAction;
  inlineEditPrompt: string;
  inlineEditResult: string;
  inlineEditAlternatives: string[];
  currentSelection: EditSelection | null;
  activeGhostText: GhostTextSuggestion | null;
  draggedContext: ContextItem[];
  workflowStep: number;

  // Methods
  showInlineEditor(): void;
  hideInlineEditor(): void;
  handleKeyboardShortcuts(event: KeyboardEvent): void;
  executeInlineEdit(): Promise<void>;
  quickAction(action: QuickAction): void;
  acceptInlineEdit(): void;
  rejectInlineEdit(): void;
  refineInlineEdit(): void;
  selectAlternative(index: number): void;
  formatInlineResult(result: string): string;
  quickQuestion(): void;
  acceptGhostText(): void;
  dismissGhostText(): void;
  getGhostTextStyle(): { left: string; top: string };
  showCodeActions(): void;
  showQuickFix(): void;
  handleDragOver(event: DragEvent): void;
  handleDragLeave(event: DragEvent): void;
  handleContextDrop(event: DragEvent): void;
  updateEditMode(): void;
  addMessageToChat(role: string, content: string): void;
  animateWorkflowProgress(): Promise<void>;
}

// Export all types
export {
  EditMode,
  EditAction,
  GhostTextSource,
  EditSelection,
  GhostTextSuggestion,
  InlineEditRequest,
  InlineEditResponse,
  WorkflowStep,
  RefinementWorkflow,
  ContextItem,
  DraggedContext,
  KeyboardShortcut,
  ShortcutMap,
  APIResponse,
  GhostActionRequest,
  InlineEditStats,
  InlineEditorState,
  InlineEditEvent,
  InlineEditorProps,
  GhostTextProps,
  CodeEditorProps,
  WorkflowDisplayProps,
  QuickAction,
  QuickActionDefinition,
  InlineEditError,
  ValidationError,
  InlineEditorConfig,
  WebSocketMessage,
  InlineEditMessage,
  EditHandler,
  GhostActionHandler,
  KeyboardShortcutHandler,
  DragDropHandler,
  WorkflowStepHandler,
  TorqConsoleStore
};

// Global declarations for Alpine.js integration
declare global {
  interface Window {
    torqConsole: () => TorqConsoleStore;
    Alpine: any;
  }
}

// Constants
export const DEFAULT_SHORTCUTS: ShortcutMap = {
  'ctrl+k': {
    key: 'k',
    ctrl: true,
    description: 'Open inline editor',
    handler: 'showInlineEditor'
  },
  'alt+enter': {
    key: 'Enter',
    alt: true,
    description: 'Quick question mode',
    handler: 'quickQuestion'
  },
  'tab': {
    key: 'Tab',
    description: 'Accept ghost text',
    handler: 'acceptGhostText'
  },
  'escape': {
    key: 'Escape',
    description: 'Dismiss ghost text',
    handler: 'dismissGhostText'
  },
  'ctrl+.': {
    key: '.',
    ctrl: true,
    description: 'Show code actions',
    handler: 'showCodeActions'
  },
  'ctrl+shift+i': {
    key: 'I',
    ctrl: true,
    shift: true,
    description: 'Show quick fix',
    handler: 'showQuickFix'
  },
  'f2': {
    key: 'F2',
    description: 'Rename symbol',
    handler: 'renameSymbol'
  }
};

export const QUICK_ACTIONS: QuickActionDefinition[] = [
  {
    id: 'add_docstring',
    label: 'Add Docstring',
    icon: '📝',
    prompt: 'Add comprehensive docstring with parameters and return value',
    action: 'refine'
  },
  {
    id: 'add_type_hints',
    label: 'Add Type Hints',
    icon: '🏷️',
    prompt: 'Add type hints to function parameters and return type',
    action: 'refine'
  },
  {
    id: 'refactor',
    label: 'Refactor',
    icon: '🔧',
    prompt: 'Refactor this code for better readability and maintainability',
    action: 'refine'
  },
  {
    id: 'explain',
    label: 'Explain',
    icon: '💡',
    prompt: 'Explain what this code does and how it works',
    action: 'explain'
  },
  {
    id: 'optimize',
    label: 'Optimize',
    icon: '⚡',
    prompt: 'Optimize this code for better performance',
    action: 'refine'
  }
];

export const EDIT_MODES: Record<EditMode, string> = {
  selection: 'Selection Edit',
  cursor: 'Cursor Complete',
  ghost_text: 'Ghost Text',
  quick_question: 'Quick Question',
  refinement: 'Refinement'
};

export const EDIT_ACTIONS: Record<EditAction, string> = {
  generate: 'Generate',
  refine: 'Refine',
  explain: 'Explain',
  complete: 'Complete',
  transform: 'Transform',
  review: 'Review'
};