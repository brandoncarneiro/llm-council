import ReactMarkdown from 'react-markdown';
import './Stage3.css';

export default function Stage3({ finalResponse }) {
  if (!finalResponse) return null;

  return (
    <section className="synthesis-card">
      <div className="synthesis-card__header">
        <p className="eyebrow">Stage 3</p>
        <h3>Council synthesis</h3>
        <span>{finalResponse.model}</span>
      </div>
      <div className="markdown-content">
        <ReactMarkdown>{finalResponse.response}</ReactMarkdown>
      </div>
    </section>
  );
}
