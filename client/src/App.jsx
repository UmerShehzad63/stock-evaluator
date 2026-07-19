import React, { useState, useCallback } from 'react';
import { evaluateStock } from './api/stockApi';
import SearchBar from './components/SearchBar';
import LandingPage from './components/LandingPage';
import LoadingScreen from './components/LoadingScreen';
import ScoreGauge from './components/ScoreGauge';
import InsiderBanner from './components/InsiderBanner';
import CompetitorStrip from './components/CompetitorStrip';
import FundamentalPanel from './components/FundamentalPanel';
import SentimentPanel from './components/SentimentPanel';
import TechnicalPanel from './components/TechnicalPanel';
import DerivativePanel from './components/DerivativePanel';
import CandlestickChart from './components/CandlestickChart';
import BacktestDashboard from './components/BacktestDashboard';


function App() {
  const [activeTab, setActiveTab] = useState('evaluator');
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [currentTicker, setCurrentTicker] = useState('');

  const handleSearch = useCallback(async (ticker) => {
    if (!ticker.trim()) return;
    setLoading(true);
    setError(null);
    setCurrentTicker(ticker.toUpperCase());

    try {
      const result = await evaluateStock(ticker);
      setData(result);
    } catch (err) {
      console.error(err);
      setError(`Failed to evaluate ${ticker.toUpperCase()}. Make sure the backend server is running on port 8000.`);
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  const chartData = data?.chart_data;
  const lastPrice = chartData?.candles?.length
    ? chartData.candles[chartData.candles.length - 1].close
    : null;

  return (
    <div className="app-container">
      <header className="app-header">
        <h1 className="main-title">QUANTITATIVE STOCK EVALUATION</h1>
        <p className="sub-title">Refining market noise into institutional-grade clarity.</p>

        <div className="nav-tabs" style={{ display: 'flex', justifyContent: 'center', gap: '20px', marginTop: '20px', marginBottom: '10px' }}>
          <button 
            className={`nav-tab ${activeTab === 'evaluator' ? 'active' : ''}`}
            onClick={() => setActiveTab('evaluator')}
            style={{
              background: 'none',
              border: 'none',
              color: activeTab === 'evaluator' ? 'var(--gold-primary)' : 'var(--text-secondary)',
              borderBottom: activeTab === 'evaluator' ? '2px solid var(--gold-primary)' : '2px solid transparent',
              paddingBottom: '5px',
              fontFamily: 'Manrope, sans-serif',
              fontWeight: '700',
              fontSize: '1rem',
              cursor: 'pointer',
              textTransform: 'uppercase',
              letterSpacing: '0.08em',
              transition: 'all 0.2s'
            }}
          >
            Single Stock Evaluator
          </button>
          <button 
            className={`nav-tab ${activeTab === 'backtest' ? 'active' : ''}`}
            onClick={() => setActiveTab('backtest')}
            style={{
              background: 'none',
              border: 'none',
              color: activeTab === 'backtest' ? 'var(--gold-primary)' : 'var(--text-secondary)',
              borderBottom: activeTab === 'backtest' ? '2px solid var(--gold-primary)' : '2px solid transparent',
              paddingBottom: '5px',
              fontFamily: 'Manrope, sans-serif',
              fontWeight: '700',
              fontSize: '1rem',
              cursor: 'pointer',
              textTransform: 'uppercase',
              letterSpacing: '0.08em',
              transition: 'all 0.2s'
            }}
          >
            Quantitative Backtester
          </button>
        </div>
      </header>

      {activeTab === 'backtest' ? (
        <BacktestDashboard />
      ) : (
        <>
          <SearchBar onSearch={handleSearch} />

          {error && (
            <div className="glass-card error-banner">
              ❌ {error}
            </div>
          )}

          {!loading && !data && !error && <LandingPage />}

          {loading && <LoadingScreen ticker={currentTicker} />}

          {!loading && data && (
            <div className="dashboard fade-in">
              <div className="dashboard-header">
                <h1>{data.ticker} <span className="company-name">{data.company_name}</span></h1>
                {(data.sector || data.industry) && (
                  <p className="sector-industry">
                    {data.sector}{data.industry ? ` · ${data.industry}` : ''}
                  </p>
                )}
              </div>

              <CompetitorStrip competitors={data.competitors || []} onSelect={handleSearch} />

              <ScoreGauge
                score={data.composite_score}
                rating={data.rating}
                price={lastPrice}
              />

              <InsiderBanner
                ticker={data.ticker}
                insider={data.insider}
              />

              <div className="signal-breakdown-label">Signal Breakdown</div>

              <div className="dashboard-grid">
                <div className="panels-column">
                  <FundamentalPanel
                    ticker={data.ticker}
                    score={data.scores?.fundamental?.score}
                    meta={data.scores?.fundamental?.meta}
                  />
                  <SentimentPanel
                    score={data.scores?.sentiment?.score}
                    meta={data.scores?.sentiment?.meta}
                  />
                  <TechnicalPanel
                    score={data.scores?.technical?.score}
                    meta={data.scores?.technical?.meta}
                  />
                  <DerivativePanel
                    ticker={data.ticker}
                    score={data.scores?.derivative?.score}
                    meta={data.scores?.derivative?.meta}
                    techTrend={data.scores?.technical?.meta?.Trend}
                  />
                </div>

                <div className="chart-column">
                  <CandlestickChart
                    chartData={chartData}
                    ticker={data.ticker}
                  />
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default App;
