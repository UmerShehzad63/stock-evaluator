import React, { useState, useEffect } from 'react';
import { getBacktestSectors, runBacktest } from '../api/stockApi';
import BacktestChart from './BacktestChart';

function BacktestDashboard() {
  const [sectors, setSectors] = useState(['All']);
  const [selectedSector, setSelectedSector] = useState('All');
  const [startDate, setStartDate] = useState('2023-01-01');
  const [endDate, setEndDate] = useState('2024-06-01');
  const [capital, setCapital] = useState(100000);
  const [portfolioSize, setPortfolioSize] = useState(3);
  
  // Custom horizons selections
  const [comparisonCount, setComparisonCount] = useState(4);
  const [slots, setSlots] = useState(['21', '63', '126', '252']); // Defaults: 1m, 3m, 6m, 1y

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [results, setResults] = useState(null);
  
  // Selected horizon for the ticker details table
  const [selectedDetailsHorizon, setSelectedDetailsHorizon] = useState('');

  useEffect(() => {
    async function loadSectors() {
      try {
        const data = await getBacktestSectors();
        if (data?.sectors) {
          setSectors(data.sectors);
        }
      } catch (err) {
        console.error('Failed to load sectors', err);
      }
    }
    loadSectors();
  }, []);

  const handleRun = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResults(null);

    // Send only the active slots based on comparison count
    const activeHorizons = slots.slice(0, comparisonCount).join(',');

    try {
      const data = await runBacktest({
        sector: selectedSector,
        start_date: startDate,
        end_date: endDate,
        capital: capital,
        portfolio_size: portfolioSize,
        horizons: activeHorizons,
      });
      setResults(data);
      
      const horizonKeys = Object.keys(data.horizons);
      if (horizonKeys.length > 0) {
        setSelectedDetailsHorizon(horizonKeys[0]);
      }
    } catch (err) {
      console.error(err);
      setError(err.message || 'Failed to run backtest simulation.');
    } finally {
      setLoading(false);
    }
  };

  const getHorizonLabel = (hKey) => {
    const days = hKey.replace('_days', '');
    if (days === '21') return '1-Month Horizon';
    if (days === '42') return '2-Month Horizon';
    if (days === '63') return '3-Month Horizon';
    if (days === '84') return '4-Month Horizon';
    if (days === '105') return '5-Month Horizon';
    if (days === '126') return '6-Month Horizon';
    if (days === '189') return '9-Month Horizon';
    if (days === '252') return '1-Year Horizon';
    if (days === '378') return '18-Month Horizon';
    if (days === '504') return '2-Year Horizon';
    return `${days}-Days Horizon`;
  };

  const getHorizonBadgeColor = (hName, index) => {
    const colorsPalette = ['#f2ca50', '#58a6ff', '#26a69a', '#ff8070', '#ab7fe6', '#f08080', '#e3a857', '#3fb950'];
    return colorsPalette[index % colorsPalette.length];
  };

  return (
    <div className="backtest-dashboard fade-in">
      <div className="dashboard-header" style={{ marginBottom: '2rem' }}>
        <h2>Quantitative Backtesting Suite</h2>
        <p className="sub-title" style={{ marginTop: '5px' }}>
          Compare performance, risk indices, and signal decay across dynamic rebalancing horizons.
        </p>
      </div>

      {/* Configuration Form */}
      <div className="glass-card" style={{ marginBottom: '2rem', padding: '1.5rem' }}>
        <form onSubmit={handleRun}>
          
          <h3 style={{ fontSize: '14px', letterSpacing: '0.1em', color: 'var(--gold-primary)', marginBottom: '1.2rem', textTransform: 'uppercase' }}>
            Core Simulation Parameters
          </h3>
          <div className="backtest-form-grid" style={{ marginBottom: '1.8rem' }}>
            <div className="form-group">
              <label>Asset Sector Pool</label>
              <select
                value={selectedSector}
                onChange={(e) => setSelectedSector(e.target.value)}
                className="search-input"
                style={{ width: '100%' }}
              >
                {sectors.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label>Portfolio Size (Top-K)</label>
              <input
                type="number"
                min="1"
                max="10"
                value={portfolioSize}
                onChange={(e) => setPortfolioSize(Number(e.target.value))}
                className="search-input"
                style={{ width: '100%' }}
                required
              />
            </div>

            <div className="form-group">
              <label>Start Date</label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="search-input"
                style={{ width: '100%' }}
                required
              />
            </div>

            <div className="form-group">
              <label>End Date</label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="search-input"
                style={{ width: '100%' }}
                required
              />
            </div>

            <div className="form-group">
              <label>Initial Capital ($)</label>
              <input
                type="number"
                value={capital}
                onChange={(e) => setCapital(Number(e.target.value))}
                className="search-input"
                style={{ width: '100%' }}
                required
              />
            </div>
          </div>

          <h3 style={{ fontSize: '14px', letterSpacing: '0.1em', color: 'var(--gold-primary)', marginBottom: '1.2rem', textTransform: 'uppercase', borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: '1.5rem' }}>
            Horizon Rebalance Comparison
          </h3>
          
          <div className="backtest-form-grid" style={{ marginBottom: '1.5rem' }}>
            <div className="form-group">
              <label>Number of Comparisons</label>
              <select
                value={comparisonCount}
                onChange={(e) => setComparisonCount(Number(e.target.value))}
                className="search-input"
                style={{ width: '100%' }}
              >
                <option value={1}>1 Horizon</option>
                <option value={2}>2 Horizons</option>
                <option value={3}>3 Horizons</option>
                <option value={4}>4 Horizons</option>
              </select>
            </div>

            {[...Array(comparisonCount)].map((_, i) => (
              <div key={i} className="form-group">
                <label>Comparison Slot {i + 1}</label>
                <select
                  value={slots[i]}
                  onChange={(e) => {
                    const newSlots = [...slots];
                    newSlots[i] = e.target.value;
                    setSlots(newSlots);
                  }}
                  className="search-input"
                  style={{ width: '100%' }}
                >
                  <option value="21">1 Month (21 days)</option>
                  <option value="42">2 Months (42 days)</option>
                  <option value="63">3 Months (63 days)</option>
                  <option value="84">4 Months (84 days)</option>
                  <option value="105">5 Months (105 days)</option>
                  <option value="126">6 Months (126 days)</option>
                  <option value="189">9 Months (189 days)</option>
                  <option value="252">12 Months / 1 Year (252 days)</option>
                  <option value="378">18 Months (378 days)</option>
                  <option value="504">24 Months / 2 Years (504 days)</option>
                </select>
              </div>
            ))}
          </div>

          <div style={{ display: 'flex', justifyContent: 'center', marginTop: '2rem' }}>
            <button type="submit" className="search-button" disabled={loading} style={{ minWidth: '220px' }}>
              {loading ? 'SIMULATING...' : 'RUN HISTORICAL BACKTEST'}
            </button>
          </div>
        </form>
      </div>

      {error && (
        <div className="glass-card error-banner" style={{ margin: '2rem 0' }}>
          <h4>Simulation Execution Blocked</h4>
          <p style={{ marginTop: '8px', fontSize: '0.9rem' }}>{error}</p>
        </div>
      )}

      {loading && (
        <div className="glass-card text-center" style={{ padding: '3rem', textAlign: 'center' }}>
          <div className="spinner" style={{ margin: '0 auto 1.5rem auto' }} />
          <h3 style={{ color: 'var(--gold-primary)' }}>Executing Horizon Simulations</h3>
          <p className="text-secondary" style={{ marginTop: '8px' }}>
            Running dynamic parallel portfolio rebalancing simulations...
          </p>
        </div>
      )}

      {!loading && results && (
        <div className="backtest-results-grid fade-in">
          
          {/* Comparative Summary Cards (Dynamic Horizons) */}
          <div className="score-cards-row" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))' }}>
            {Object.entries(results.horizons).map(([hName, data], index) => {
              const returnVal = data.summary.cumulative_return;
              const alphaVal = data.summary.alpha;
              const isPositive = returnVal >= 0;
              const isAlphaPositive = alphaVal >= 0;
              
              return (
                <div key={hName} className="glass-card score-card" style={{ borderTop: `3px solid ${getHorizonBadgeColor(hName, index)}` }}>
                  <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '8px' }}>
                    <span className="dot" style={{ background: getHorizonBadgeColor(hName, index), width: '8px', height: '8px', borderRadius: '50%' }} />
                    <h3 style={{ fontSize: '11px', letterSpacing: '0.15em' }}>{getHorizonLabel(hName)}</h3>
                  </div>
                  
                  <div className="value" style={{ color: isPositive ? '#26a69a' : '#ef5350', fontSize: '2rem' }}>
                    {returnVal}%
                  </div>
                  
                  <div className="metric-grid" style={{ gridTemplateColumns: 'repeat(2, 1fr)', marginTop: '12px', borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: '10px' }}>
                    <div style={{ textAlign: 'left' }}>
                      <div className="metric-label" style={{ fontSize: '8px' }}>Sharpe Ratio</div>
                      <div className="metric-value" style={{ fontSize: '0.95rem', margin: '2px 0 0 0' }}>{data.summary.sharpe_ratio}</div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <div className="metric-label" style={{ fontSize: '8px' }}>Max Drawdown</div>
                      <div className="metric-value" style={{ fontSize: '0.95rem', margin: '2px 0 0 0', color: '#ef5350' }}>{data.summary.max_drawdown}%</div>
                    </div>
                  </div>
                  
                  <div className="metric-grid" style={{ gridTemplateColumns: 'repeat(2, 1fr)', marginTop: '4px' }}>
                    <div style={{ textAlign: 'left' }}>
                      <div className="metric-label" style={{ fontSize: '8px' }}>Excess Alpha</div>
                      <div className="metric-value" style={{ fontSize: '0.95rem', margin: '2px 0 0 0', color: isAlphaPositive ? '#f2ca50' : '#ef5350' }}>
                        {isAlphaPositive ? '+' : ''}{alphaVal}%
                      </div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <div className="metric-label" style={{ fontSize: '8px' }}>Sortino / SPY DD</div>
                      <div className="metric-value" style={{ fontSize: '0.85rem', margin: '2px 0 0 0', color: 'var(--text-secondary)' }}>
                        {data.summary.sortino_ratio} / {data.summary.benchmark_max_drawdown}%
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Grid Layout: Chart and Table */}
          <div className="dashboard-grid">
            {/* Chart Column */}
            <div className="chart-column" style={{ position: 'static', width: '100%' }}>
              {results.chart_data && <BacktestChart data={results.chart_data} />}

              {/* Information Hit Precision */}
              {results.horizons[selectedDetailsHorizon]?.hit_precision && (
                <div className="glass-card" style={{ marginTop: '2rem' }}>
                  <div className="panel-header" style={{ marginBottom: '1rem' }}>
                    <h3 className="panel-title">INFORMATION HIT PRECISION ANALYSIS</h3>
                  </div>
                  <p className="text-secondary" style={{ fontSize: '0.85rem', marginBottom: '1.5rem' }}>
                    Measures the percentage frequency of assets registering a <b>Score &ge; 80</b> outperforming the SPY benchmark over subsequent trading intervals.
                  </p>
                  
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', textAlign: 'center' }}>
                    <div className="pillar-breakdown" style={{ margin: '0' }}>
                      <div className="pillar-breakdown-title">T+10 Days</div>
                      <div className="value" style={{ fontSize: '1.5rem', fontWeight: '800', color: 'var(--gold-primary)' }}>
                        {results.horizons[selectedDetailsHorizon].hit_precision.t10}%
                      </div>
                    </div>
                    <div className="pillar-breakdown" style={{ margin: '0' }}>
                      <div className="pillar-breakdown-title">T+30 Days</div>
                      <div className="value" style={{ fontSize: '1.5rem', fontWeight: '800', color: 'var(--gold-primary)' }}>
                        {results.horizons[selectedDetailsHorizon].hit_precision.t30}%
                      </div>
                    </div>
                    <div className="pillar-breakdown" style={{ margin: '0' }}>
                      <div className="pillar-breakdown-title">T+60 Days</div>
                      <div className="value" style={{ fontSize: '1.5rem', fontWeight: '800', color: 'var(--gold-primary)' }}>
                        {results.horizons[selectedDetailsHorizon].hit_precision.t60}%
                      </div>
                    </div>
                  </div>
                  <div className="text-center" style={{ marginTop: '15px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    Sample Size: {results.horizons[selectedDetailsHorizon].hit_precision.sample_size} signals observed
                  </div>
                </div>
              )}
            </div>

            {/* Assets Table Column */}
            <div className="panels-column">
              <div className="glass-card">
                <div className="panel-header" style={{ marginBottom: '1.5rem', flexWrap: 'wrap', gap: '10px' }}>
                  <h3 className="panel-title">Asset Allocation & Contribution</h3>
                  
                  {/* Select horizon to view detailed table */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-secondary)' }}>View:</span>
                    <select
                      value={selectedDetailsHorizon}
                      onChange={(e) => setSelectedDetailsHorizon(e.target.value)}
                      className="search-input"
                      style={{ padding: '4px 8px', fontSize: '12px', background: '#111316' }}
                    >
                      {Object.keys(results.horizons).map((key) => (
                        <option key={key} value={key}>
                          {getHorizonLabel(key)}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="table-responsive" style={{ maxHeight: '550px', overflowY: 'auto' }}>
                  <table className="backtest-table" style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                    <thead>
                      <tr style={{ borderBottom: '1px solid var(--border-subtle)', fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-secondary)' }}>
                        <th style={{ padding: '10px' }}>Ticker</th>
                        <th style={{ padding: '10px' }}>Return Contribution</th>
                        <th style={{ padding: '10px' }}>Trades</th>
                        <th style={{ padding: '10px' }}>Days Held</th>
                        <th style={{ padding: '10px' }}>Avg Hold (Days)</th>
                      </tr>
                    </thead>
                    <tbody>
                      {results.horizons[selectedDetailsHorizon] && 
                        Object.entries(results.horizons[selectedDetailsHorizon].ticker_details).map(([ticker, details]) => {
                          const horizonIndex = Object.keys(results.horizons).indexOf(selectedDetailsHorizon);
                          return (
                            <tr key={ticker} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)', fontSize: '0.85rem' }}>
                              <td style={{ padding: '10px', fontWeight: '700', color: getHorizonBadgeColor(selectedDetailsHorizon, horizonIndex) }}>{ticker}</td>
                              <td style={{ padding: '10px', color: details.cumulative_return >= 0 ? '#26a69a' : '#ef5350', fontWeight: '600' }}>
                                {details.cumulative_return >= 0 ? '+' : ''}{details.cumulative_return}%
                              </td>
                              <td style={{ padding: '10px' }}>{details.trade_count}</td>
                              <td style={{ padding: '10px' }}>{details.days_held}</td>
                              <td style={{ padding: '10px' }}>
                                {details.trade_count > 0 ? Math.round(details.days_held / details.trade_count) : 0}
                              </td>
                            </tr>
                          );
                        })
                      }
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default BacktestDashboard;
