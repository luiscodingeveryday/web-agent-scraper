export interface Message {
  id: string;
  role: 'user' | 'agent';
  content: string;
  timestamp: Date;
  isLoading?: boolean;
  error?: string;
}

export interface AgentResponse {
  final_answer: string | null;
  scratchpad: string;
  error: string | null;
  steps: number;
}

export interface ChatState {
  messages: Message[];
  isLoading: boolean;
  error: string | null;
}