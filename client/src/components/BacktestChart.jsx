import React, { useEffect, useRef } from 'react';
import { createChart } from 'lightweight-charts';

function BacktestChart({ data }) {
  const chartContainerRef = useRef(null);
  const chartRef = useRef(null);

  // Extract strategy keys dynamically from first data item
  const firstItem = data?.[0] || {};
  const strategyKeys = Object.keys(firstItem)
    .filter(key => key.startsWith('strategy_'))
    .sort((a, b) => {
      // Sort horizons numerically
      const numA = parseInt(a.replace('strategy_', '').replace('_days', ''));
      const numB = parseInt(b.replace('strategy_', '').replace('_days', ''));
      return numA - numB;
    });

  // Premium color palette for dynamic strategy curves
  const colorsPalette = ['#f2ca50', '#58a6ff', '#26a69a', '#ff8070', '#ab7fe6', '#f08080', '#e3a857', '#3fb950'];

  // Map strategy keys to labels and colors
  const strategyMeta = strategyKeys.map((key, index) => {
    const rawVal = key.replace('strategy_', '').replace('_days', '');
    const cleanLabel = rawVal === '21' ? '1-Month' :
                       rawVal === '63' ? '3-Month' :
                       rawVal === '126' ? '6-Month' :
                       rawVal === '252' ? '1-Year' : `${rawVal}-Days`;
    return {
      key,
      label: cleanLabel,
      color: colorsPalette[index % colorsPalette.length]
    };
  });

  useEffect(() => {
    if (!chartContainerRef.current || !data?.length) return;

    const container = chartContainerRef.current;

    const chart = createChart(container, {
      width: container.clientWidth,
      height: 400,
      layout: {
        background: { color: '#111316' },
        textColor: '#c6c6c6',
        fontFamily: 'Inter, sans-serif',
        fontSize: 11,
      },
      grid: {
        vertLines: { color: 'rgba(255,255,255,0.04)' },
        horzLines: { color: 'rgba(255,255,255,0.04)' },
      },
      rightPriceScale: { 
        borderColor: 'rgba(255,255,255,0.08)',
        alignLabels: true
      },
      timeScale: {
        borderColor: 'rgba(255,255,255,0.08)',
        timeVisible: true,
      },
    });

    chartRef.current = chart;

    // Add strategy lines dynamically
    strategyMeta.forEach(({ key, label, color }) => {
      const series = chart.addLineSeries({
        color: color,
        lineWidth: 2,
        title: label,
        priceLineVisible: false,
      });
      series.setData(
        data.map((d) => ({ time: d.time, value: d[key] }))
      );
    });

    // Benchmark Line (Silver)
    const benchmarkSeries = chart.addLineSeries({
      color: '#8b949e',
      lineWidth: 1.5,
      title: 'SPY Benchmark',
      priceLineVisible: false,
    });
    benchmarkSeries.setData(
      data.map((d) => ({ time: d.time, value: d.benchmark }))
    );

    chart.timeScale().fitContent();

    const handleResize = () => {
      if (container) {
        chart.applyOptions({ width: container.clientWidth });
      }
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
      chartRef.current = null;
    };
  }, [data, strategyKeys.join(',')]);

  return (
    <div className="chart-wrapper backtest-chart-card">
      <div className="chart-header">
        <h3>EQUITY CURVE COMPARISON</h3>
      </div>
      <div className="chart-legend" style={{ marginBottom: '15px', flexWrap: 'wrap', gap: '15px' }}>
        {strategyMeta.map(({ key, label, color }) => (
          <div key={key} className="leg">
            <div className="dot" style={{ background: color }} />
            {label} Hold
          </div>
        ))}
        <div className="leg">
          <div className="dot" style={{ background: '#8b949e' }} />
          SPY Benchmark
        </div>
      </div>
      <div ref={chartContainerRef} className="chart-container" />
    </div>
  );
}

export default BacktestChart;
