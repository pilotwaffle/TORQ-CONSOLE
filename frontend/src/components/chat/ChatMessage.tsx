import React from 'react';
import { Badge } from '@/components/ui/Badge';
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

          <div className="text-body text-text-secondary">
            {message.type === 'code' ? (
              <pre className="bg-bg-tertiary rounded-md p-3 overflow-x-auto scrollbar-thin font-mono text-code">
                <code>{message.content}</code>
              </pre>
            ) : message.type === 'error' ? (
              <div className="bg-agent-error/10 border border-agent-error/30 rounded-md p-3">
                <p className="text-agent-error">{message.content}</p>
              </div>
            ) : (
              <p className="whitespace-pre-wrap break-words">{message.content}</p>
            )}

            {message.metadata?.filePath && (
              <div className="mt-2 text-small text-text-muted">
                File: <span className="font-mono">{message.metadata.filePath}</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
