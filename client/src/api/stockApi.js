const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function evaluateStock(ticker) {
  const res = await fetch(`${API_BASE}/api/evaluate/${encodeURIComponent(ticker)}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function searchTicker(query) {
  const res = await fetch(`${API_BASE}/api/search?q=${encodeURIComponent(query)}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function getBacktestSectors() {
  const res = await fetch(`${API_BASE}/api/backtest/sectors`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function runBacktest(params) {
  const query = new URLSearchParams(params).toString();
  const res = await fetch(`${API_BASE}/api/backtest?${query}`);
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || `API error: ${res.status}`);
  }
  return res.json();
}

