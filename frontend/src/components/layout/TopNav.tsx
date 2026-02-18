import React from 'react';
import { Badge, Button, TorqLogo } from '@/components/ui';
import { useAgentStore } from '@/stores/agentStore';

export const TopNav: React.FC = () => {
  const { workspace, isConnected } = useAgentStore();

  return (
    <div className="h-12 bg-bg-secondary border-b border-border flex items-center justify-between px-4">
      <div className="flex items-center gap-3">
        <TorqLogo size="sm" />
        <h1 className="text-h3 font-semibold text-torq-accent">TORQ Console</h1>
        {workspace && (
          <span className="text-text-muted text-small">
            {workspace.name}
          </span>
        )}
      </div>

      <div className="flex items-center gap-3">
        <Badge variant={isConnected ? 'success' : 'error'}>
          {isConnected ? 'Connected' : 'Disconnected'}
        </Badge>

        <Button variant="ghost" size="icon">
          <svg
            width="16"
            height="16"
            viewBox="0 0 16 16"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M8 4V8L11 11"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <circle
              cx="8"
              cy="8"
              r="6"
              stroke="currentColor"
              strokeWidth="1.5"
            />
          </svg>
        </Button>

        <Button variant="ghost" size="icon">
          <svg
            width="16"
            height="16"
            viewBox="0 0 16 16"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M8 2C8.39397 2 8.78407 2.0776 9.14805 2.22836C9.51203 2.37913 9.84274 2.6001 10.1213 2.87868C10.3999 3.15726 10.6209 3.48797 10.7716 3.85195C10.9224 4.21593 11 4.60603 11 5"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
            />
            <path
              d="M2 8C2 4.68629 4.68629 2 8 2C11.3137 2 14 4.68629 14 8"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
            />
          </svg>
        </Button>
      </div>
    </div>
  );
};
