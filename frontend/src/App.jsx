import { useCallback, useEffect, useState } from 'react';
import { api } from './api';
import ChatInterface from './components/ChatInterface';
import Sidebar from './components/Sidebar';
import './App.css';

const EMPTY_LOADING = { stage1: false, stage2: false, stage3: false };

function withLastAssistant(conversation, updater) {
  if (!conversation?.messages?.length) return conversation;
  const lastIndex = conversation.messages.length - 1;
  return {
    ...conversation,
    messages: conversation.messages.map((message, index) => (
      index === lastIndex ? updater(message) : message
    )),
  };
}

export default function App() {
  const [sessions, setSessions] = useState([]);
  const [activeId, setActiveId] = useState(null);
  const [conversation, setConversation] = useState(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');

  const refreshSessions = useCallback(async () => {
    const nextSessions = await api.listConversations();
    setSessions(nextSessions);
  }, []);

  const openConversation = useCallback(async (id) => {
    const nextConversation = await api.getConversation(id);
    setConversation(nextConversation);
  }, []);

  useEffect(() => {
    refreshSessions().catch((err) => setError(err.message));
  }, [refreshSessions]);

  useEffect(() => {
    if (!activeId) return;
    openConversation(activeId).catch((err) => setError(err.message));
  }, [activeId, openConversation]);

  const patchAssistant = useCallback((updater) => {
    setConversation((current) => withLastAssistant(current, updater));
  }, []);

  const startConversation = useCallback(async () => {
    setError('');
    const created = await api.createConversation();
    setSessions((current) => [
      { ...created, message_count: 0 },
      ...current,
    ]);
    setActiveId(created.id);
    setConversation(created);
    return created;
  }, []);

  const createSession = async () => {
    await startConversation();
  };

  const deleteSession = async (id) => {
    setError('');
    await api.deleteConversation(id);
    setSessions((current) => current.filter((session) => session.id !== id));
    if (id === activeId) {
      setActiveId(null);
      setConversation(null);
    }
  };

  const sendMessage = async (content) => {
    if (pending) return;
    setError('');
    setPending(true);

    let targetConversation = conversation;
    let targetId = activeId;

    try {
      if (!targetId || !targetConversation) {
        targetConversation = await startConversation();
        targetId = targetConversation.id;
      }

      const optimisticMessages = [
        { role: 'user', content },
        {
          role: 'assistant',
          stage1: null,
          stage2: null,
          stage3: null,
          metadata: null,
          loading: EMPTY_LOADING,
        },
      ];

      setConversation({
        ...targetConversation,
        messages: [
          ...(targetConversation.messages || []),
          ...optimisticMessages,
        ],
      });

      await api.sendMessageStream(targetId, content, (eventType, event) => {
        if (eventType === 'stage1_start') {
          patchAssistant((message) => ({
            ...message,
            loading: { ...message.loading, stage1: true },
          }));
        }

        if (eventType === 'stage1_complete') {
          patchAssistant((message) => ({
            ...message,
            stage1: event.data,
            loading: { ...message.loading, stage1: false },
          }));
        }

        if (eventType === 'stage2_start') {
          patchAssistant((message) => ({
            ...message,
            loading: { ...message.loading, stage2: true },
          }));
        }

        if (eventType === 'stage2_complete') {
          patchAssistant((message) => ({
            ...message,
            stage2: event.data,
            metadata: event.metadata,
            loading: { ...message.loading, stage2: false },
          }));
        }

        if (eventType === 'stage3_start') {
          patchAssistant((message) => ({
            ...message,
            loading: { ...message.loading, stage3: true },
          }));
        }

        if (eventType === 'stage3_complete') {
          patchAssistant((message) => ({
            ...message,
            stage3: event.data,
            loading: { ...message.loading, stage3: false },
          }));
        }

        if (eventType === 'title_complete' || eventType === 'complete') {
          refreshSessions().catch((err) => setError(err.message));
        }

        if (eventType === 'error') {
          setError(event.message || 'Council run failed.');
        }
      });
    } catch (err) {
      setError(err.message);
      setConversation((current) => (
        current
          ? { ...current, messages: current.messages.slice(0, -2) }
          : null
      ));
    } finally {
      setPending(false);
    }
  };

  return (
    <main className="app-shell">
      <Sidebar
        conversations={sessions}
        currentConversationId={activeId}
        onDeleteConversation={deleteSession}
        onNewConversation={createSession}
        onSelectConversation={setActiveId}
      />
      <ChatInterface
        conversation={conversation}
        error={error}
        isLoading={pending}
        onSendMessage={sendMessage}
      />
    </main>
  );
}
