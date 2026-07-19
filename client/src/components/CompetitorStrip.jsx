import React from 'react';

function CompetitorStrip({ competitors, onSelect }) {
  if (!competitors || competitors.length === 0) return null;

  return (
    <div className="competitor-strip">
      <span className="competitor-strip-label">Peers</span>
      {competitors.map((comp, idx) => (
        <div
          key={idx}
          className="competitor-chip"
          onClick={() => onSelect(comp.ticker)}
          title={comp.name || ''}
        >
          <strong>{comp.ticker}</strong>&nbsp;
          <span>{comp.name || ''}</span>
        </div>
      ))}
    </div>
  );
}

export default CompetitorStrip;
