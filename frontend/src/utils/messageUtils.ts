/**
 * Phase 2 - Chat System Integrity
 *
 * Message utilities for deduplication and safe message handling.
 */

import type { ChatMessage, MessageInsertResult, Message } from '@/types/chat';
import { generateMessageId, isValidMessageId } from '@/types/chat';

/**
 * Check if two messages are the same by ID
 */
export function isSameMessage(a: ChatMessage | Message, b: ChatMessage | Message): boolean {
  const aId = 'message_id' in a ? a.message_id : a.id;
  const bId = 'message_id' in b ? b.message_id : b.id;
  return aId === bId;
}

/**
 * Check if a message already exists in a list
 */
export function hasMessage(
  messages: (ChatMessage | Message)[],
  targetMessage: ChatMessage | Message
): boolean {
  const targetId = 'message_id' in targetMessage ? targetMessage.message_id : targetMessage.id;

  return messages.some((msg) => {
    const msgId = 'message_id' in msg ? msg.message_id : msg.id;
    return msgId === targetId;
  });
}

/**
 * Find a message by ID in a list
 */
export function findMessageById(
  messages: (ChatMessage | Message)[],
  messageId: string
): ChatMessage | Message | undefined {
  return messages.find((msg) => {
    const msgId = 'message_id' in msg ? msg.message_id : msg.id;
    return msgId === messageId;
  });
}

/**
 * Insert a message if it doesn't already exist (deduplication)
 *
 * This is the primary method for adding messages to prevent duplicates.
 *
 * @param messages - Current message list
 * @param message - Message to insert
 * @returns Result with inserted status and the message (or existing)
 */
export function insertMessageIfMissing(
  messages: ChatMessage[],
  message: ChatMessage
): MessageInsertResult {
  // Validate message ID
  if (!message.message_id || !isValidMessageId(message.message_id)) {
    return {
      inserted: false,
      message: null,
      reason: 'invalid',
    };
  }

  // Check for duplicate
  const existing = findMessageById(messages, message.message_id);
  if (existing) {
    return {
      inserted: false,
      message: existing as ChatMessage,
      reason: 'duplicate',
    };
  }

  // Insert the message
  return {
    inserted: true,
    message,
    reason: 'success',
  };
}

/**
 * Insert multiple messages with deduplication
 *
 * @param messages - Current message list
 * @param newMessages - Messages to insert
 * @returns Updated message list with only new messages added
 */
export function insertMessagesIfMissing(
  messages: ChatMessage[],
  newMessages: ChatMessage[]
): ChatMessage[] {
  const result = [...messages];
  const insertedIds = new Set<string>();

  for (const msg of newMessages) {
    const { inserted, message, reason } = insertMessageIfMissing(result, msg);

    if (inserted && message) {
      result.push(message);
      insertedIds.add(message.message_id);
    }
  }

  return result;
}

/**
 * Create a user message with proper UUID
 */
export function createUserMessage(
  content: string,
  sessionId: string,
  agentId: string
): ChatMessage {
  return {
    message_id: generateMessageId(),
    session_id: sessionId,
    role: 'user',
    agent_id: agentId,
    timestamp: Date.now(),
    content,
    type: 'text',
    streaming: 'complete',
  };
}

/**
 * Create an assistant message with proper UUID
 */
export function createAssistantMessage(
  content: string,
  sessionId: string,
  agentId: string,
  options: {
    type?: 'text' | 'code' | 'diff' | 'error' | 'system';
    mode?: string;
    metadata?: Record<string, unknown>;
  } = {}
): ChatMessage {
  return {
    message_id: generateMessageId(),
    session_id: sessionId,
    role: 'assistant',
    agent_id: agentId,
    timestamp: Date.now(),
    content,
    type: options.type || 'text',
    mode: options.mode,
    streaming: 'complete',
    metadata: options.metadata,
  };
}

/**
 * Create a streaming placeholder message
 *
 * This creates an initial message that will be updated as streaming progresses.
 */
export function createStreamingMessage(
  sessionId: string,
  agentId: string,
  options: {
    mode?: string;
  } = {}
): ChatMessage {
  return {
    message_id: generateMessageId(),
    session_id: sessionId,
    role: 'assistant',
    agent_id: agentId,
    timestamp: Date.now(),
    content: '',
    type: 'text',
    mode: options.mode,
    streaming: 'streaming',
  };
}

/**
 * Update a streaming message with new content
 *
 * @param message - The streaming message to update
 * @param content - New content to append
 * @returns Updated message
 */
export function updateStreamingMessage(
  message: ChatMessage,
  content: string
): ChatMessage {
  return {
    ...message,
    content: message.content + content,
    timestamp: Date.now(), // Update timestamp to show activity
  };
}

/**
 * Mark a streaming message as complete
 *
 * @param message - The streaming message to complete
 * @returns Completed message
 */
export function completeStreamingMessage(
  message: ChatMessage,
  finalContent?: string
): ChatMessage {
  return {
    ...message,
    content: finalContent !== undefined ? finalContent : message.content,
    streaming: 'complete',
    timestamp: Date.now(),
  };
}

