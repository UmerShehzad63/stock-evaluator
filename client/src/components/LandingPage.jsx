import React from 'react';

function LandingPage() {
  return (
    <div className="landing-page">
      <div className="feature-grid">
        <div className="feature-card">
          <div className="feature-icon">📊</div>
          <div className="feature-title">Fundamental Analysis</div>
          <div className="feature-desc">Deep dive into financial health with Piotroski F-Score, P/E ratios, ROE, and debt-to-equity metrics.</div>
        </div>
        <div className="feature-card">
          <div className="feature-icon">📈</div>
          <div className="feature-title">Technical Indicators</div>
          <div className="feature-desc">RSI, MACD, Bollinger Bands, and trend analysis across multiple timeframes with SMA overlays.</div>
        </div>
        <div className="feature-card">
          <div className="feature-icon">🚀</div>
          <div className="feature-title">Price Momentum</div>
          <div className="feature-desc">20-day historical trend velocity and volatility-adjusted direction analysis.</div>
        </div>
        <div className="feature-card">
          <div className="feature-icon">⚡</div>
          <div className="feature-title">Options & Derivatives</div>
          <div className="feature-desc">Put/Call ratios, implied volatility, short interest, and squeeze indicators for complete market context.</div>
        </div>
      </div>

      <div className="stats-row">
        <div className="stat-item">
          <div className="stat-number">4</div>
          <div className="stat-label">Analysis Pillars</div>
        </div>
        <div className="stat-item">
          <div className="stat-number">Real-Time</div>
          <div className="stat-label">Data Updates</div>
        </div>
        <div className="stat-item">
          <div className="stat-number">20-Day</div>
          <div className="stat-label">Trend Momentum</div>
        </div>
      </div>

      <div className="how-it-works">
        <div className="section-title">How It Works</div>
        <div className="step-row">
          <div className="step-number">1</div>
          <div className="step-text"><strong>Enter a Stock</strong>Type any ticker symbol or company name in the search bar above.</div>
        </div>
        <div className="step-row">
          <div className="step-number">2</div>
          <div className="step-text"><strong>Multi-Pillar Analysis</strong>Our system aggregates real-time data across fundamentals, technicals, momentum, and derivatives.</div>
        </div>
        <div className="step-row">
          <div className="step-number">3</div>
          <div className="step-text"><strong>Get Your Score</strong>Receive a composite rating with detailed breakdowns and actionable insights.</div>
        </div>
      </div>
    </div>
  );
}

export default LandingPage;
