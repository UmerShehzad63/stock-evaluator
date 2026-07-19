import React from 'react';

function LoadingScreen({ ticker }) {
  return (
    <div className="loading-screen">
      <div className="spinner">🔄</div>
      <div className="loading-text">
        Fetching Real-Time Analysis for {ticker}...
      </div>
      <div className="loading-bar-bg">
        <div className="loading-bar-fill" />
      </div>
    </div>
  );
}

export default LoadingScreen;
