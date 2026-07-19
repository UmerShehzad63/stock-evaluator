import React from 'react';

function ScoreGauge({ score, rating, price }) {
  const ratingText = rating?.text || 'Neutral / Mixed';
  const ratingColor = rating?.color || '#a89060';

  return (
    <div className="score-cards-row">
      <div className="glass-card score-card" style={{ borderTopColor: ratingColor }}>
        <h3>Composite Score</h3>
        <div className="value" style={{ color: ratingColor }}>
          {score != null ? score.toFixed(1) : '--'}
          <span className="score-suffix">/100</span>
        </div>
      </div>

      <div className="glass-card score-card" style={{ borderTopColor: ratingColor }}>
        <h3>Signal Strength</h3>
        <div className="value signal-text" style={{ color: ratingColor }}>
          {ratingText}
        </div>
      </div>

      <div className="glass-card score-card">
        <h3>Current Price</h3>
        <div className="value">
          {price != null ? `$${parseFloat(price).toFixed(2)}` : '--'}
        </div>
      </div>
    </div>
  );
}

export default ScoreGauge;
