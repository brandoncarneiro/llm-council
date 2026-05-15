import './Sidebar.css';

function formatCount(count) {
  return count === 1 ? '1 message' : `${count} messages`;
}

export default function Sidebar({
  conversations,
  currentConversationId,
  onDeleteConversation,
  onNewConversation,
  onSelectConversation,
}) {
  return (
    <aside className="sidebar" aria-label="Conversations">
      <div className="sidebar__header">
        <div>
          <p className="eyebrow">Local workspace</p>
          <h1>LLM Council</h1>
        </div>
        <button type="button" className="sidebar__new" onClick={onNewConversation}>
          New
        </button>
      </div>

      <nav className="session-list">
        {conversations.length === 0 ? (
          <p className="session-list__empty">No saved sessions.</p>
        ) : (
          conversations.map((conversation) => {
            const active = conversation.id === currentConversationId;
            return (
              <div className="session-row" key={conversation.id}>
                <button
                  type="button"
                  className={`session-row__main ${active ? 'is-active' : ''}`}
                  onClick={() => onSelectConversation(conversation.id)}
                >
                  <span>{conversation.title || 'New Conversation'}</span>
                  <small>{formatCount(conversation.message_count || 0)}</small>
                </button>
                <button
                  type="button"
                  className="session-row__delete"
                  aria-label={`Delete ${conversation.title || 'conversation'}`}
                  onClick={() => onDeleteConversation(conversation.id)}
                >
                  Delete
                </button>
              </div>
            );
          })
        )}
      </nav>
    </aside>
  );
}
