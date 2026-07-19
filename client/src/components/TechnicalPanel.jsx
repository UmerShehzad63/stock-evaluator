import React from 'react';

function TechnicalPanel({ score, meta }) {
  if (!meta) return null;

  const s = Math.round(score || 0);
  const price = meta.Price || 0;
  const ema20 = meta.EMA20 || 0;
  const sma50 = meta.SMA50 || 0;
  const sma200 = meta.SMA200 || 0;
  const rsi = meta.RSI;
  const macdLine = meta.MACD || 0;
  const macdSignal = meta.MACD_Signal || 0;
  const bbHi = meta.BB_High || 0;
  const bbLo = meta.BB_Low || 0;
  const isUptrend = meta.Trend;

  // Derive display values (same logic as original Streamlit UI)
  const macdStatus = macdLine > macdSignal ? 'Bullish Cross' : 'Bearish Cross';

  let trendStr;
  if (price > ema20 && ema20 > sma50 && sma50 > sma200) trendStr = 'Strong Uptrend';
  else if (price > sma50 && sma50 > sma200) trendStr = 'Uptrend';
  else if (price < sma50 && price > sma200) trendStr = 'Weakening / Pullback';
  else if (price < sma200) trendStr = 'Downtrend';
  else trendStr = 'Mixed/Consolidating';

  let bbStr;
  if (price > bbHi) bbStr = isUptrend ? 'Upper Band (Breakout)' : 'Overbought';
  else if (price < bbLo) bbStr = isUptrend ? 'Lower Band (Support)' : 'Oversold';
  else bbStr = 'Mid-Channel';

  const signals = meta.signal_details || [];

  return (
    <div className="glass-card">
      <div className="panel-header">
        <h2 className="panel-title">
          TECHNICAL ANALYSIS
          <span className="panel-sub"> · {s}</span>
        </h2>
      </div>

      <div className="progress-container">
        <div className="progress-bar" style={{ width: `${s}%` }} />
      </div>

      <div className="metric-grid">
        <div className="metric-item">
          <div className="metric-label">RSI (14)</div>
          <div className="metric-value">{rsi != null ? rsi.toFixed(1) : '--'}</div>
        </div>
        <div className="metric-item">
          <div className="metric-label">MACD</div>
          <div className="metric-value">{macdStatus}</div>
        </div>
        <div className="metric-item">
          <div className="metric-label">Trend (vs 200 SMA)</div>
          <div className="metric-value">{trendStr}</div>
        </div>
        <div className="metric-item">
          <div className="metric-label">Volatility (BB)</div>
          <div className="metric-value">{bbStr}</div>
        </div>
      </div>

      {signals.length > 0 && (
        <div className="tech-signals">
          {signals.map(([label, val], idx) => (
            <span key={idx} className={`signal-pill ${val === 1 ? 'fsig-pass' : 'fsig-fail'}`}>
              {val === 1 ? '✓' : '✗'} {label}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

export default TechnicalPanel;
