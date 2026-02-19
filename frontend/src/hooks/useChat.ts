import { useState, useCallback, useRef, useEffect } from 'react';
import { sendMessage } from '../services/api';
import type { Message, ChatState } from '../types';

export const useChat = () => {
  const [state, setState] = useState<ChatState>({
    messages: [],
    isLoading: false,
    error: null,
  });

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to last message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [state.messages]);

  const addMessage = useCallback((message: Omit<Message, 'id' | 'timestamp'>) => {
    const newMessage: Message = {
      ...message,
      id: crypto.randomUUID(),
      timestamp: new Date(),
    };
    setState((prev) => ({
      ...prev,
      messages: [...prev.messages, newMessage],
    }));
    return newMessage.id;
  }, []);

  const updateMessage = useCallback((id: string, updates: Partial<Message>) => {
    setState((prev) => ({
      ...prev,
      messages: prev.messages.map((msg) =>
        msg.id === id ? { ...msg, ...updates } : msg
      ),
    }));
  }, []);

  const sendUserMessage = useCallback(async (content: string) => {
    if (!content.trim()) return;

    // Add user message
    addMessage({ role: 'user', content: content.trim() });

    // Add agent "Typing" message
    const agentMessageId = addMessage({
      role: 'agent',
      content: '',
      isLoading: true,
    });

    setState((prev) => ({ ...prev, isLoading: true, error: null }));

    try {
      const response = await sendMessage(content.trim());

      // Update agent message with response
      updateMessage(agentMessageId, {
        content: response.final_answer || response.error || 'No response',
        isLoading: false,
        error: response.error || undefined,
      });

      setState((prev) => ({ ...prev, isLoading: false }));
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';

      updateMessage(agentMessageId, {
        content: 'Failed to get response from agent',
        isLoading: false,
        error: errorMessage,
      });

      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: errorMessage,
      }));
    }
  }, [addMessage, updateMessage]);

  const clearError = useCallback(() => {
    setState((prev) => ({ ...prev, error: null }));
  }, []);

  return {
    messages: state.messages,
    isLoading: state.isLoading,
    error: state.error,
    sendMessage: sendUserMessage,
    clearError,
    messagesEndRef,
  };
};