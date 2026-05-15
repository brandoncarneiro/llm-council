import { useEffect, useRef, useState } from 'react';
import Stage1 from './Stage1';
import Stage2 from './Stage2';
import Stage3 from './Stage3';
import './ChatInterface.css';

const LOADING_LABELS = {
  stage1: 'Collecting advisor answers',
  stage2: 'Running anonymous peer review',
  stage3: 'Writing final synthesis',
};

function LoadingRow({ label }) {
  return (
    <div className="loading-row" role="status">
      <span className="loading-row__dot" />
      <span>{label}</span>
    </div>
  );
}

function AssistantMessage({ message }) {
  const loading = message.loading || {};

  return (
    <section className="assistant-output" aria-label="Council output">
      {loading.stage1 && <LoadingRow label={LOADING_LABELS.stage1} />}
      {message.stage3 && <Stage3 finalResponse={message.stage3} />}
      {message.stage1 && <Stage1 responses={message.stage1} />}
      {loading.stage2 && <LoadingRow label={LOADING_LABELS.stage2} />}
      {message.stage2 && (
        <Stage2
          aggregateRankings={message.metadata?.aggregate_rankings}
          labelToModel={message.metadata?.label_to_model}
          labelToRole={message.metadata?.label_to_role}
          rankings={message.stage2}
        />
      )}
      {loading.stage3 && <LoadingRow label={LOADING_LABELS.stage3} />}
    </section>
  );
}

function EmptyState({ hasConversation }) {
  return (
    <div className="empty-state">
      <p className="eyebrow">{hasConversation ? 'Ready' : 'New session'}</p>
      <h2>{hasConversation ? 'Ask one decision-quality question.' : 'Start with one decision-quality question.'}</h2>
      <p>
        The council is built for questions where disagreement, ranking, and
        synthesis are more useful than a single agreeable answer.
      </p>
    </div>
  );
}

export default function ChatInterface({
  conversation,
  error,
  isLoading,
  onSendMessage,
}) {
  const [draft, setDraft] = useState('');
  const scrollAnchor = useRef(null);

  useEffect(() => {
    scrollAnchor.current?.scrollIntoView({ block: 'end', behavior: 'smooth' });
  }, [conversation?.messages?.length]);

  const disabled = isLoading;
  const canSubmit = draft.trim().length > 0 && !disabled;

  const submit = (event) => {
    event.preventDefault();
    if (!canSubmit) return;
    onSendMessage(draft.trim());
    setDraft('');
  };

  return (
    <section className="chat">
      <header className="chat__header">
        <p className="eyebrow">Founder/operator decision council</p>
        <h2>{conversation?.title || 'LLM Council'}</h2>
      </header>

      <div className="chat__messages">
        {error && <div className="error-banner">{error}</div>}

        {!conversation || conversation.messages.length === 0 ? (
          <EmptyState hasConversation={Boolean(conversation)} />
        ) : (
          conversation.messages.map((message, index) => (
            <article className="message" key={`${message.role}-${index}`}>
              {message.role === 'user' ? (
                <>
                  <p className="message__label">You</p>
                  <p className="message__body">{message.content}</p>
                </>
              ) : (
                <AssistantMessage message={message} />
              )}
            </article>
          ))
        )}
        <div ref={scrollAnchor} />
      </div>

      <form className="composer" onSubmit={submit}>
        <label className="sr-only" htmlFor="council-question">
          Question
        </label>
        <textarea
          id="council-question"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter' && !event.shiftKey) {
              submit(event);
            }
          }}
          disabled={disabled}
          placeholder="Ask a consequential question..."
          rows={3}
        />
        <button type="submit" disabled={!canSubmit}>
          Send
        </button>
      </form>
    </section>
  );
}
