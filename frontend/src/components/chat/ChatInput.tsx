import React, { useState } from 'react';
import { Button } from '@/components/ui';

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

export const ChatInput: React.FC<ChatInputProps> = ({ onSend, disabled = false }) => {
  const [input, setInput] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !disabled) {
      onSend(input.trim());
      setInput('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handlePaste = (e: React.ClipboardEvent<HTMLTextAreaElement>) => {
    // Prevent default paste behavior to avoid conflicts
    e.preventDefault();

    // Get pasted content and insert it manually
    const pastedText = e.clipboardData.getData('text');
    const textarea = e.currentTarget;
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const currentValue = input;

    // Insert pasted text at cursor position
    const newValue =
      currentValue.substring(0, start) + pastedText + currentValue.substring(end);

    setInput(newValue);

    // Set cursor position after pasted text
    setTimeout(() => {
      textarea.selectionStart = textarea.selectionEnd = start + pastedText.length;
      textarea.focus();
    }, 0);
  };

  return (
    <form onSubmit={handleSubmit} className="border-t border-border bg-bg-secondary p-4">
      <div className="flex gap-2">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          onPaste={handlePaste}
          placeholder="Ask an agent anything... (Shift+Enter for new line)"
          disabled={disabled}
          className="flex-1 bg-bg-tertiary text-text-primary rounded-md px-3 py-2 text-body resize-none focus:outline-none focus:ring-2 focus:ring-border-focus disabled:opacity-50"
          rows={3}
        />
        <Button
          type="submit"
          disabled={disabled || !input.trim()}
          className="self-end"
        >
          Send
        </Button>
      </div>
      <div className="mt-2 text-small text-text-muted">
        Tip: Use @ to mention specific agents or files
      </div>
    </form>
  );
};
