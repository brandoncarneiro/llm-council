import { useMemo, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import './Stage2.css';

function modelSlug(model) {
  return model?.split('/').at(-1) || model || 'model';
}

function modelRoleMap(labelToModel, labelToRole) {
  const output = {};
  Object.entries(labelToModel || {}).forEach(([label, model]) => {
    if (labelToRole?.[label]) output[model] = labelToRole[label];
  });
  return output;
}

function replaceLabels(text, labelToRole) {
  return Object.entries(labelToRole || {}).reduce((current, [label, role]) => (
    current.replaceAll(label, `**${role}**`)
  ), text || '');
}

export default function Stage2({
  aggregateRankings,
  labelToModel,
  labelToRole,
  rankings,
}) {
  const [selected, setSelected] = useState(0);
  const rolesByModel = useMemo(
    () => modelRoleMap(labelToModel, labelToRole),
    [labelToModel, labelToRole],
  );

  if (!rankings?.length) return null;

  const active = rankings[Math.min(selected, rankings.length - 1)];

  return (
    <section className="stage-card">
      <div className="stage-card__header">
        <p className="eyebrow">Stage 2</p>
        <h3>Anonymous peer rankings</h3>
      </div>

      {aggregateRankings?.length > 0 && (
        <ol className="ranking-summary" aria-label="Aggregate ranking">
          {aggregateRankings.map((item) => (
            <li key={item.model}>
              <span>{rolesByModel[item.model] || modelSlug(item.model)}</span>
              <small>{item.average_rank.toFixed(2)} avg from {item.rankings_count}</small>
            </li>
          ))}
        </ol>
      )}

      <div className="tab-list" role="tablist" aria-label="Peer reviews">
        {rankings.map((ranking, index) => (
          <button
            type="button"
            role="tab"
            aria-selected={index === selected}
            className={index === selected ? 'is-active' : ''}
            key={ranking.model}
            onClick={() => setSelected(index)}
          >
            {rolesByModel[ranking.model] || modelSlug(ranking.model)}
          </button>
        ))}
      </div>

      <div className="stage-card__body">
        <p className="model-chip">{active.model}</p>
        <div className="markdown-content">
          <ReactMarkdown>{replaceLabels(active.ranking, labelToRole)}</ReactMarkdown>
        </div>
      </div>
    </section>
  );
}