/**
 * Mark a streaming message as errored
 *
 * @param message - The streaming message that errored
 * @param error - Error message
 * @returns Errored message
 */
export function errorStreamingMessage(
  message: ChatMessage,
  error: string
): ChatMessage {
  return {
    ...message,
    content: `⚠️ ${error}`,
    type: 'error',
    streaming: 'error',
    timestamp: Date.now(),
  };
}

/**
 * Sort messages by timestamp
 */
export function sortMessagesByTimestamp(
  messages: ChatMessage[]
): ChatMessage[] {
  return [...messages].sort((a, b) => a.timestamp - b.timestamp);
}

/**
 * Group messages by role for rendering optimizations
 */
export function groupMessagesByRole(
  messages: ChatMessage[]
): Map<'user' | 'assistant' | 'system', ChatMessage[]> {
  const groups = new Map<'user' | 'assistant' | 'system', ChatMessage[]>();

  for (const msg of messages) {
    const role = msg.role;
    if (!groups.has(role)) {
      groups.set(role, []);
    }
    groups.get(role)!.push(msg);
  }

  return groups;
}

/**
 * Check if a session is empty (no user messages)
 */
export function isSessionEmpty(session: { messages: ChatMessage[] }): boolean {
  return !session.messages.some((m) => m.role === 'user');
}

/**
 * Get last user message from a session
 */
export function getLastUserMessage(session: { messages: ChatMessage[] }): ChatMessage | null {
  const userMessages = session.messages
    .filter((m) => m.role === 'user')
    .sort((a, b) => b.timestamp - a.timestamp);

  return userMessages[0] || null;
}

/**
 * Get last assistant message from a session
 */
export function getLastAssistantMessage(session: { messages: ChatMessage[] }): ChatMessage | null {
  const assistantMessages = session.messages
    .filter((m) => m.role === 'assistant')
    .sort((a, b) => b.timestamp - a.timestamp);

  return assistantMessages[0] || null;
}

/**
 * Create a system notification message
 */
export function createSystemMessage(
  content: string,
  sessionId: string,
  agentId: string
): ChatMessage {
  return {
    message_id: generateMessageId(),
    session_id: sessionId,
    role: 'system',
    agent_id: agentId,
    timestamp: Date.now(),
    content,
    type: 'system',
    streaming: 'complete',
  };
}

/**
 * Calculate message display name
 */
export function getMessageDisplayName(
  message: ChatMessage,
  agentName?: string
): string {
  switch (message.role) {
    case 'user':
      return 'You';
    case 'system':
      return 'System';
    case 'assistant':
      return agentName || 'Assistant';
    default:
      return 'Unknown';
  }
}

/**
 * Truncate content for previews
 */
export function truncateContent(
  content: string,
  maxLength: number = 100
): string {
  if (content.length <= maxLength) {
    return content;
  }
  return content.substring(0, maxLength) + '...';
}

/**
 * Extract code blocks from message content
 */
export function extractCodeBlocks(content: string): string[] {
  const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g;
  const blocks: string[] = [];
  let match;

  while ((match = codeBlockRegex.exec(content)) !== null) {
    blocks.push(match[2]);
  }

  return blocks;
}

/**
 * Format message content for display
 * Handles basic markdown-like formatting
 */
export function formatMessageContent(content: string): string {
  // Escape HTML
  let formatted = content
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  // Convert code blocks
  formatted = formatted.replace(
    /```(\w+)?\n([\s\S]*?)```/g,
    '<pre><code class="language-$1">$2</code></pre>'
  );

  // Convert inline code
  formatted = formatted.replace(/`([^`]+)`/g, '<code>$1</code>');

  // Convert bold
  formatted = formatted.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

  // Convert italic
  formatted = formatted.replace(/\*([^*]+)\*/g, '<em>$1</em>');

  return formatted;
}

/**
 * Validate message object
 */
export function validateMessage(message: unknown): message is ChatMessage {
  if (!message || typeof message !== 'object') {
    return false;
  }

  const msg = message as Record<string, unknown>;

  return (
    typeof msg.message_id === 'string' &&
    typeof msg.session_id === 'string' &&
    typeof msg.role === 'string' &&
    typeof msg.agent_id === 'string' &&
    typeof msg.content === 'string' &&
    typeof msg.timestamp === 'number'
  );
}

/**
 * Export all utilities as a named object for easier importing
 */
export const messageUtils = {
  isSameMessage,
  hasMessage,
  findMessageById,
  insertMessageIfMissing,
  insertMessagesIfMissing,
  createUserMessage,
  createAssistantMessage,
  createStreamingMessage,
  updateStreamingMessage,
  completeStreamingMessage,
  errorStreamingMessage,
  sortMessagesByTimestamp,
  groupMessagesByRole,
  isSessionEmpty,
  getLastUserMessage,
  getLastAssistantMessage,
  createSystemMessage,
  getMessageDisplayName,
  truncateContent,
  extractCodeBlocks,
  formatMessageContent,
  validateMessage,
};

export default messageUtils;
