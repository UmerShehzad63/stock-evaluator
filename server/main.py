import math
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from data_loader import DataLoader, convert_name_to_ticker
from scorers import ScoringEngine
from utils import get_rating

# Backtesting modules
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backtesting.engine import RuleBasedBacktester
from backtesting.data_manager import BacktestingDataManager, SECTORS, ALL_TICKERS, CACHE_FILE


app = FastAPI(title="AI Stock Evaluator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def clean_value(v):
    """Clean a single value for JSON serialization."""
    if v is None:
        return None
    if isinstance(v, pd.DataFrame):
        return None
    if isinstance(v, pd.Series):
        return None
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        if np.isnan(v) or np.isinf(v):
            return None
        return float(v)
    if isinstance(v, float):
        if math.isnan(v) or math.isinf(v):
            return None
        return v
    if isinstance(v, (np.bool_,)):
        return bool(v)
    try:
        if pd.isna(v):
            return None
    except (TypeError, ValueError):
        pass
    return v


def clean_dict(d):
    """Recursively clean a dict/list for JSON serialization."""
    if isinstance(d, dict):
        return {
            k: clean_dict(v)
            for k, v in d.items()
            if not (k.startswith("_") and isinstance(v, (pd.DataFrame, type(None))))
            and not isinstance(v, (pd.DataFrame, pd.Series))
        }
    elif isinstance(d, list):
        return [clean_dict(item) for item in d]
    elif isinstance(d, tuple):
        return [clean_dict(item) for item in d]
    else:
        return clean_value(d)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/search")
def search(q: str):
    ticker = convert_name_to_ticker(q)
    if not ticker:
        raise HTTPException(status_code=404, detail="Ticker not found")
    return {"ticker": ticker}


@app.get("/api/backtest/sectors")
def get_backtest_sectors():
    return {"sectors": ["All"] + list(SECTORS.keys())}


@app.get("/api/backtest")
def run_backtest(
    sector: str = "All",
    start_date: str = "2021-01-01",
    end_date: str = "2026-07-20",
    capital: float = 100000.0,
    portfolio_size: int = 3,
    horizons: str = "21,63,126,252"
):
    manager = BacktestingDataManager()
    
    # Check if cache exists
    if not os.path.exists(CACHE_FILE):
        if sector == "All":
            raise HTTPException(
                status_code=400,
                detail="Data cache file is missing. Please build the cache using the command: `python backtesting/run_cli.py --download-only` in your terminal."
            )
        else:
            # Download just the requested sector's tickers dynamically
            tickers_to_download = SECTORS.get(sector, []) + ["SPY"]
            print(f"Cache missing. Downloading sector {sector} tickers on-the-fly...")
            for ticker in tickers_to_download:
                res = manager.download_ticker_data(ticker, start_date=start_date, end_date=end_date)
                if res:
                    manager.data_cache[ticker] = res
            manager.save_cache()
    else:
        # Load existing cache
        manager.load_cache()

    # Determine tickers to backtest
    if sector != "All" and sector in SECTORS:
        tickers = SECTORS[sector]
    else:
        tickers = ALL_TICKERS

    # Verify we have data in cache for these tickers
    available_tickers = [t for t in tickers if manager.get_ticker_data(t) is not None]
    if not available_tickers:
        if sector != "All":
            tickers_to_download = SECTORS.get(sector, []) + ["SPY"]
            print(f"Tickers missing from cache. Downloading sector {sector} tickers on-the-fly...")
            for ticker in tickers_to_download:
                res = manager.download_ticker_data(ticker, start_date=start_date, end_date=end_date)
                if res:
                    manager.data_cache[ticker] = res
            manager.save_cache()
            available_tickers = [t for t in tickers if manager.get_ticker_data(t) is not None]
        
        if not available_tickers:
            raise HTTPException(
                status_code=400,
                detail="No cached data available for selected tickers. Please run data download command in terminal."
            )

    try:
        # Parse custom horizons
        try:
            horizons_list = [int(h.strip()) for h in horizons.split(",") if h.strip().isdigit()]
        except Exception:
            horizons_list = [21, 63, 126, 252]
        if not horizons_list:
            horizons_list = [21, 63, 126, 252]

        backtester = RuleBasedBacktester(
            tickers=available_tickers,
            start_date=start_date,
            end_date=end_date,
            initial_capital=capital,
            portfolio_size=portfolio_size
        )
        results = backtester.run_simulation(horizons_list=horizons_list)
        if not results:
            raise HTTPException(status_code=500, detail="Backtest simulation yielded empty results.")
        return clean_dict(results)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/evaluate/{ticker_input}")

def evaluate(ticker_input: str):
    ticker = convert_name_to_ticker(ticker_input)
    if not ticker:
        raise HTTPException(status_code=404, detail="Could not resolve ticker")

    loader = DataLoader()
    engine = ScoringEngine()

    # Fetch technical data first (needed for scoring)
    df_tech = loader.get_technical_data(ticker)
    if df_tech is None or df_tech.empty:
        raise HTTPException(status_code=404, detail=f"No market data found for {ticker}")

    # Calculate technical score (sets engine.current_tech_trend)
    score_tech, meta_tech = engine.calculate_technical(df_tech)

    # Fetch remaining data in parallel (excluding social sentiment)
    with ThreadPoolExecutor(max_workers=2) as executor:
        deriv_future = executor.submit(loader.get_derivative_data, ticker)
        fund_future = executor.submit(loader.get_fundamental_data, ticker)

        data_deriv = deriv_future.result()
        data_fund = fund_future.result()

    # Calculate Multi-Scale Trend Velocity (MSTV) Momentum Score
    close_series = df_tech['Close']
    
    # Calculate EMAs
    ema5 = close_series.ewm(span=5, adjust=False).mean()
    ema12 = close_series.ewm(span=12, adjust=False).mean()
    ema20 = close_series.ewm(span=20, adjust=False).mean()
    ema50 = close_series.ewm(span=50, adjust=False).mean()
    ema200 = close_series.ewm(span=min(200, len(close_series)), adjust=False).mean()
    
    # Latest values
    val_close = float(close_series.iloc[-1])
    val_ema5 = float(ema5.iloc[-1])
    val_ema12 = float(ema12.iloc[-1])
    val_ema20 = float(ema20.iloc[-1])
    val_ema50 = float(ema50.iloc[-1])
    val_ema200 = float(ema200.iloc[-1])
    
    # Spreads in %
    spread_short = ((val_ema5 - val_ema20) / val_ema20) * 100.0 if val_ema20 else 0.0
    spread_medium = ((val_ema12 - val_ema50) / val_ema50) * 100.0 if val_ema50 else 0.0
    spread_long = ((val_ema20 - val_ema200) / val_ema200) * 100.0 if val_ema200 else 0.0
    
    # Combined Spread (40% Short, 30% Medium, 30% Long)
    combined_spread = (0.40 * spread_short) + (0.30 * spread_medium) + (0.30 * spread_long)
    score_social = max(0.0, min(100.0, 50.0 + (combined_spread * 4.0)))
    
    meta_social = {
        "sentiment_source": "Multi-Scale Trend Velocity",
        "spread_short": round(spread_short, 2),
        "spread_medium": round(spread_medium, 2),
        "spread_long": round(spread_long, 2),
        "combined_spread": round(combined_spread, 2),
        "price_today": round(val_close, 2),
        "ema5": round(val_ema5, 2),
        "ema20": round(val_ema20, 2),
        "ema12": round(val_ema12, 2),
        "ema50": round(val_ema50, 2),
        "ema200": round(val_ema200, 2)
    }

    score_deriv, meta_deriv = engine.calculate_derivative(data_deriv)
    score_fund, meta_fund = engine.calculate_fundamental(data_fund)

    # Composite: Fundamentals 40% | Sentiment 25% | Technical 20% | Derivatives 15%
    base_composite = (
        score_fund * 0.40
        + score_social * 0.25
        + score_tech * 0.20
        + score_deriv * 0.15
    )

    insider_buys = meta_fund.get("insider_buys", 0)
    insider_sells = meta_fund.get("insider_sells", 0)
    insider_booster = meta_fund.get("insider_booster", 0)
    composite = min(100, base_composite + insider_booster)

    rating_text, rating_color = get_rating(composite)

    company_name = meta_fund.get("longName") or meta_fund.get("shortName") or ticker
    sector = meta_fund.get("sector", "")
    industry = meta_fund.get("industry", "")

    # Competitors
    competitors = loader.get_competitors(ticker, company_name, sector, industry)

    # Build chart data
    chart_data = {
        "candles": [],
        "sma50": [],
        "sma200": [],
        "bb_high": [],
        "bb_low": [],
    }

    if df_tech is not None and not df_tech.empty:
        from ta.trend import SMAIndicator
        from ta.volatility import BollingerBands

        close = df_tech["Close"]
        df_tech["sma_50"] = SMAIndicator(close, window=50).sma_indicator()
        df_tech["sma_200"] = SMAIndicator(
            close, window=min(200, len(df_tech))
        ).sma_indicator()
        bb = BollingerBands(close)
        df_tech["bb_high"] = bb.bollinger_hband()
        df_tech["bb_low"] = bb.bollinger_lband()

        for row in df_tech.itertuples():
            ts = int(row.Index.timestamp())
            o, h, l, c = float(row.Open), float(row.High), float(row.Low), float(row.Close)
            if not (math.isnan(o) or math.isnan(h) or math.isnan(l) or math.isnan(c)):
                chart_data["candles"].append(
                    {"time": ts, "open": round(o, 4), "high": round(h, 4), "low": round(l, 4), "close": round(c, 4)}
                )

            sma50_val = getattr(row, "sma_50", None)
            if sma50_val is not None and not (isinstance(sma50_val, float) and math.isnan(sma50_val)):
                chart_data["sma50"].append({"time": ts, "value": round(float(sma50_val), 4)})

            sma200_val = getattr(row, "sma_200", None)
            if sma200_val is not None and not (isinstance(sma200_val, float) and math.isnan(sma200_val)):
                chart_data["sma200"].append({"time": ts, "value": round(float(sma200_val), 4)})

            bb_h = getattr(row, "bb_high", None)
            if bb_h is not None and not (isinstance(bb_h, float) and math.isnan(bb_h)):
                chart_data["bb_high"].append({"time": ts, "value": round(float(bb_h), 4)})

            bb_l = getattr(row, "bb_low", None)
            if bb_l is not None and not (isinstance(bb_l, float) and math.isnan(bb_l)):
                chart_data["bb_low"].append({"time": ts, "value": round(float(bb_l), 4)})

    response = {
        "ticker": ticker,
        "company_name": company_name,
        "sector": sector,
        "industry": industry,
        "composite_score": float(composite),
        "rating": {"text": rating_text, "color": rating_color},
        "scores": {
            "technical": {"score": float(score_tech), "meta": meta_tech},
            "fundamental": {"score": float(score_fund), "meta": meta_fund},
            "sentiment": {"score": float(score_social), "meta": meta_social},
            "derivative": {"score": float(score_deriv), "meta": meta_deriv},
        },
        "insider": {
            "buys": insider_buys,
            "sells": insider_sells,
            "booster": float(insider_booster),
        },
        "chart_data": chart_data,
        "competitors": competitors,
    }

    return clean_dict(response)
