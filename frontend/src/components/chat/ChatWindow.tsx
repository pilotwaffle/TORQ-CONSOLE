import React, { useEffect, useRef } from 'react';
import { ChatMessage } from './ChatMessage';
import { ChatInput } from './ChatInput';
import { useAgentStore } from '@/stores/agentStore';

export const ChatWindow: React.FC = () => {
  const { sessions, activeSessionId, agents, addMessage } = useAgentStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const activeSession = sessions.find((s) => s.id === activeSessionId);
  const activeAgent = agents.find((a) => a.id === activeSession?.agentId);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [activeSession?.messages]);

  const handleSend = (message: string) => {
    if (!activeSessionId) return;

    const newMessage = {
      id: `msg_${Date.now()}`,
      agentId: activeSession?.agentId || '',
      type: 'text' as const,
      content: message,
      timestamp: Date.now(),
    };

    addMessage(activeSessionId, newMessage);

    // Simulate agent response (will be replaced with actual WebSocket integration)
    setTimeout(() => {
      const response = {
        id: `msg_${Date.now()}`,
        agentId: activeSession?.agentId || '',
        type: 'text' as const,
        content: 'This is a simulated response. Backend integration coming soon!',
        timestamp: Date.now(),
      };
      addMessage(activeSessionId, response);
    }, 1000);
  };

  if (!activeSession) {
    return (
      <div className="flex-1 flex items-center justify-center bg-bg-primary">
        <div className="text-center">
          <div className="text-4xl mb-4">💬</div>
          <h3 className="text-h3 text-text-secondary mb-2">No Active Chat</h3>
          <p className="text-small text-text-muted">
            Select an agent from the sidebar to start chatting
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col bg-bg-primary">
      {/* Chat header */}
      <div className="h-14 bg-bg-secondary border-b border-border flex items-center px-4">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-accent-primary flex items-center justify-center text-small font-semibold">
            {activeAgent?.name.slice(0, 2).toUpperCase() || 'AG'}
          </div>
          <div>
            <h3 className="text-body font-medium">{activeAgent?.name || 'Agent'}</h3>
            <p className="text-small text-text-muted">
              {activeAgent?.capabilities.join(', ') || 'No capabilities'}
            </p>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto scrollbar-thin">
        {activeSession.messages.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <p className="text-text-muted text-small">
                Start a conversation with {activeAgent?.name || 'the agent'}
              </p>
            </div>
          </div>
        ) : (
          <div className="divide-y divide-border">
            {activeSession.messages.map((message) => (
              <ChatMessage
                key={message.id}
                message={message}
                agentName={activeAgent?.name || 'Agent'}
              />
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input */}
      <ChatInput onSend={handleSend} disabled={!activeAgent} />
    </div>
  );
};
