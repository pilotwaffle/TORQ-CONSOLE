/**
 * Phase 2 - Chat System Integrity
 *
 * Standardized chat type definitions with UUID-based IDs,
 * streaming support, and proper message deduplication.
 */

/**
 * Message role types
 */
export type MessageRole = 'user' | 'assistant' | 'system';

/**
 * Message types for different content formats
 */
export type MessageType = 'text' | 'code' | 'diff' | 'error' | 'system';

/**
 * Streaming status for messages
 */
export type StreamingStatus = 'idle' | 'streaming' | 'complete' | 'error';

/**
 * Standardized Message Schema
 *
 * All messages must use UUID for message_id to prevent duplicates.
 */
export interface ChatMessage {
  // Unique identifier - MUST use UUID, never timestamp
  message_id: string;

  // Session this message belongs to
  session_id: string;

  // Who sent this message
  role: MessageRole;

  // Which agent handled this message (for assistant role)
  agent_id: string;

  // Mode of generation (single_agent, multi_agent, etc.)
  mode?: string;

  // When the message was created
  timestamp: number;

  // Message content
  content: string;

  // Type of message for rendering
  type: MessageType;

  // Streaming state (for responses)
  streaming?: StreamingStatus;

  // Optional metadata
  metadata?: {
    language?: string;
    filePath?: string;
    diff?: DiffBlock;
    token_count?: number;
    model?: string;
    [key: string]: unknown;
  };
}

/**
 * Chat session with standardized message schema
 */
export interface ChatSession {
  id: string;
  title: string;
  agentId: string;
  messages: ChatMessage[];
  createdAt: number;
  updatedAt: number;

  // Agent typing state
  isTyping?: boolean;

  // Current streaming message ID (if any)
  streamingMessageId?: string | null;
}

/**
 * Diff block for code change messages
 */
export interface DiffBlock {
  additions: number;
  deletions: number;
  hunks: DiffHunk[];
}

/**
 * Diff hunk for line-by-line changes
 */
export interface DiffHunk {
  oldStart: number;
  oldLines: number;
  newStart: number;
  newLines: number;
  lines: DiffLine[];
}

/**
 * Individual diff line
 */
export interface DiffLine {
  type: 'add' | 'remove' | 'context';
  content: string;
  lineNumber?: number;
}

/**
 * Typing indicator state
 */
export interface TypingState {
  isTyping: boolean;
  agentId: string | null;
  agentName?: string;
  startedAt: number;
}

/**
 * Message deduplication result
 */
export interface MessageInsertResult {
  inserted: boolean;
  message: ChatMessage | null;
  reason?: 'duplicate' | 'invalid' | 'success';
}

/**
 * Generate a unique message ID using crypto API
 * Falls back to timestamp + random if crypto unavailable
 */
export function generateMessageId(): string {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return `msg_${crypto.randomUUID()}`;
  }

  // Fallback for older browsers
  return `msg_${Date.now()}_${Math.random().toString(36).substring(2, 11)}`;
}

/**
 * Generate a unique session ID
 */
export function generateSessionId(): string {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return `session_${crypto.randomUUID()}`;
  }

  return `session_${Date.now()}_${Math.random().toString(36).substring(2, 11)}`;
}

/**
 * Check if a message ID is a valid UUID-based ID
 */
export function isValidMessageId(id: string): boolean {
  return id.startsWith('msg_') && id.length > 10;
}

/**
 * Legacy Message interface (for backward compatibility)
 * @deprecated Use ChatMessage instead
 */
export interface Message {
  id: string;
  agentId: string;
  type: 'text' | 'code' | 'diff' | 'error' | 'system';
  content: string;
  timestamp: number;
  metadata?: {
    language?: string;
    filePath?: string;
    diff?: DiffBlock;
  };
}

/**
 * Convert legacy Message to ChatMessage
 */
export function legacyToChatMessage(legacy: Message, sessionId: string): ChatMessage {
  return {
    message_id: legacy.id,
    session_id: sessionId,
    role: legacy.agentId === 'user' ? 'user' : 'assistant',
    agent_id: legacy.agentId,
    timestamp: legacy.timestamp,
    content: legacy.content,
    type: legacy.type,
    streaming: 'complete',
    metadata: legacy.metadata,
  };
}

/**
 * Convert ChatMessage to legacy Message
 */
export function chatToLegacyMessage(chat: ChatMessage): Message {
  return {
    id: chat.message_id,
    agentId: chat.agent_id,
    type: chat.type,
    content: chat.content,
    timestamp: chat.timestamp,
    metadata: chat.metadata,
  };
}
