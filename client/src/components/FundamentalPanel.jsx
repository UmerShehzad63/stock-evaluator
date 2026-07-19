import React, { useState } from 'react';

const fmtPct = (v) => (v != null ? `${(v * 100).toFixed(1)}%` : 'N/A');
const fmtNum = (v) => (v != null ? v.toFixed(2) : 'N/A');
const fmtDE = (v) => (v != null ? (v / 100).toFixed(2) : 'N/A');

const pillarColors = {
  Profitability: '#f2ca50',
  Growth: '#bfcdff',
  Valuation: '#d4af37',
  Health: '#bfcdff',
  'FCF Quality': '#e9c349',
};

function FundamentalPanel({ ticker, score, meta }) {
  const [showFScore, setShowFScore] = useState(false);
  if (!meta) return null;

  const s = Math.round(score || 0);
  const pillarScores = meta.pillar_scores || {};
  const pSigs = meta.piotroski_signals || {};
  const pRaw = meta.piotroski_raw || 0;
  const pMax = meta.piotroski_max || 0;
  const distTag = meta.is_distressed ? ' — DISTRESSED ASSET' : '';
  const fBadge = pMax > 0 ? ` · F-Score ${pRaw}/${pMax}` : '';
  const peMed = meta.sector_pe_median;

  return (
    <div className="glass-card">
      <div className="panel-header">
        <h2 className="panel-title">
          FUNDAMENTALS
          <span className="panel-sub"> · {s}{fBadge}{distTag}</span>
        </h2>
      </div>

      <div className="progress-container">
        <div className="progress-bar" style={{ width: `${s}%` }} />
      </div>

      {/* 5-pillar mini breakdown */}
      {Object.keys(pillarScores).length > 0 && (
        <div className="pillar-breakdown">
          <div className="pillar-breakdown-title">Factor Breakdown</div>
          {Object.entries(pillarScores).map(([name, val]) => {
            if (val == null) return null;
            const color = pillarColors[name] || '#c6c6c6';
            return (
              <div key={name} className="pillar-row">
                <span className="pillar-name">{name}</span>
                <div className="pillar-bar-bg">
                  <div className="pillar-bar-fill" style={{ width: `${Math.max(2, val)}%`, background: color }} />
                </div>
                <span className="pillar-val" style={{ color }}>{val}</span>
              </div>
            );
          })}
        </div>
      )}

      <div className="metric-grid">
        <div className="metric-item">
          <div className="metric-label">{peMed ? `P/E Ratio (vs ~${peMed}x sector)` : 'P/E Ratio'}</div>
          <div className="metric-value">{fmtNum(meta.PE)}</div>
        </div>
        <div className="metric-item">
          <div className="metric-label">P/B Ratio</div>
          <div className="metric-value">{fmtNum(meta.PB)}</div>
        </div>
        <div className="metric-item">
          <div className="metric-label">Return on Equity</div>
          <div className="metric-value">{fmtPct(meta.ROE)}</div>
        </div>
        <div className="metric-item">
          <div className="metric-label">Net Margin</div>
          <div className="metric-value">{fmtPct(meta.Margins)}</div>
        </div>
        <div className="metric-item">
          <div className="metric-label">Revenue Growth</div>
          <div className="metric-value">{fmtPct(meta.RevGrowth)}</div>
        </div>
        <div className="metric-item">
          <div className="metric-label">Debt-to-Equity</div>
          <div className="metric-value">{fmtDE(meta.DebtEq)}</div>
        </div>
      </div>

      {/* Piotroski F-Score */}
      {Object.keys(pSigs).length > 0 && (
        <div className="fscore-section">
          <button className="expander-btn" onClick={() => setShowFScore(!showFScore)}>
            {showFScore ? '▾' : '▸'} Piotroski F-Score Signals
          </button>
          {showFScore && (
            <div className="fscore-pills">
              {Object.entries(pSigs).map(([lbl, val]) => (
                <span key={lbl} className={`signal-pill ${val === 1 ? 'fsig-pass' : 'fsig-fail'}`}>
                  {val === 1 ? '✓' : '✗'} {lbl}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      <div className="ext-link">
        <a href={`https://finance.yahoo.com/quote/${ticker}/financials`} target="_blank" rel="noopener noreferrer">
          View Financial Statements ↗
        </a>
      </div>
    </div>
  );
}

export default FundamentalPanel;
