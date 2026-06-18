'use client';

import { useState, KeyboardEvent, FormEvent } from 'react';
import { Send, Loader2 } from 'lucide-react';

interface ChatInputProps {
  onSend: (message: string) => void;
  isLoading: boolean;
  disabled?: boolean;
  placeholder?: string;
}

export function ChatInput({
  onSend,
  isLoading,
  disabled = false,
  placeholder = 'Type your message...',
}: ChatInputProps) {
  const [input, setInput] = useState('');

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isLoading && !disabled) {
      onSend(input.trim());
      setInput('');
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="border-t border-gray-200 p-4 bg-white">
      <div className="flex items-end gap-3 max-w-4xl mx-auto">
        <div className="flex-1 relative">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={isLoading || disabled}
            rows={1}
            className="w-full resize-none rounded-xl border border-gray-300 px-4 py-3 pr-12
                       focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent
                       disabled:bg-gray-100 disabled:cursor-not-allowed
                       text-gray-800 placeholder-gray-400
                       min-h-[48px] max-h-[200px]"
            style={{
              height: 'auto',
              overflow: 'hidden',
            }}
            onInput={(e) => {
              const target = e.target as HTMLTextAreaElement;
              target.style.height = 'auto';
              target.style.height = Math.min(target.scrollHeight, 200) + 'px';
            }}
          />
        </div>

        <button
          type="submit"
          disabled={!input.trim() || isLoading || disabled}
          className="flex-shrink-0 w-12 h-12 rounded-xl bg-primary-600 text-white
                     flex items-center justify-center
                     hover:bg-primary-700 transition-colors
                     disabled:bg-gray-300 disabled:cursor-not-allowed
                     focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
        >
          {isLoading ? (
            <Loader2 size={20} className="animate-spin" />
          ) : (
            <Send size={20} />
          )}
        </button>
      </div>
    </form>
  );
}
