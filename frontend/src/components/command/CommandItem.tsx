import React from 'react';
import { LucideIcon } from 'lucide-react';
import { formatShortcut, KeyboardShortcut } from '@/hooks/useKeyboardShortcuts';

export interface CommandItemProps {
  id: string;
  title: string;
  category: string;
  icon: LucideIcon;
  shortcut?: KeyboardShortcut;
  selected?: boolean;
  onClick: () => void;
  metadata?: {
    description?: string;
    badge?: string;
  };
}

export function CommandItem({
  title,
  category,
  icon: Icon,
  shortcut,
  selected = false,
  onClick,
  metadata,
}: CommandItemProps) {
  return (
    <button
      onClick={onClick}
      className={`
        w-full flex items-center gap-3 px-4 py-3 text-left
        transition-all duration-150 ease-out
        border-l-2
        ${
          selected
            ? 'bg-bg-tertiary border-l-torq-accent text-text-primary'
            : 'border-l-transparent hover:bg-bg-secondary text-text-secondary hover:text-text-primary'
        }
        group cursor-pointer
      `}
    >
      {/* Icon */}
      <div
        className={`
        flex-shrink-0 w-8 h-8 rounded-md flex items-center justify-center
        transition-colors duration-150
        ${selected ? 'bg-torq-accent/20 text-torq-accent' : 'bg-bg-primary text-text-muted group-hover:text-torq-accent'}
      `}
      >
        <Icon size={16} />
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-body font-medium truncate">{title}</span>
          {metadata?.badge && (
            <span className="px-1.5 py-0.5 text-xs font-medium rounded bg-bg-primary text-text-muted border border-border">
              {metadata.badge}
            </span>
          )}
        </div>
        {metadata?.description && (
          <p className="text-small text-text-muted truncate mt-0.5">{metadata.description}</p>
        )}
      </div>

      {/* Category & Shortcut */}
      <div className="flex-shrink-0 flex items-center gap-3">
        <span className="text-small text-text-muted">{category}</span>
        {shortcut && (
          <kbd
            className={`
            px-2 py-1 text-xs font-mono rounded border
            transition-colors duration-150
            ${
              selected
                ? 'bg-bg-primary border-border-focus text-text-primary'
                : 'bg-bg-primary border-border text-text-muted'
            }
          `}
          >
            {formatShortcut(shortcut)}
          </kbd>
        )}
      </div>
    </button>
  );
}
