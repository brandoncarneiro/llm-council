import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import './Stage1.css';

function displayModel(model) {
  return model?.split('/').at(-1) || model || 'model';
}

export default function Stage1({ responses }) {
  const [selected, setSelected] = useState(0);
  if (!responses?.length) return null;

  const active = responses[Math.min(selected, responses.length - 1)];

  return (
    <section className="stage-card">
      <div className="stage-card__header">
        <p className="eyebrow">Stage 1</p>
        <h3>Independent advisor responses</h3>
      </div>
      <div className="tab-list" role="tablist" aria-label="Advisor responses">
        {responses.map((response, index) => (
          <button
            type="button"
            role="tab"
            aria-selected={index === selected}
            className={index === selected ? 'is-active' : ''}
            key={`${response.role}-${response.model}`}
            onClick={() => setSelected(index)}
          >
            {response.role || displayModel(response.model)}
          </button>
        ))}
      </div>
      <div className="stage-card__body">
        <p className="model-chip">{active.model}</p>
        <div className="markdown-content">
          <ReactMarkdown>{active.response}</ReactMarkdown>
        </div>
      </div>
    </section>
  );
}
