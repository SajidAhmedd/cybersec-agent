'use client';

import { useState, useCallback } from 'react';
import { chatApi, ApiError } from './api';
import {
  Message,
  ChatSession,
  ConversationPhase,
  ExpertRecommendation,
} from '@/types';

function generateId(): string {
  return Math.random().toString(36).substring(2, 15);
}

export function useChat() {
  const [session, setSession] = useState<ChatSession>({
    sessionId: null,
    messages: [],
    phase: 'start',
    isComplete: false,
    experts: null,
  });

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const addMessage = useCallback((role: 'user' | 'assistant', content: string) => {
    const message: Message = {
      id: generateId(),
      role,
      content,
      timestamp: new Date(),
    };
    setSession((prev) => ({
      ...prev,
      messages: [...prev.messages, message],
    }));
    return message;
  }, []);

  const sendMessage = useCallback(
    async (content: string) => {
      if (!content.trim() || isLoading) return;

      setError(null);
      setIsLoading(true);

      // Add user message immediately
      addMessage('user', content);

      try {
        let response;

        if (!session.sessionId) {
          // Start new session
          response = await chatApi.startChat(content);
          setSession((prev) => ({
            ...prev,
            sessionId: response.session_id,
            phase: response.phase,
          }));
        } else {
          try {
            // Continue existing session
            response = await chatApi.continueChat(session.sessionId, content);
            setSession((prev) => ({
              ...prev,
              phase: response.phase,
              isComplete: response.is_complete,
              // Only keep experts if we're still in presenting phase
              // Clear them after handoff/completion to avoid showing again
              experts: response.is_complete ? null : (response.experts || prev.experts),
            }));
          } catch (continueErr) {
            // If session not found, start a new one
            if (continueErr instanceof ApiError && continueErr.message.includes('Session not found')) {
              console.log('Session expired, starting new session...');
              response = await chatApi.startChat(content);
              setSession((prev) => ({
                ...prev,
                sessionId: response.session_id,
                phase: response.phase,
              }));
            } else {
              throw continueErr;
            }
          }
        }

        // Add assistant response
        addMessage('assistant', response.response);
      } catch (err) {
        const errorMessage =
          err instanceof ApiError
            ? err.message
            : 'Failed to send message. Please try again.';
        setError(errorMessage);
        console.error('Chat error:', err);
      } finally {
        setIsLoading(false);
      }
    },
    [session.sessionId, isLoading, addMessage]
  );

  const selectExpert = useCallback(
    async (expertId: number) => {
      if (!session.sessionId || isLoading) return;

      setError(null);
      setIsLoading(true);

      try {
        const response = await chatApi.selectExpert(session.sessionId, expertId);

        // Find expert name for user message
        const expert = session.experts?.find((e) => e.expert.id === expertId);
        const expertName = expert?.expert.name || `Expert #${expertId}`;

        addMessage('user', `I'd like to connect with ${expertName}`);
        addMessage('assistant', response.response);

        setSession((prev) => ({
          ...prev,
          phase: response.phase,
          isComplete: response.is_complete,
          experts: null, // Clear experts after selection
        }));
      } catch (err) {
        const errorMessage =
          err instanceof ApiError
            ? err.message
            : 'Failed to select expert. Please try again.';
        setError(errorMessage);
        console.error('Select expert error:', err);
      } finally {
        setIsLoading(false);
      }
    },
    [session.sessionId, session.experts, isLoading, addMessage]
  );

  const resetChat = useCallback(() => {
    if (session.sessionId) {
      chatApi.endSession(session.sessionId).catch(console.error);
    }
    setSession({
      sessionId: null,
      messages: [],
      phase: 'start',
      isComplete: false,
      experts: null,
    });
    setError(null);
  }, [session.sessionId]);

  return {
    messages: session.messages,
    phase: session.phase,
    isComplete: session.isComplete,
    experts: session.experts,
    isLoading,
    error,
    sendMessage,
    selectExpert,
    resetChat,
  };
}
