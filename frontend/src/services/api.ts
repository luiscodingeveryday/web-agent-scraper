import axios from 'axios';
import type { AgentResponse } from '../types';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  timeout: 120000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const sendMessage = async (userInput: string): Promise<AgentResponse> => {
  const response = await api.post<AgentResponse>('/api/agent/run', {
    user_input: userInput,
  });
  return response.data;
};

export const checkHealth = async (): Promise<{ status: string }> => {
  const response = await api.get('/api/health');
  return response.data;
};