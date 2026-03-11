/**
 * Phase 3: Product UX & Identity
 *
 * Empty State Component for Chat
 * Shown when chat has no messages
 */

import { MessageSquare, Sparkles } from 'lucide-react';

interface ChatEmptyStateProps {
  agentName?: string;
  isFirstMessage?: boolean;
}

export function ChatEmptyState({ agentName = 'Prince Flowers', isFirstMessage = false }: ChatEmptyStateProps) {
  const suggestions = [
    'Search for the latest AI research trends',
    'Help me write a React component with TypeScript',
    'Explain the difference between REST and GraphQL',
    'Create a Python script for data visualization',
  ];

  return (
    <div className="flex flex-col items-center justify-center h-full px-8 py-12">
      {/* Icon */}
      <div className="w-16 h-16 bg-gradient-to-br from-blue-100 to-purple-100 rounded-full flex items-center justify-center mb-6">
        {isFirstMessage ? (
          <Sparkles className="w-8 h-8 text-blue-600" />
        ) : (
          <MessageSquare className="w-8 h-8 text-blue-600" />
        )}
      </div>

      {/* Heading */}
      {isFirstMessage ? (
        <>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            Welcome to TORQ Console
          </h2>
          <p className="text-gray-500 text-center max-w-md mb-6">
            Start a conversation with {agentName}. Ask anything about code, research,
            or let {agentName} coordinate specialized agents to help you build faster.
          </p>
        </>
      ) : (
        <>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            Start a conversation
          </h2>
          <p className="text-gray-500 text-center max-w-md mb-6">
            Ask {agentName} anything. From code reviews to research synthesis,
            multiple AI agents are ready to help.
          </p>
        </>
      )}

      {/* Suggestions */}
      <div className="w-full max-w-lg">
        <p className="text-sm font-medium text-gray-700 mb-3 text-center">Try asking:</p>
        <div className="grid grid-cols-2 gap-2">
          {suggestions.map((suggestion, i) => (
            <button
              key={i}
              className="text-left px-4 py-3 bg-gray-50 hover:bg-gray-100 rounded-xl text-sm text-gray-700 transition-colors text-left"
              onClick={() => {
                // This will be handled by parent component
                const event = new CustomEvent('suggestion-click', { detail: suggestion });
                window.dispatchEvent(event);
              }}
            >
              "{suggestion}"
            </button>
          ))}
        </div>
      </div>

      {/* Capabilities hint */}
      <div className="mt-8 flex flex-wrap justify-center gap-2">
        {['Web Search', 'Code Generation', 'Analysis', 'Orchestration'].map((cap) => (
          <span
            key={cap}
            className="px-3 py-1 bg-blue-50 text-blue-700 text-xs font-medium rounded-full"
          >
            {cap}
          </span>
        ))}
      </div>
    </div>
  );
}
