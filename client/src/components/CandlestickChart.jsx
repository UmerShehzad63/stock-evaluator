import React, { useEffect, useRef } from 'react';
import { createChart, CrosshairMode, LineStyle } from 'lightweight-charts';

function CandlestickChart({ chartData, ticker }) {
  const chartContainerRef = useRef(null);
  const chartRef = useRef(null);

  useEffect(() => {
    if (!chartContainerRef.current || !chartData?.candles?.length) return;

    const container = chartContainerRef.current;

    const chart = createChart(container, {
      width: container.clientWidth,
      height: 500,
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
      crosshair: { mode: CrosshairMode.Normal },
      rightPriceScale: { borderColor: 'rgba(255,255,255,0.08)' },
      timeScale: {
        borderColor: 'rgba(255,255,255,0.08)',
        timeVisible: true,
        secondsVisible: false,
      },
      handleScroll: { mouseWheel: true, pressedMouseMove: true, horzTouchDrag: true },
      handleScale: { mouseWheel: true, pinch: true, axisPressedMouseMove: true },
    });

    chartRef.current = chart;

    // Candlestick series
    const candleSeries = chart.addCandlestickSeries({
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderUpColor: '#26a69a',
      borderDownColor: '#ef5350',
      wickUpColor: '#26a69a',
      wickDownColor: '#ef5350',
    });
    candleSeries.setData(chartData.candles);

    // BB upper
    if (chartData.bb_high?.length) {
      const bbHi = chart.addLineSeries({
        color: 'rgba(242,202,80,0.25)',
        lineWidth: 1,
        priceLineVisible: false,
        lastValueVisible: false,
      });
      bbHi.setData(chartData.bb_high);
    }

    // BB lower
    if (chartData.bb_low?.length) {
      const bbLo = chart.addLineSeries({
        color: 'rgba(242,202,80,0.25)',
        lineWidth: 1,
        priceLineVisible: false,
        lastValueVisible: false,
      });
      bbLo.setData(chartData.bb_low);
    }

    // SMA 50
    if (chartData.sma50?.length) {
      const sma50 = chart.addLineSeries({
        color: '#bfcdff',
        lineWidth: 1.5,
        priceLineVisible: false,
        lastValueVisible: false,
      });
      sma50.setData(chartData.sma50);
    }

    // SMA 200
    if (chartData.sma200?.length) {
      const sma200 = chart.addLineSeries({
        color: '#ffb4ab',
        lineWidth: 1.5,
        lineStyle: LineStyle.Dashed,
        priceLineVisible: false,
        lastValueVisible: false,
      });
      sma200.setData(chartData.sma200);
    }

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
  }, [chartData]);

  return (
    <div className="chart-wrapper">
      <div className="chart-header">
        <h3>PRICE ACTION & INDICATORS</h3>
      </div>
      <div className="chart-legend">
        <div className="leg"><div className="dot" style={{ background: '#26a69a' }} />Price</div>
        <div className="leg"><div className="dot" style={{ background: '#bfcdff' }} />SMA 50</div>
        <div className="leg"><div className="dot" style={{ background: '#ffb4ab' }} />SMA 200</div>
        <div className="leg"><div className="dot" style={{ background: 'rgba(242,202,80,0.4)' }} />BB Band</div>
      </div>
      <div ref={chartContainerRef} className="chart-container" />
      {ticker && (
        <div className="chart-tv-link">
          <a href={`https://www.tradingview.com/chart/?symbol=${ticker}`} target="_blank" rel="noopener noreferrer">
            View on TradingView ↗
          </a>
        </div>
      )}
    </div>
  );
}

export default CandlestickChart;
