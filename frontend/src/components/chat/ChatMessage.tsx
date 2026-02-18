import React from 'react';
import { Badge } from '@/components/ui';
import { CodeBlock } from './CodeBlock';
import type { Message } from '@/lib/types';

interface ChatMessageProps {
  message: Message;
  agentName: string;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message, agentName }) => {
  const formatTimestamp = (timestamp: number) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const typeColors = {
    text: 'secondary',
    code: 'active',
    diff: 'warning',
    error: 'error',
    system: 'secondary',
  } as const;

  const renderContent = () => {
    switch (message.type) {
      case 'code':
        return (
          <CodeBlock
            code={message.content}
            language={message.metadata?.language}
            fileName={extractFileName(message.metadata?.filePath)}
            filePath={message.metadata?.filePath}
            maxHeight="500px"
            collapsible={true}
            defaultCollapsed={message.content.split('\n').length > 30}
          />
        );

      case 'error':
        return (
          <div className="bg-agent-error/10 border border-agent-error/30 rounded-md p-3">
            <p className="text-agent-error whitespace-pre-wrap break-words">
              {message.content}
            </p>
          </div>
        );

      case 'diff':
        // For diff type, still use CodeBlock with proper language detection
        return (
          <CodeBlock
            code={message.content}
            language="diff"
            fileName={extractFileName(message.metadata?.filePath)}
            filePath={message.metadata?.filePath}
            maxHeight="500px"
            collapsible={true}
          />
        );

      case 'system':
        return (
          <div className="bg-bg-tertiary/50 border border-border rounded-md p-3">
            <p className="text-text-muted text-small whitespace-pre-wrap break-words">
              {message.content}
            </p>
          </div>
        );

      case 'text':
      default:
        return (
          <div className="whitespace-pre-wrap break-words">{message.content}</div>
        );
    }
  };

  return (
    <div className="py-3 px-4 hover:bg-bg-secondary/50 transition-colors">
      <div className="flex items-start gap-3">
        <div className="w-8 h-8 rounded-full bg-accent-primary flex items-center justify-center text-small font-semibold flex-shrink-0">
          {agentName.slice(0, 2).toUpperCase()}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-body font-medium">{agentName}</span>
            <Badge variant={typeColors[message.type]} className="text-xs">
              {message.type}
            </Badge>
            <span className="text-small text-text-muted">
              {formatTimestamp(message.timestamp)}
            </span>
          </div>

          <div className="text-body text-text-secondary">{renderContent()}</div>

          {/* File path metadata (only show if not already in CodeBlock) */}
          {message.metadata?.filePath && message.type !== 'code' && message.type !== 'diff' && (
            <div className="mt-2 text-small text-text-muted">
              File: <span className="font-mono">{message.metadata.filePath}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

/**
 * Extract file name from file path
 */
function extractFileName(filePath?: string): string | undefined {
  if (!filePath) return undefined;

  // Handle both Windows and Unix paths
  const parts = filePath.replace(/\\/g, '/').split('/');
  return parts[parts.length - 1];
}

export default ChatMessage;
