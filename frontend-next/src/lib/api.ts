import {
  StartChatResponse,
  ContinueChatResponse,
  SelectExpertResponse,
  ChatRequest,
} from '@/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8003';

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorText = await response.text();
    throw new ApiError(response.status, errorText || 'An error occurred');
  }
  return response.json();
}

export const chatApi = {
  /**
   * Start a new chat session
   */
  async startChat(message: string): Promise<StartChatResponse> {
    const response = await fetch(`${API_URL}/chat/start`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ message } as ChatRequest),
    });
    return handleResponse<StartChatResponse>(response);
  },

  /**
   * Continue an existing chat session
   */
  async continueChat(
    sessionId: string,
    message: string
  ): Promise<ContinueChatResponse> {
    const response = await fetch(`${API_URL}/chat/${sessionId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ message } as ChatRequest),
    });
    return handleResponse<ContinueChatResponse>(response);
  },

  /**
   * Select an expert from the matched results
   */
  async selectExpert(
    sessionId: string,
    expertId: number
  ): Promise<SelectExpertResponse> {
    const response = await fetch(
      `${API_URL}/chat/${sessionId}/select-expert?expert_id=${expertId}`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );
    return handleResponse<SelectExpertResponse>(response);
  },

  /**
   * Get session state (for debugging)
   */
  async getSessionState(sessionId: string): Promise<any> {
    const response = await fetch(`${API_URL}/chat/${sessionId}/state`);
    return handleResponse(response);
  },

  /**
   * End a chat session
   */
  async endSession(sessionId: string): Promise<void> {
    await fetch(`${API_URL}/chat/${sessionId}`, {
      method: 'DELETE',
    });
  },

  /**
   * Health check
   */
  async healthCheck(): Promise<{ status: string }> {
    const response = await fetch(`${API_URL}/health`);
    return handleResponse(response);
  },
};

export { ApiError };
