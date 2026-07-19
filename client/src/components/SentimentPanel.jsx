import React, { useState } from 'react';

function SentimentPanel({ score, meta }) {
  const [showRawValues, setShowRawValues] = useState(false);
  if (!meta) return null;

  const s = Math.round(score || 0);
  const spreadShort = meta["spread_short"] || 0;
  const spreadMedium = meta["spread_medium"] || 0;
  const spreadLong = meta["spread_long"] || 0;
  const combinedSpread = meta["combined_spread"] || 0;
  
  const priceToday = meta["price_today"] || 0;
  const ema5 = meta["ema5"] || 0;
  const ema20 = meta["ema20"] || 0;
  const ema12 = meta["ema12"] || 0;
  const ema50 = meta["ema50"] || 0;
  const ema200 = meta["ema200"] || 0;
  const source = meta["sentiment_source"] || 'Multi-Scale Trend Velocity';

  const isPositive = combinedSpread >= 0;

  let statusStr = "Neutral / Consolidated Trend";
  if (combinedSpread > 2.0) {
    statusStr = "Strong Bullish Acceleration";
  } else if (combinedSpread > 0.0) {
    statusStr = "Mild Bullish Velocity";
  } else if (combinedSpread < -2.0) {
    statusStr = "Strong Bearish Deceleration";
  } else if (combinedSpread < 0.0) {
    statusStr = "Mild Bearish Velocity";
  }

  const formatPct = (val) => {
    const isPos = val >= 0;
    return (
      <span style={{ color: isPos ? '#26a69a' : '#ff8070', fontWeight: '700' }}>
        {isPos ? '+' : ''}{val.toFixed(2)}%
      </span>
    );
  };

  return (
    <div className="glass-card">
      <div className="panel-header">
        <h2 className="panel-title">
          PRICE MOMENTUM
          <span className="panel-sub"> · {s}</span>
        </h2>
      </div>

      <div className="progress-container">
        <div className="progress-bar" style={{ width: `${s}%` }} />
      </div>

      <p className="sentiment-summary" style={{ fontStyle: 'normal', color: 'var(--text-primary)', fontWeight: '600', marginBottom: '15px' }}>
        Status: <span style={{ color: isPositive ? '#26a69a' : '#ff8070' }}>{statusStr}</span> (Combined Spread: {formatPct(combinedSpread)})
      </p>

      <div className="metric-grid">
        <div className="metric-item">
          <div className="metric-label">Short-Term (5/20)</div>
          <div className="metric-value">{formatPct(spreadShort)}</div>
        </div>
        <div className="metric-item">
          <div className="metric-label">Medium-Term (12/50)</div>
          <div className="metric-value">{formatPct(spreadMedium)}</div>
        </div>
        <div className="metric-item">
          <div className="metric-label">Long-Term (20/200)</div>
          <div className="metric-value">{formatPct(spreadLong)}</div>
        </div>
        <div className="metric-item">
          <div className="metric-label">Current Price</div>
          <div className="metric-value">${priceToday.toFixed(2)}</div>
        </div>
      </div>

      <div className="fscore-section" style={{ borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: '10px', marginTop: '12px' }}>
        <button className="expander-btn" onClick={() => setShowRawValues(!showRawValues)}>
          {showRawValues ? '▾' : '▸'} View Raw EMA Metrics & Spreads
        </button>

        {showRawValues && (
          <div style={{ marginTop: '10px', padding: '10px', background: 'rgba(0,0,0,0.2)', borderRadius: '4px', fontSize: '0.8rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
              <span>5 EMA vs 20 EMA:</span>
              <span style={{ fontFamily: 'monospace' }}>${ema5.toFixed(2)} / ${ema20.toFixed(2)}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
              <span>12 EMA vs 50 EMA:</span>
              <span style={{ fontFamily: 'monospace' }}>${ema12.toFixed(2)} / ${ema50.toFixed(2)}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
              <span>20 EMA vs 200 EMA:</span>
              <span style={{ fontFamily: 'monospace' }}>${ema20.toFixed(2)} / ${ema200.toFixed(2)}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', color: 'var(--text-secondary)', fontSize: '0.75rem', marginTop: '6px' }}>
              <span>Weightings:</span>
              <span>40% Short | 30% Medium | 30% Long</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default SentimentPanel;
