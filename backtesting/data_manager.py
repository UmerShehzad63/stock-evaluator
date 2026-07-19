import os
import pickle
import logging
import pandas as pd
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

SECTORS = {
    "Technology & Communication": [
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "AVGO", "CSCO", "ORCL", "ADBE", "NFLX", "AMD", "CRM", "QCOM", "INTC"
    ],
    "Financials & Banking": [
        "JPM", "BAC", "MS", "GS", "WFC", "C", "V", "MA", "AXP", "BLK", "SCHW", "BRK-B"  # yfinance uses BRK-B instead of BRK.B
    ],
    "Healthcare & Pharmaceuticals": [
        "JNJ", "LLY", "UNH", "PFE", "ABBV", "MRK", "TMO", "DHR", "ISRG", "BMY", "AMGN", "GILD"
    ],
    "Consumer Discretionary & Retail": [
        "TSLA", "HD", "NKE", "MCD", "SBUX", "LOW", "TJX", "TGT", "BKNG", "CMG", "ORLY"
    ],
    "Industrials, Aerospace & Logistics": [
        "CAT", "GE", "UNP", "HON", "UPS", "FDX", "LMT", "RTX", "DE", "ETN", "WM"
    ],
    "Energy & Infrastructure": [
        "XOM", "CVX", "COP", "SLB", "EOG", "MPC", "PSX", "VLO", "KMI"
    ],
    "Consumer Staples": [
        "PG", "KO", "PEP", "COST", "WMT", "PM", "MO", "CL", "EL"
    ],
    "Basic Materials & Mining": [
        "LIN", "APD", "FCX", "NEM", "NUE", "SHW", "DD"
    ],
    "Utilities & Power Generation": [
        "NEE", "SO", "DUK", "AEP", "D", "EXC", "SRE"
    ],
    "Real Estate & Trusts": [
        "PLD", "AMT", "CCI", "EQIX", "O", "SPG", "PSA"
    ]
}

ALL_TICKERS = []
for t_list in SECTORS.values():
    ALL_TICKERS.extend(t_list)

CACHE_DIR = os.path.join(os.path.dirname(__file__), "cache")
CACHE_FILE = os.path.join(CACHE_DIR, "data_cache.pkl")

class BacktestingDataManager:
    def __init__(self, cache_file=CACHE_FILE):
        self.cache_file = cache_file
        self.data_cache = {}

    def load_cache(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'rb') as f:
                    self.data_cache = pickle.load(f)
                logging.info(f"Loaded data cache from {self.cache_file}. Total cached tickers: {len(self.data_cache.keys()) - 1}")
                return True
            except Exception as e:
                logging.error(f"Error loading cache: {e}. Will re-download.")
        return False

    def save_cache(self):
        os.makedirs(CACHE_DIR, exist_ok=True)
        try:
            with open(self.cache_file, 'wb') as f:
                pickle.dump(self.data_cache, f)
            logging.info(f"Successfully saved data cache to {self.cache_file}")
        except Exception as e:
            logging.error(f"Error saving cache: {e}")

    def download_ticker_data(self, ticker, start_date="2021-01-01", end_date="2026-07-20"):
        logging.info(f"Downloading data for {ticker}...")
        try:
            t = yf.Ticker(ticker)
            # Fetch 1d historical prices (extend start_date back by 300 days to allow for 200 SMA lookback)
            start_dt = pd.to_datetime(start_date)
            extended_start = (start_dt - pd.Timedelta(days=365)).strftime('%Y-%m-%d')
            
            prices = t.history(start=extended_start, end=end_date, interval="1d")
            if prices.empty:
                logging.warning(f"No price data found for {ticker}")
                return None

            # Get historical statements
            financials = t.quarterly_financials
            balance_sheet = t.quarterly_balance_sheet
            cashflow = t.quarterly_cashflow
            
            # If quarterly is empty, try annual
            if financials.empty:
                financials = t.financials
            if balance_sheet.empty:
                balance_sheet = t.balance_sheet
            if cashflow.empty:
                cashflow = t.cashflow

            # Get current info (sector, longName, trailingPE, etc.) for fallback
            info = {}
            try:
                info = t.info
            except Exception:
                pass

            ticker_data = {
                "prices": prices,
                "financials": financials,
                "balance_sheet": balance_sheet,
                "cashflow": cashflow,
                "info": info
            }
            return ticker_data
        except Exception as e:
            logging.error(f"Failed to download data for {ticker}: {e}")
            return None

    def build_cache(self, start_date="2021-01-01", end_date="2026-07-20", force=False):
        if not force and self.load_cache():
            return

        logging.info("Rebuilding backtesting cache from Yahoo Finance. This will take a moment...")
        self.data_cache = {}
        
        # Also download SPY as benchmark
        tickers_to_download = ALL_TICKERS + ["SPY"]
        
        with ThreadPoolExecutor(max_workers=8) as executor:
            future_to_ticker = {
                executor.submit(self.download_ticker_data, ticker, start_date, end_date): ticker 
                for ticker in tickers_to_download
            }
            
            for future in as_completed(future_to_ticker):
                ticker = future_to_ticker[future]
                try:
                    res = future.result()
                    if res:
                        self.data_cache[ticker] = res
                except Exception as e:
                    logging.error(f"Exception downloading {ticker}: {e}")

        self.save_cache()

    def get_ticker_data(self, ticker):
        # Handle BRK.B mapping
        if ticker == "BRK.B":
            ticker = "BRK-B"
        return self.data_cache.get(ticker)

    def get_benchmark_prices(self):
        spy_data = self.data_cache.get("SPY")
        if spy_data:
            return spy_data["prices"]
        # Fallback fetch
        return yf.Ticker("SPY").history(period="5y")

if __name__ == "__main__":
    manager = BacktestingDataManager()
    manager.build_cache(force=True)
