'use client';

import { useRef, useEffect, useState } from 'react';
import { useChat } from '@/lib/useChat';
import { Header, ChatMessage, ChatInput, ExpertList } from '@/components';
import { Shield, X, MessageSquare, Mail, Linkedin, Globe, ExternalLink } from 'lucide-react';
import { Expert } from '@/types';

// The seeded network experts are sample profiles with placeholder contact details
// (reserved example.com addresses), so their contact links must not be followed
function hasPlaceholderContact(expert: Expert) {
  return !expert.email || expert.email.endsWith('@example.com');
}

export default function Home() {
  const {
    messages,
    phase,
    isComplete,
    experts,
    isLoading,
    error,
    sendMessage,
    selectExpert,
    resetChat,
  } = useChat();

  const [showExpertPopup, setShowExpertPopup] = useState(false);
  const [selectedExpert, setSelectedExpert] = useState<Expert | null>(null);

  const handleSelectExpert = (expertId: number) => {
    // Keep the expert's details: the list is cleared once the selection completes
    const expert = experts?.find((e) => e.expert.id === expertId)?.expert ?? null;
    setSelectedExpert(expert);
    setShowExpertPopup(expert !== null);
    selectExpert(expertId);
  };

  const whatsappDigits = selectedExpert?.whatsapp?.replace(/\D/g, '');
  const showContactLinks = selectedExpert !== null && !selectedExpert.is_external && !hasPlaceholderContact(selectedExpert);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <Header phase={phase} onReset={resetChat} />

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto">
        {/* Welcome Screen (no messages yet) */}
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full px-4 py-12">
            <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center mb-6 shadow-xl">
              <Shield size={40} className="text-white" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2 text-center">
              Welcome to CyberSecAgent
            </h2>
            <p className="text-gray-600 text-center max-w-md mb-8">
              Tell us about your security concern, and we'll connect you with
              the right expert.
            </p>

            {/* Quick Start Suggestions */}
            <div className="flex flex-wrap justify-center gap-3 max-w-lg">
              {[
                'My phone might be hacked',
                'I received a suspicious email',
                'My computer is acting strange',
                'I need a security assessment',
              ].map((suggestion) => (
                <button
                  key={suggestion}
                  onClick={() => sendMessage(suggestion)}
                  disabled={isLoading}
                  className="px-4 py-2 bg-white border border-gray-200 rounded-full text-sm text-gray-700
                             hover:border-primary-400 hover:text-primary-600 transition-colors
                             disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Chat Messages and Expert List - all in one scrollable area */}
        {messages.length > 0 && (
          <div className="max-w-4xl mx-auto px-4 py-6">
            {messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))}

            {/* Expert List - inline with chat (only before handoff) */}
            {experts && experts.length > 0 && !isComplete && (
              <div className="my-4">
                <ExpertList
                  experts={experts}
                  onSelect={handleSelectExpert}
                  isLoading={isLoading}
                />
              </div>
            )}

            {/* Typing Indicator */}
            {isLoading && (
              <div className="flex gap-3 mb-4">
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center">
                  <Shield size={20} className="text-white" />
                </div>
                <div className="bg-gray-100 rounded-2xl rounded-tl-sm px-4 py-3">
                  <div className="flex gap-1">
                    <span className="w-2 h-2 bg-gray-400 rounded-full typing-dot" />
                    <span className="w-2 h-2 bg-gray-400 rounded-full typing-dot" />
                    <span className="w-2 h-2 bg-gray-400 rounded-full typing-dot" />
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        )}

        {/* Expert Connection Popup */}
        {showExpertPopup && selectedExpert && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl animate-fade-in">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-xl font-bold text-gray-900">
                  Contact {selectedExpert.name}
                </h3>
                <button
                  onClick={() => setShowExpertPopup(false)}
                  className="p-2 hover:bg-gray-100 rounded-full transition-colors"
                >
                  <X size={20} className="text-gray-500" />
                </button>
              </div>

              {/* External freelancers: reached only through their public profile */}
              {selectedExpert.is_external && selectedExpert.profile_url && (
                <>
                  <p className="text-gray-600 mb-6">
                    {selectedExpert.name} is an independent freelancer, not affiliated with this
                    project. Contact them directly through their profile:
                  </p>
                  <a
                    href={selectedExpert.profile_url}
                    target="_blank"
                    rel="noopener noreferrer nofollow"
                    className="w-full flex items-center gap-3 p-4 bg-amber-50 hover:bg-amber-100 rounded-xl transition-colors border border-amber-200"
                  >
                    <div className="w-10 h-10 bg-amber-500 rounded-full flex items-center justify-center">
                      <ExternalLink size={20} className="text-white" />
                    </div>
                    <div className="text-left">
                      <p className="font-semibold text-amber-800">
                        View profile on {selectedExpert.profile_platform || 'their platform'}
                      </p>
                      <p className="text-sm text-amber-700">Opens in a new tab</p>
                    </div>
                  </a>
                </>
              )}

              {/* Network experts with real contact details */}
              {showContactLinks && (
                <>
                  <p className="text-gray-600 mb-6">
                    Choose how you'd like to reach {selectedExpert.name}:
                  </p>
                  <div className="space-y-3">
                    {whatsappDigits && (
                      <a
                        href={`https://wa.me/${whatsappDigits}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="w-full flex items-center gap-3 p-4 bg-green-50 hover:bg-green-100 rounded-xl transition-colors border border-green-200"
                      >
                        <div className="w-10 h-10 bg-green-500 rounded-full flex items-center justify-center">
                          <MessageSquare size={20} className="text-white" />
                        </div>
                        <div className="text-left">
                          <p className="font-semibold text-green-700">WhatsApp</p>
                          <p className="text-sm text-green-600">Start chatting now</p>
                        </div>
                      </a>
                    )}

                    <a
                      href={`mailto:${selectedExpert.email}`}
                      className="w-full flex items-center gap-3 p-4 bg-blue-50 hover:bg-blue-100 rounded-xl transition-colors border border-blue-200"
                    >
                      <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center">
                        <Mail size={20} className="text-white" />
                      </div>
                      <div className="text-left">
                        <p className="font-semibold text-blue-700">Email</p>
                        <p className="text-sm text-blue-600">{selectedExpert.email}</p>
                      </div>
                    </a>

                    {selectedExpert.linkedin && (
                      <a
                        href={selectedExpert.linkedin}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="w-full flex items-center gap-3 p-4 bg-sky-50 hover:bg-sky-100 rounded-xl transition-colors border border-sky-200"
                      >
                        <div className="w-10 h-10 bg-sky-600 rounded-full flex items-center justify-center">
                          <Linkedin size={20} className="text-white" />
                        </div>
                        <div className="text-left">
                          <p className="font-semibold text-sky-800">LinkedIn</p>
                          <p className="text-sm text-sky-700">View their profile</p>
                        </div>
                      </a>
                    )}

                    {selectedExpert.website && (
                      <a
                        href={selectedExpert.website}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="w-full flex items-center gap-3 p-4 bg-purple-50 hover:bg-purple-100 rounded-xl transition-colors border border-purple-200"
                      >
                        <div className="w-10 h-10 bg-purple-500 rounded-full flex items-center justify-center">
                          <Globe size={20} className="text-white" />
                        </div>
                        <div className="text-left">
                          <p className="font-semibold text-purple-700">Website</p>
                          <p className="text-sm text-purple-600">Visit their page</p>
                        </div>
                      </a>
                    )}
                  </div>
                </>
              )}

              {/* Sample network experts: placeholder details, nothing to link to */}
              {!selectedExpert.is_external && !showContactLinks && (
                <div className="p-4 bg-gray-50 border border-gray-200 rounded-xl">
                  <p className="font-semibold text-gray-800 mb-1">Sample expert profile</p>
                  <p className="text-sm text-gray-600">
                    {selectedExpert.name} is demo data used to show how matching works, so there
                    are no real contact details. Choose one of the external freelancers to reach
                    a real person through their public profile.
                  </p>
                </div>
              )}

              <button
                onClick={() => setShowExpertPopup(false)}
                className="w-full mt-4 py-3 text-gray-600 hover:text-gray-800 transition-colors"
              >
                Continue chatting instead
              </button>
            </div>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="max-w-4xl mx-auto px-4 py-4">
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
              <p className="font-medium">Error</p>
              <p className="text-sm">{error}</p>
            </div>
          </div>
        )}
      </main>

      {/* Chat Input - always enabled for continued conversation */}
      <ChatInput
        onSend={sendMessage}
        isLoading={isLoading}
        disabled={false}
        placeholder={
          messages.length === 0
            ? 'Describe your security concern...'
            : isComplete
            ? 'Need anything else? Keep chatting...'
            : 'Type your message...'
        }
      />
    </div>
  );
}
