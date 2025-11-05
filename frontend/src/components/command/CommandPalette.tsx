import React, { useState, useEffect, useRef, useMemo } from 'react';
import { createPortal } from 'react-dom';
import {
  Search,
  MessageSquarePlus,
  ArrowLeftRight,
  Trash2,
  Download,
  Settings,
  Palette,
  Bot,
  Code,
  Bug,
  FileText,
  TestTube,
  GitBranch,
  Lightbulb,
  Clock,
} from 'lucide-react';
import { useAgentStore } from '@/stores/agentStore';
import { CommandItem, CommandItemProps } from './CommandItem';
import { useKeyboardShortcuts, SHORTCUTS } from '@/hooks/useKeyboardShortcuts';
import type { Agent } from '@/lib/types';

interface Command extends Omit<CommandItemProps, 'selected' | 'onClick'> {
  keywords?: string[];
  action: () => void;
  recent?: boolean;
}

const AGENT_ICONS: Record<Agent['type'], typeof Bot> = {
  code: Code,
  debug: Bug,
  docs: FileText,
  test: TestTube,
  architecture: GitBranch,
  research: Lightbulb,
};

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
}

export function CommandPalette({ isOpen, onClose }: CommandPaletteProps) {
  const [search, setSearch] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [recentCommands, setRecentCommands] = useState<string[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  const { agents, addSession, setActiveSession, activeSessionId, sessions } = useAgentStore();

  // Load recent commands from localStorage
  useEffect(() => {
    const stored = localStorage.getItem('torq-recent-commands');
    if (stored) {
      try {
        setRecentCommands(JSON.parse(stored));
      } catch (e) {
        console.error('Failed to parse recent commands:', e);
      }
    }
  }, []);

  // Save recent command
  const saveRecentCommand = (commandId: string) => {
    const updated = [commandId, ...recentCommands.filter((id) => id !== commandId)].slice(0, 5);
    setRecentCommands(updated);
    localStorage.setItem('torq-recent-commands', JSON.stringify(updated));
  };

  // Build commands list
  const commands = useMemo(() => {
    const commandsList: Command[] = [];

    // Agent commands - New Chat
    agents.forEach((agent) => {
      const Icon = AGENT_ICONS[agent.type];
      commandsList.push({
        id: `new-chat-${agent.id}`,
        title: `New Chat with ${agent.name}`,
        category: 'Agents',
        icon: Icon,
        keywords: ['new', 'chat', 'create', agent.name.toLowerCase(), agent.type],
        metadata: {
          description: agent.capabilities.join(', '),
          badge: agent.status,
        },
        action: () => {
          const newSession = {
            id: `session_${Date.now()}`,
            title: `New ${agent.name} Chat`,
            agentId: agent.id,
            messages: [],
            createdAt: Date.now(),
            updatedAt: Date.now(),
          };
          addSession(newSession);
          setActiveSession(newSession.id);
          saveRecentCommand(`new-chat-${agent.id}`);
          onClose();
        },
      });
    });

    // Agent commands - Switch To
    agents.forEach((agent) => {
      const Icon = AGENT_ICONS[agent.type];
      const agentSessions = sessions.filter((s) => s.agentId === agent.id);
      if (agentSessions.length > 0) {
        commandsList.push({
          id: `switch-${agent.id}`,
          title: `Switch to ${agent.name}`,
          category: 'Agents',
          icon: ArrowLeftRight,
          keywords: ['switch', 'change', agent.name.toLowerCase()],
          metadata: {
            description: `${agentSessions.length} active session${agentSessions.length > 1 ? 's' : ''}`,
          },
          action: () => {
            const latestSession = agentSessions.sort((a, b) => b.updatedAt - a.updatedAt)[0];
            if (latestSession) {
              setActiveSession(latestSession.id);
              saveRecentCommand(`switch-${agent.id}`);
              onClose();
            }
          },
        });
      }
    });

    // Session commands
    if (activeSessionId) {
      commandsList.push(
        {
          id: 'clear-chat',
          title: 'Clear Chat',
          category: 'Sessions',
          icon: Trash2,
          keywords: ['clear', 'delete', 'remove', 'chat'],
          metadata: {
            description: 'Clear all messages in current chat',
          },
          action: () => {
            // TODO: Implement clear chat
            console.log('Clear chat');
            saveRecentCommand('clear-chat');
            onClose();
          },
        },
        {
          id: 'export-chat',
          title: 'Export Chat',
          category: 'Sessions',
          icon: Download,
          keywords: ['export', 'download', 'save', 'chat'],
          metadata: {
            description: 'Export chat history as JSON or Markdown',
          },
          action: () => {
            // TODO: Implement export
            console.log('Export chat');
            saveRecentCommand('export-chat');
            onClose();
          },
        }
      );
    }

    // Navigation commands
    commandsList.push({
      id: 'settings',
      title: 'Settings',
      category: 'Navigation',
      icon: Settings,
      shortcut: SHORTCUTS.SETTINGS,
      keywords: ['settings', 'preferences', 'config'],
      metadata: {
        description: 'Open application settings',
      },
      action: () => {
        // TODO: Implement settings
        console.log('Open settings');
        saveRecentCommand('settings');
        onClose();
      },
    });

    // Actions commands
    commandsList.push({
      id: 'toggle-theme',
      title: 'Toggle Theme',
      category: 'Actions',
      icon: Palette,
      keywords: ['theme', 'dark', 'light', 'mode'],
      metadata: {
        description: 'Switch between light and dark theme (Coming Soon)',
        badge: 'Soon',
      },
      action: () => {
        // TODO: Implement theme toggle
        console.log('Toggle theme');
        saveRecentCommand('toggle-theme');
        onClose();
      },
    });

    // Mark recent commands
    return commandsList.map((cmd) => ({
      ...cmd,
      recent: recentCommands.includes(cmd.id),
    }));
  }, [agents, sessions, activeSessionId, recentCommands, addSession, setActiveSession, onClose]);

  // Filter commands based on search
  const filteredCommands = useMemo(() => {
    if (!search.trim()) {
      // Show recent commands first, then all commands
      const recent = commands.filter((cmd) => cmd.recent);
      const rest = commands.filter((cmd) => !cmd.recent);
      return [...recent, ...rest];
    }

    const searchLower = search.toLowerCase();
    return commands
      .map((cmd) => {
        const titleMatch = cmd.title.toLowerCase().includes(searchLower);
        const categoryMatch = cmd.category.toLowerCase().includes(searchLower);
        const keywordMatch = cmd.keywords?.some((kw) => kw.includes(searchLower));
        const descriptionMatch = cmd.metadata?.description?.toLowerCase().includes(searchLower);

        let score = 0;
        if (titleMatch) score += 10;
        if (categoryMatch) score += 5;
        if (keywordMatch) score += 3;
        if (descriptionMatch) score += 1;
        if (cmd.recent) score += 2;

        return { cmd, score };
      })
      .filter(({ score }) => score > 0)
      .sort((a, b) => b.score - a.score)
      .map(({ cmd }) => cmd);
  }, [commands, search]);

  // Group commands by category
  const groupedCommands = useMemo(() => {
    const groups: Record<string, Command[]> = {};

    // Add "Recent" category if we have recent commands and no search
    if (!search.trim() && recentCommands.length > 0) {
      groups['Recent'] = filteredCommands.filter((cmd) => cmd.recent);
    }

    filteredCommands.forEach((cmd) => {
      if (!search.trim() && cmd.recent) return; // Skip, already in Recent

      if (!groups[cmd.category]) {
        groups[cmd.category] = [];
      }
      groups[cmd.category].push(cmd);
    });

    return groups;
  }, [filteredCommands, search, recentCommands]);

  // Reset selection when search changes
  useEffect(() => {
    setSelectedIndex(0);
  }, [search]);

  // Focus input when opened
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
      setSearch('');
      setSelectedIndex(0);
    }
  }, [isOpen]);

  // Scroll selected item into view
  useEffect(() => {
    if (listRef.current && selectedIndex >= 0) {
      const items = listRef.current.querySelectorAll('[data-command-item]');
      const selectedItem = items[selectedIndex];
      if (selectedItem) {
        selectedItem.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
      }
    }
  }, [selectedIndex]);

  // Keyboard navigation
  useKeyboardShortcuts(
    [
      {
        key: 'Escape',
        callback: () => {
          if (isOpen) onClose();
        },
      },
      {
        key: 'ArrowDown',
        callback: (e) => {
          if (isOpen) {
            e.preventDefault();
            setSelectedIndex((prev) => Math.min(prev + 1, filteredCommands.length - 1));
          }
        },
      },
      {
        key: 'ArrowUp',
        callback: (e) => {
          if (isOpen) {
            e.preventDefault();
            setSelectedIndex((prev) => Math.max(prev - 1, 0));
          }
        },
      },
      {
        key: 'Enter',
        callback: (e) => {
          if (isOpen && filteredCommands[selectedIndex]) {
            e.preventDefault();
            filteredCommands[selectedIndex].action();
          }
        },
      },
    ],
    { enabled: isOpen }
  );

  if (!isOpen) return null;

  return createPortal(
    <div
      className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh] px-4 animate-fade-in"
      onClick={onClose}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />

      {/* Command Palette */}
      <div
        className="relative w-full max-w-2xl bg-bg-secondary border border-border rounded-lg shadow-2xl overflow-hidden animate-slide-in"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Search Input */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-border">
          <Search size={18} className="text-text-muted flex-shrink-0" />
          <input
            ref={inputRef}
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Type a command or search..."
            className="flex-1 bg-transparent text-body text-text-primary placeholder:text-text-muted outline-none"
          />
          <kbd className="px-2 py-1 text-xs font-mono rounded border border-border bg-bg-primary text-text-muted">
            ESC
          </kbd>
        </div>

        {/* Commands List */}
        <div ref={listRef} className="max-h-[60vh] overflow-y-auto scrollbar-thin">
          {Object.keys(groupedCommands).length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
              <Search size={48} className="text-text-muted mb-3 opacity-50" />
              <p className="text-body text-text-secondary mb-1">No commands found</p>
              <p className="text-small text-text-muted">Try a different search term</p>
            </div>
          ) : (
            Object.entries(groupedCommands).map(([category, cmds]) => (
              <div key={category}>
                {/* Category Header */}
                <div className="flex items-center gap-2 px-4 py-2 bg-bg-primary sticky top-0 z-10">
                  {category === 'Recent' && <Clock size={14} className="text-text-muted" />}
                  <span className="text-small font-semibold text-text-muted uppercase tracking-wide">
                    {category}
                  </span>
                  <div className="flex-1 h-px bg-border" />
                </div>

                {/* Commands */}
                {cmds.map((cmd, idx) => {
                  const globalIndex = filteredCommands.indexOf(cmd);
                  return (
                    <div key={cmd.id} data-command-item>
                      <CommandItem
                        {...cmd}
                        selected={globalIndex === selectedIndex}
                        onClick={cmd.action}
                      />
                    </div>
                  );
                })}
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-4 py-2 border-t border-border bg-bg-primary">
          <div className="flex items-center gap-4 text-small text-text-muted">
            <span className="flex items-center gap-1.5">
              <kbd className="px-1.5 py-0.5 text-xs font-mono rounded border border-border bg-bg-secondary">
                ↑↓
              </kbd>
              Navigate
            </span>
            <span className="flex items-center gap-1.5">
              <kbd className="px-1.5 py-0.5 text-xs font-mono rounded border border-border bg-bg-secondary">
                ↵
              </kbd>
              Select
            </span>
            <span className="flex items-center gap-1.5">
              <kbd className="px-1.5 py-0.5 text-xs font-mono rounded border border-border bg-bg-secondary">
                ESC
              </kbd>
              Close
            </span>
          </div>
          <span className="text-small text-text-muted">
            {filteredCommands.length} command{filteredCommands.length !== 1 ? 's' : ''}
          </span>
        </div>
      </div>
    </div>,
    document.body
  );
}
