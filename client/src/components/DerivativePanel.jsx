import React from 'react';

const fmtNum = (v) => (v != null ? v.toFixed(2) : 'N/A');
const fmtPct = (v) => (v != null ? `${v.toFixed(1)}%` : 'N/A');

function DerivativePanel({ ticker, score, meta, techTrend }) {
  if (!meta) return null;

  const s = Math.round(score || 0);
  const pcrVol = meta.pcr_vol;
  const pcrOi = meta.pcr_oi;
  const shortFloat = meta.short_float;
  const shortRatio = meta.short_ratio;
  const iv = meta.avg_iv;

  const squeeze = shortRatio && shortFloat && shortRatio > 8 && shortFloat > 10 && techTrend;
  const ivStr = iv && iv > 50 ? 'High Volatility Expected' : (iv != null ? 'Normal Volatility' : 'N/A');

  return (
    <div className="glass-card">
      <div className="panel-header">
        <h2 className="panel-title">
          DERIVATIVES & OPTIONS
          <span className="panel-sub"> · {s}</span>
        </h2>
      </div>

      <div className="progress-container">
        <div className="progress-bar" style={{ width: `${s}%` }} />
      </div>

      <div className="metric-grid">
        <div className="metric-item">
          <div className="metric-label">Volume P/C Ratio</div>
          <div className="metric-value">{fmtNum(pcrVol)}</div>
        </div>
        <div className="metric-item">
          <div className="metric-label">Open Interest P/C Ratio</div>
          <div className="metric-value">{fmtNum(pcrOi)}</div>
        </div>
        <div className="metric-item">
          <div className="metric-label">Short Float</div>
          <div className="metric-value">{fmtPct(shortFloat)}</div>
        </div>
        <div className="metric-item">
          <div className="metric-label">Days to Cover</div>
          <div className="metric-value">
            {fmtNum(shortRatio)}
            {squeeze && <span className="squeeze-tag"> ▲ Squeeze Watch</span>}
          </div>
        </div>
        <div className="metric-item">
          <div className="metric-label">Implied Volatility (IV)</div>
          <div className="metric-value">{fmtPct(iv)}</div>
        </div>
        <div className="metric-item">
          <div className="metric-label">Market Expectation</div>
          <div className="metric-value">{ivStr}</div>
        </div>
      </div>

      <div className="ext-link">
        <a href={`https://finance.yahoo.com/quote/${ticker}/options`} target="_blank" rel="noopener noreferrer">
          View Options Chain ↗
        </a>
      </div>
    </div>
  );
}

export default DerivativePanel;
