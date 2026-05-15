import { parseSseEvents } from './sse';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001';

async function requestJson(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options);
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed: ${response.status}`);
  }
  return response.json();
}

export const api = {
  listConversations() {
    return requestJson('/api/conversations');
  },

  createConversation() {
    return requestJson('/api/conversations', { method: 'POST' });
  },

  getConversation(conversationId) {
    return requestJson(`/api/conversations/${encodeURIComponent(conversationId)}`);
  },

  async deleteConversation(conversationId) {
    const response = await fetch(
      `${API_BASE}/api/conversations/${encodeURIComponent(conversationId)}`,
      { method: 'DELETE' },
    );
    if (!response.ok) {
      throw new Error(`Delete failed: ${response.status}`);
    }
  },

  sendMessage(conversationId, content) {
    return requestJson(`/api/conversations/${encodeURIComponent(conversationId)}/message`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content }),
    });
  },

  async sendMessageStream(conversationId, content, onEvent) {
    const response = await fetch(
      `${API_BASE}/api/conversations/${encodeURIComponent(conversationId)}/message/stream`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content }),
      },
    );

    if (!response.ok || !response.body) {
      throw new Error(`Stream failed: ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const parsed = parseSseEvents(buffer);
      buffer = parsed.remaining;
      parsed.events.forEach((event) => onEvent(event.type, event));
    }
  },
};
