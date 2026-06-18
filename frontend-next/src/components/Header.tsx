'use client';

import { Shield, RotateCcw } from 'lucide-react';
import { ConversationPhase } from '@/types';

interface HeaderProps {
  phase: ConversationPhase;
  onReset: () => void;
}

const phaseLabels: Record<ConversationPhase, string> = {
  start: 'Ready to help',
  greeting: 'Getting started',
  gathering: 'Understanding your situation',
  extracting: 'Analyzing details',
  analyzing: 'Security analysis',
  matching: 'Finding experts',
  presenting: 'Expert recommendations',
  selecting: 'Selecting expert',
  handoff: 'Connecting you',
  complete: 'Connected!',
};

export function Header({ phase, onReset }: HeaderProps) {
  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
      <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
        {/* Logo & Title */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg">
            <Shield size={22} className="text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-gray-900">CyberSecAgent</h1>
            <p className="text-xs text-gray-500">{phaseLabels[phase]}</p>
          </div>
        </div>

        {/* Phase Indicator & Reset */}
        <div className="flex items-center gap-4">
          {/* Phase dots */}
          <div className="hidden sm:flex items-center gap-1">
            {(['gathering', 'analyzing', 'presenting', 'complete'] as const).map(
              (p, i) => {
                const phases: ConversationPhase[] = [
                  'start',
                  'greeting',
                  'gathering',
                  'extracting',
                  'analyzing',
                  'matching',
                  'presenting',
                  'selecting',
                  'handoff',
                  'complete',
                ];
                const currentIndex = phases.indexOf(phase);
                const targetIndex = phases.indexOf(p);
                const isActive = currentIndex >= targetIndex;
                const isCurrent = phase === p;

                return (
                  <div
                    key={p}
                    className={`w-2 h-2 rounded-full transition-colors ${
                      isCurrent
                        ? 'bg-primary-600 scale-125'
                        : isActive
                        ? 'bg-primary-400'
                        : 'bg-gray-200'
                    }`}
                  />
                );
              }
            )}
          </div>

          {/* Reset Button */}
          <button
            onClick={onReset}
            className="flex items-center gap-2 px-3 py-2 text-sm text-gray-600
                       hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <RotateCcw size={16} />
            <span className="hidden sm:inline">New Chat</span>
          </button>
        </div>
      </div>
    </header>
  );
}
