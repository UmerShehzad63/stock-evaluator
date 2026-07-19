import React from 'react';

function InsiderBanner({ ticker, insider }) {
  if (!insider) return null;
  const { buys = 0, sells = 0, booster = 0 } = insider;

  let emoji, title, borderColor;
  if (buys > 10) {
    emoji = '▲'; title = `MASSIVE INSIDER CLUSTER BUYING (+${booster.toFixed(1)} pts)`; borderColor = '#f2ca50';
  } else if (buys > 0) {
    emoji = '▲'; title = `INSIDER BUYING DETECTED (+${booster.toFixed(1)} pts)`; borderColor = '#d4af37';
  } else {
    emoji = '—'; title = 'CORPORATE INSIDER ACTIVITY (+0 pts)'; borderColor = '#a89060';
  }

  return (
    <div className="insider-banner" style={{ borderLeftColor: borderColor }}>
      <div>
        <div className="insider-title" style={{ color: borderColor }}>{emoji} {title}</div>
        <div className="insider-counts">
          <span className="insider-period">12-Month Transactions · </span>
          <span style={{ color: '#f2ca50', fontWeight: 700 }}>{buys} Buys</span>
          <span style={{ color: '#c6c6c6' }}> · </span>
          <span style={{ color: '#ffb4ab', fontWeight: 700 }}>{sells} Sells</span>
        </div>
        <div className="insider-note">Insiders only buy when they expect the price to rise.</div>
        <div className="insider-links">
          <a href={`http://openinsider.com/search?q=${ticker}`} target="_blank" rel="noopener noreferrer">
            OpenInsider Log ↗
          </a>
          <span> · </span>
          <a href={`https://finance.yahoo.com/quote/${ticker}/insider-transactions`} target="_blank" rel="noopener noreferrer">
            Yahoo Finance ↗
          </a>
        </div>
      </div>
    </div>
  );
}

export default InsiderBanner;
