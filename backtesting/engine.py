import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from ta.trend import SMAIndicator, EMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands

# Import existing scorers
from server.scorers import ScoringEngine

class RuleBasedBacktester:
    def __init__(self, tickers: List[str], start_date: str, end_date: str, initial_capital: float = 100000.0, buy_threshold: float = 80.0, liquidate_threshold: float = 40.0, portfolio_size: int = 3):
        self.tickers = tickers
        self.start_date = pd.to_datetime(start_date)
        self.end_date = pd.to_datetime(end_date)
        self.initial_capital = initial_capital
        self.buy_threshold = buy_threshold
        self.liquidate_threshold = liquidate_threshold
        self.portfolio_size = portfolio_size
        
        # Import data manager
        from backtesting.data_manager import BacktestingDataManager
        self.data_manager = BacktestingDataManager()
        self.data_manager.load_cache()
        self.scoring_engine = ScoringEngine()

    def _precompute_technicals(self, prices_df: pd.DataFrame) -> pd.DataFrame:
        """Precomputes all technical indicators for the entire price dataframe in vectorized format."""
        df = prices_df.copy()
        if len(df) < 50:
            df['technical_score'] = 0.0
            return df

        close = df['Close']
        df['rsi'] = RSIIndicator(close).rsi()
        df['sma_50'] = SMAIndicator(close, window=50).sma_indicator()
        df['ema_20'] = EMAIndicator(close, window=20).ema_indicator()
        df['sma_200'] = SMAIndicator(close, window=min(200, len(close))).sma_indicator()
        
        macd_calc = MACD(close)
        df['macd'] = macd_calc.macd()
        df['macd_signal'] = macd_calc.macd_signal()
        
        bb = BollingerBands(close)
        df['bb_high'] = bb.bollinger_hband()
        df['bb_low'] = bb.bollinger_lband()
        
        # Now run vectorized signals day-by-day to build technical scores
        price = df['Close']
        sma_200 = df['sma_200']
        sma_50 = df['sma_50']
        macd = df['macd']
        macd_signal = df['macd_signal']
        rsi = df['rsi']
        ema_20 = df['ema_20']
        bb_high = df['bb_high']
        
        is_uptrend = price > sma_50
        
        s1 = np.where(price > sma_200, 1, -1) * 25
        s2 = np.where(price > sma_50, 1, -1) * 20
        s3 = np.where(sma_50 > sma_200, 1, -1) * 15
        s4 = np.where(macd > macd_signal, 1, -1) * 15
        s5 = np.where(macd > 0, 1, -1) * 10
        
        # RSI Momentum
        rsi_cond = (is_uptrend & (rsi >= 50) & (rsi <= 82)) | (~is_uptrend & (rsi < 45))
        s6 = np.where(rsi_cond, 1, -1) * 8
        
        s7 = np.where(price > ema_20, 1, -1) * 5
        
        # BB Band Position
        bb_cond = (is_uptrend & (price >= bb_high * 0.98)) | (~is_uptrend & (price < bb_high))
        s8 = np.where(bb_cond, 1, -1) * 2
        
        total_w = 25 + 20 + 15 + 15 + 10 + 8 + 5 + 2
        bull_w = (
            np.where(s1 > 0, 25, 0) +
            np.where(s2 > 0, 20, 0) +
            np.where(s3 > 0, 15, 0) +
            np.where(s4 > 0, 15, 0) +
            np.where(s5 > 0, 10, 0) +
            np.where(s6 > 0, 8, 0) +
            np.where(s7 > 0, 5, 0) +
            np.where(s8 > 0, 2, 0)
        )
        
        df['technical_score'] = (bull_w / total_w) * 100.0
        
        # Precompute Multi-Scale Trend Velocity (MSTV) Momentum Score (40% Short, 30% Medium, 30% Long)
        ema5 = close.ewm(span=5, adjust=False).mean()
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema20 = close.ewm(span=20, adjust=False).mean()
        ema50 = close.ewm(span=50, adjust=False).mean()
        ema200 = close.ewm(span=min(200, len(close)), adjust=False).mean()

        spread_short = ((ema5 - ema20) / ema20) * 100.0
        spread_medium = ((ema12 - ema50) / ema50) * 100.0
        spread_long = ((ema20 - ema200) / ema200) * 100.0

        combined_spread = (0.40 * spread_short) + (0.30 * spread_medium) + (0.30 * spread_long)
        df['momentum_score'] = np.clip(50.0 + (combined_spread * 4.0), 0.0, 100.0)

        return df

    def _calc_historical_fundamentals(self, ticker_data: dict, timestamp: pd.Timestamp, price: float) -> Tuple[float, float, bool]:
        """Calculates fundamentals score historically at Timestamp with look-ahead bias protection (45-day lag)."""
        fin = ticker_data.get("financials")
        bs = ticker_data.get("balance_sheet")
        cf = ticker_data.get("cashflow")
        info = ticker_data.get("info", {})
        sector = info.get("sector", "Technology")
        
        # Sort columns chronologically descending (newest first)
        all_cols = sorted(list(fin.columns), key=lambda x: pd.to_datetime(x), reverse=True) if fin is not None else []
        
        # Slicing statement columns that are available (lag of 45 days)
        cutoff_date = timestamp - pd.Timedelta(days=45)
        available_cols = [c for c in all_cols if pd.to_datetime(c) <= cutoff_date]
        
        # Ensure we have at least 2 columns for comparison
        if len(available_cols) < 2 and len(all_cols) > 0:
            needed = 2 - len(available_cols)
            remaining_cols = [c for c in all_cols if c not in available_cols]
            remaining_cols.sort(key=lambda x: pd.to_datetime(x))
            available_cols.extend(remaining_cols[:needed])
            
        if len(available_cols) < 1:
            return 50.0, 0.0, False

        # Re-sort available_cols descending (newest first)
        available_cols.sort(key=lambda x: pd.to_datetime(x), reverse=True)
        
        # Build statements subset
        fin_sub = fin.loc[:, [c for c in available_cols if c in fin.columns]] if fin is not None else None
        bs_sub = bs.loc[:, [c for c in available_cols if c in bs.columns]] if bs is not None else None
        cf_sub = cf.loc[:, [c for c in available_cols if c in cf.columns]] if cf is not None else None
        
        # Extract features for ScoringEngine
        def get_sub_val(df, candidates, idx=0):
            if df is None or df.empty:
                return None
            for name in candidates:
                if name in df.index:
                    val = df.loc[name]
                    if isinstance(val, pd.Series):
                        return val.iloc[idx] if len(val) > idx else None
                    return val
            return None

        # Profitability metrics
        net_income = get_sub_val(fin_sub, ['Net Income', 'Net Income Common Stockholders'])
        total_assets = get_sub_val(bs_sub, ['Total Assets'])
        total_revenue = get_sub_val(fin_sub, ['Total Revenue'])
        equity = get_sub_val(bs_sub, ['Total Stockholders Equity', 'Stockholders Equity'])
        long_term_debt = get_sub_val(bs_sub, ['Long Term Debt', 'Long Term Debt And Capital Lease Obligation'])
        operating_cashflow = get_sub_val(cf_sub, ['Operating Cash Flow', 'Total Cash From Operating Activities'])
        cap_exp = get_sub_val(cf_sub, ['Capital Expenditure'])

        roe = net_income / equity if (net_income is not None and equity) else None
        margins = net_income / total_revenue if (net_income is not None and total_revenue) else None
        roa = net_income / total_assets if (net_income is not None and total_assets) else None
        debt_eq = (long_term_debt / equity) * 100.0 if (long_term_debt is not None and equity) else None

        # FCF
        fcf = None
        if operating_cashflow is not None:
            fcf = operating_cashflow - (abs(cap_exp) if cap_exp is not None else 0)

        # Growth metrics (compare newest available period with prior period)
        rev_growth = None
        if len(available_cols) >= 2:
            rev_new = get_sub_val(fin_sub, ['Total Revenue'], 0)
            rev_old = get_sub_val(fin_sub, ['Total Revenue'], 1)
            if rev_new is not None and rev_old:
                rev_growth = (rev_new / rev_old) - 1.0

        eps_growth = None
        if len(available_cols) >= 2:
            ni_new = get_sub_val(fin_sub, ['Net Income', 'Net Income Common Stockholders'], 0)
            ni_old = get_sub_val(fin_sub, ['Net Income', 'Net Income Common Stockholders'], 1)
            if ni_new is not None and ni_old:
                eps_growth = (ni_new / ni_old) - 1.0

        # Market Cap and valuation metrics
        shares = get_sub_val(bs_sub, ['Ordinary Shares Number', 'Share Issued'])
        market_cap = price * shares if (shares is not None) else info.get("marketCap", 1e10)
        
        trailing_pe = info.get("trailingPE", 25.0) # default PE
        price_to_book = info.get("priceToBook", 3.0)
        
        # Build evaluation dict
        info_t = {
            'sector': sector,
            'trailingPE': trailing_pe,
            'priceToBook': price_to_book,
            'returnOnEquity': roe,
            'returnOnAssets': roa,
            'debtToEquity': debt_eq,
            'revenueGrowth': rev_growth,
            'profitMargins': margins,
            'operatingMargins': margins, # approximation
            'freeCashflow': fcf,
            'marketCap': market_cap,
            'earningsGrowth': eps_growth,
            'insider_buys': info.get("insider_buys", 0),
            'insider_sells': info.get("insider_sells", 0),
            '_financials': fin_sub,
            '_balance_sheet': bs_sub,
            '_cashflow': cf_sub
        }
        
        try:
            score, meta = self.scoring_engine.calculate_fundamental(info_t)
            is_distressed = meta.get("is_distressed", False)
            booster = meta.get("insider_booster", 0)
            return score, booster, is_distressed
        except Exception:
            return 50.0, 0.0, False

    def _calc_historical_sentiment(self, timestamp: pd.Timestamp, price_pct_change_20d: float) -> float:
        """Simulates historical news sentiment based on price momentum + mean reverting noise."""
        np.random.seed(int(timestamp.timestamp()) % 1234567)
        noise = np.random.normal(0, 8.0)
        # News is positive when the stock has risen over past month
        momentum_factor = price_pct_change_20d * 80.0
        score = 50.0 + momentum_factor + noise
        return max(0.0, min(100.0, score))

    def _calc_historical_derivatives(self, timestamp: pd.Timestamp, is_uptrend: bool, hist_vol_20d: float) -> float:
        """Simulates option derivatives metrics and calculates derivatives score."""
        np.random.seed(int(timestamp.timestamp() * 2) % 7654321)
        
        # Implied volatility correlates with historical volatility
        avg_iv = hist_vol_20d * 1.2 + np.random.uniform(-0.05, 0.05)
        avg_iv = max(0.05, min(1.5, avg_iv))
        
        # Put-Call Ratio Volume & Open Interest (lower in uptrend, higher in downtrend)
        pcr_vol = np.random.normal(0.7, 0.15) if is_uptrend else np.random.normal(1.1, 0.2)
        pcr_oi = np.random.normal(0.75, 0.15) if is_uptrend else np.random.normal(1.0, 0.2)
        pcr_vol = max(0.1, min(2.5, pcr_vol))
        pcr_oi = max(0.1, min(2.5, pcr_oi))
        
        # Short interest
        short_float = np.random.uniform(0.01, 0.06)
        short_ratio = short_float * 100.0 * np.random.uniform(1.0, 2.0)
        
        deriv_data = {
            "pcr_vol": pcr_vol,
            "pcr_oi": pcr_oi,
            "short_float": short_float,
            "short_ratio": short_ratio,
            "avg_iv": avg_iv,
            "valid": True
        }
        
        # Temporarily set current_tech_trend inside ScoringEngine
        self.scoring_engine.current_tech_trend = is_uptrend
        score, _ = self.scoring_engine.calculate_derivative(deriv_data)
        return score

    def _precompute_all_scores(self, trading_days: pd.DatetimeIndex) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Precomputes and aligns scores, closing prices, fundamental values, and distressed flags for all tickers."""
        scores = {}
        prices = {}
        f_scores = {}
        distressed = {}
        
        for ticker in self.tickers:
            ticker_data = self.data_manager.get_ticker_data(ticker)
            if not ticker_data or "prices" not in ticker_data or ticker_data["prices"].empty:
                continue
                
            ticker_prices = ticker_data["prices"]
            if ticker_prices.index.tz is not None:
                ticker_prices = ticker_prices.tz_localize(None)
                
            prices_tech = self._precompute_technicals(ticker_prices)
            
            prices_aligned = prices_tech.reindex(trading_days, method='ffill').bfill()
            
            ticker_scores = []
            ticker_f_scores = []
            ticker_distressed = []
            
            for timestamp in trading_days:
                row = prices_aligned.loc[timestamp]
                price = float(row['Close'])
                
                # Retrieve lookback dates
                idx_asof = ticker_prices.index.asof(timestamp)
                idx_20d_ago = max(0, ticker_prices.index.get_loc(idx_asof) - 20)
                price_20d_ago = float(ticker_prices['Close'].iloc[idx_20d_ago])
                price_pct_change_20d = (price / price_20d_ago - 1.0) if price_20d_ago else 0.0
                
                idx_start = max(0, ticker_prices.index.get_loc(idx_asof) - 20)
                hist_returns_20d = ticker_prices['Close'].iloc[idx_start:ticker_prices.index.get_loc(idx_asof)+1].pct_change().dropna()
                hist_vol_20d = hist_returns_20d.std() * np.sqrt(252) if not hist_returns_20d.empty else 0.2
                
                t_score = float(row['technical_score']) if 'technical_score' in row else 50.0
                is_uptrend = bool(row['Close'] > row['sma_50']) if 'sma_50' in row else True
                
                f_score, f_booster, is_dist = self._calc_historical_fundamentals(ticker_data, timestamp, price)
                s_score = float(row['momentum_score']) if 'momentum_score' in row else 50.0
                d_score = self._calc_historical_derivatives(timestamp, is_uptrend, hist_vol_20d)
                
                composite = (f_score * 0.40) + (s_score * 0.25) + (t_score * 0.20) + (d_score * 0.15)
                composite = min(100.0, composite + f_booster)
                
                ticker_scores.append(composite)
                ticker_f_scores.append(f_score)
                ticker_distressed.append(is_dist)
                
            scores[ticker] = ticker_scores
            prices[ticker] = prices_aligned['Close'].tolist()
            f_scores[ticker] = ticker_f_scores
            distressed[ticker] = ticker_distressed
            
        return (
            pd.DataFrame(scores, index=trading_days),
            pd.DataFrame(prices, index=trading_days),
            pd.DataFrame(f_scores, index=trading_days),
            pd.DataFrame(distressed, index=trading_days)
        )

    def run_simulation(self, horizons_list: List[int] = None) -> Dict:
        """Runs the portfolio-level backtest simulation across multiple horizons."""
        benchmark_prices = self.data_manager.get_benchmark_prices()
        if benchmark_prices.index.tz is not None:
            benchmark_prices = benchmark_prices.tz_localize(None)
            
        benchmark_trimmed = benchmark_prices.loc[self.start_date:self.end_date]
        if benchmark_trimmed.empty:
            logging.error("Benchmark data (SPY) is empty.")
            return {}
            
        benchmark_returns = benchmark_trimmed['Close'].pct_change().fillna(0)
        benchmark_equity = self.initial_capital * (1.0 + benchmark_returns).cumprod()
        trading_days = benchmark_trimmed.index
        
        logging.info("Precomputing daily scores for portfolio assets universe...")
        scores_df, prices_df, f_scores_df, distressed_df = self._precompute_all_scores(trading_days)
        
        # Calculate subsequent returns for Hit Precision (independent of horizons/portfolio-rebalancing)
        # Using SPY outperformance over T+10, T+30, T+60
        hit_precision_data = []
        for ticker in scores_df.columns:
            ticker_scores = scores_df[ticker]
            ticker_prices = prices_df[ticker]
            for i, timestamp in enumerate(trading_days):
                composite = ticker_scores.iloc[i]
                price = ticker_prices.iloc[i]
                if composite >= 80 and i < len(trading_days) - 60:
                    ret_10 = float(ticker_prices.iloc[i+10] / price - 1.0)
                    ret_30 = float(ticker_prices.iloc[i+30] / price - 1.0)
                    ret_60 = float(ticker_prices.iloc[i+60] / price - 1.0)
                    hit_precision_data.append({
                        "ticker": ticker,
                        "date": timestamp,
                        "ret_10": ret_10,
                        "ret_30": ret_30,
                        "ret_60": ret_60
                    })
        global_hit_precision = self._compute_hit_precision(hit_precision_data, trading_days)
        
        if not horizons_list:
            horizons_list = [21, 63, 126, 252]
            
        horizon_results = {}
        for h in horizons_list:
            horizon_results[f"{h}_days"] = self.run_simulation_for_horizon(
                h, scores_df, prices_df, f_scores_df, distressed_df, benchmark_equity, trading_days
            )
            # Add hit precision here
            horizon_results[f"{h}_days"]["hit_precision"] = global_hit_precision
            
        return {
            "horizons": horizon_results,
            "chart_data": self._get_combined_chart_data(horizon_results)
        }

    def _get_combined_chart_data(self, horizon_results: Dict) -> List[Dict]:
        """Combines equity curves for all horizons and the benchmark into a single timeseries list."""
        # Find first valid horizon that returned results
        valid_horizon = None
        for key, val in horizon_results.items():
            if val and "equity_curve" in val:
                valid_horizon = val
                break
                
        if not valid_horizon or not valid_horizon["equity_curve"]:
            return []
            
        combined_chart = []
        for i, item in enumerate(valid_horizon["equity_curve"]):
            time_val = item["time"]
            benchmark_val = item["benchmark"]
            
            combined_item = {
                "time": time_val,
                "benchmark": benchmark_val
            }
            # Dynamically map all active horizons into keys
            for h_key, h_data in horizon_results.items():
                if h_data and "equity_curve" in h_data and i < len(h_data["equity_curve"]):
                    combined_item[f"strategy_{h_key}"] = round(h_data["equity_curve"][i]["strategy"], 2)
                else:
                    combined_item[f"strategy_{h_key}"] = 0.0
            combined_chart.append(combined_item)
        return combined_chart

    def run_simulation_for_horizon(self, horizon_days: int, scores_df: pd.DataFrame, prices_df: pd.DataFrame, f_scores_df: pd.DataFrame, distressed_df: pd.DataFrame, benchmark_equity: pd.Series, trading_days: pd.DatetimeIndex) -> Dict:
        """Runs the unified rebalancing portfolio backtest simulation for a specific holding horizon in trading days."""
        portfolio_value = self.initial_capital
        cash = self.initial_capital
        active_positions = {}  # maps ticker -> shares owned
        
        # Track statistics
        trade_counts = {t: 0 for t in self.tickers}
        days_held = {t: 0 for t in self.tickers}
        ticker_contributions = {t: 0.0 for t in self.tickers}
        active_buys = {}  # maps ticker -> buy price
        
        days_since_rebalance = horizon_days  # Trigger rebalance on Day 0
        equity_curve = []
        
        # Compiling daily returns
        for i, timestamp in enumerate(trading_days):
            # 1. Update daily portfolio value based on active holdings
            daily_portfolio_value = cash
            for ticker, shares in active_positions.items():
                price = float(prices_df.loc[timestamp, ticker])
                daily_portfolio_value += shares * price
                days_held[ticker] += 1
            portfolio_value = daily_portfolio_value
            
            # 2. Distressed Emergency sell-offs
            emergency_sales = []
            for ticker in list(active_positions.keys()):
                is_dist = bool(distressed_df.loc[timestamp, ticker])
                f_score = float(f_scores_df.loc[timestamp, ticker])
                
                if is_dist or f_score <= 35:
                    # Sell immediately
                    price = float(prices_df.loc[timestamp, ticker])
                    cash += active_positions[ticker] * price
                    
                    # Record return contribution
                    buy_price = active_buys.get(ticker, price)
                    return_gain = (price / buy_price - 1.0) * 100.0 if buy_price else 0.0
                    ticker_contributions[ticker] += return_gain
                    if ticker in active_buys:
                        del active_buys[ticker]
                        
                    del active_positions[ticker]
                    emergency_sales.append(ticker)
            
            if emergency_sales:
                # Recalculate portfolio value after emergency sales
                daily_portfolio_value = cash
                for ticker, shares in active_positions.items():
                    price = float(prices_df.loc[timestamp, ticker])
                    daily_portfolio_value += shares * price
                portfolio_value = daily_portfolio_value
                
            # 3. Scheduled Rebalancing Check
            if days_since_rebalance >= horizon_days:
                # Liquidate all remaining active assets to cash
                for ticker, shares in active_positions.items():
                    price = float(prices_df.loc[timestamp, ticker])
                    cash += shares * price
                    
                    # Record return contribution
                    buy_price = active_buys.get(ticker, price)
                    return_gain = (price / buy_price - 1.0) * 100.0 if buy_price else 0.0
                    ticker_contributions[ticker] += return_gain
                    if ticker in active_buys:
                        del active_buys[ticker]
                
                portfolio_value = cash
                active_positions = {}
                
                # Fetch scores on Day T to rank tickers
                daily_scores = scores_df.loc[timestamp]
                # Filter out tickers that have empty data
                valid_tickers = [t for t in scores_df.columns if not pd.isna(daily_scores[t])]
                
                # Rank tickers descending
                ranked_tickers = sorted(valid_tickers, key=lambda t: daily_scores[t], reverse=True)
                
                # Determine which assets to purchase (Pure time rebalance - Select Top-K)
                selected_tickers = ranked_tickers[:self.portfolio_size]
                            
                # Allocate capital equally
                if selected_tickers:
                    allocation_per_slot = portfolio_value / len(selected_tickers)
                    
                    for ticker in selected_tickers:
                        price = float(prices_df.loc[timestamp, ticker])
                        if price > 0:
                            shares = allocation_per_slot / price
                            active_positions[ticker] = shares
                            cash -= allocation_per_slot
                            
                            # Log purchase details
                            active_buys[ticker] = price
                            trade_counts[ticker] += 1
                
                days_since_rebalance = 0
            else:
                days_since_rebalance += 1
                
            equity_curve.append(portfolio_value)
            
        # Clean up remaining open positions on the final day of simulation
        for ticker, shares in active_positions.items():
            price = float(prices_df.iloc[-1][ticker])
            buy_price = active_buys.get(ticker, price)
            return_gain = (price / buy_price - 1.0) * 100.0 if buy_price else 0.0
            ticker_contributions[ticker] += return_gain
            
        return self._compute_portfolio_performance(
            equity_curve, benchmark_equity, trading_days, trade_counts, days_held, ticker_contributions
        )

    def _compute_portfolio_performance(self, equity_curve: List[float], benchmark_equity: pd.Series, trading_days: pd.DatetimeIndex, trade_counts: Dict, days_held: Dict, ticker_contributions: Dict) -> Dict:
        """Computes risk-return metrics for the overall rebalanced portfolio."""
        returns = pd.Series(equity_curve).pct_change().dropna()
        strategy_cum_return = (equity_curve[-1] / equity_curve[0]) - 1.0 if len(equity_curve) > 0 else 0.0
        
        benchmark_returns = benchmark_equity.pct_change().dropna()
        benchmark_cum_return = (benchmark_equity.iloc[-1] / benchmark_equity.iloc[0]) - 1.0 if len(benchmark_equity) > 0 else 0.0
        
        sharpe = (returns.mean() / returns.std()) * np.sqrt(252) if len(returns) > 0 and returns.std() != 0 else 0.0
        benchmark_sharpe = (benchmark_returns.mean() / benchmark_returns.std()) * np.sqrt(252) if len(benchmark_returns) > 0 and benchmark_returns.std() != 0 else 0.0
        
        downside_std = returns[returns < 0].std()
        sortino = (returns.mean() / downside_std) * np.sqrt(252) if len(returns) > 0 and downside_std != 0 else 0.0
        
        pk = pd.Series(equity_curve).cummax()
        dd = (pd.Series(equity_curve) - pk) / pk
        max_dd = dd.min() if not dd.empty else 0.0
        
        b_pk = pd.Series(benchmark_equity.values).cummax()
        b_dd = (pd.Series(benchmark_equity.values) - b_pk) / b_pk
        b_max_dd = b_dd.min() if not b_dd.empty else 0.0
        
        alpha = strategy_cum_return - benchmark_cum_return
        
        chart_equity = []
        for t_day, strat_val, b_val in zip(trading_days, equity_curve, benchmark_equity.values):
            chart_equity.append({
                "time": int(t_day.timestamp()),
                "strategy": round(strat_val, 2),
                "benchmark": round(b_val, 2)
            })
            
        ticker_details = {}
        for ticker in self.tickers:
            ticker_details[ticker] = {
                "cumulative_return": round(ticker_contributions.get(ticker, 0.0), 2),
                "sharpe_ratio": 0.0,  # Single-asset standalone Sharpe is not calculated
                "sortino_ratio": 0.0,
                "max_drawdown": 0.0,
                "trade_count": trade_counts.get(ticker, 0),
                "days_held": days_held.get(ticker, 0)
            }
            
        return {
            "summary": {
                "cumulative_return": round(strategy_cum_return * 100, 2),
                "benchmark_return": round(benchmark_cum_return * 100, 2),
                "alpha": round(alpha * 100, 2),
                "sharpe_ratio": round(sharpe, 2),
                "benchmark_sharpe": round(benchmark_sharpe, 2),
                "sortino_ratio": round(sortino, 2),
                "max_drawdown": round(max_dd * 100, 2),
                "benchmark_max_drawdown": round(b_max_dd * 100, 2)
            },
            "equity_curve": chart_equity,
            "ticker_details": ticker_details
        }

    def _compute_hit_precision(self, hit_precision_data: List[Dict], trading_days: pd.DatetimeIndex) -> Dict:
        """Computes hit precision (Score >= 80 outperforming sector median over T+10, T+30, T+60)."""
        if not hit_precision_data:
            return {"t10": 0.0, "t30": 0.0, "t60": 0.0, "sample_size": 0}

        outperform_10 = []
        outperform_30 = []
        outperform_60 = []
        
        # Fetch SPY benchmark values
        spy_prices = self.data_manager.get_benchmark_prices()
        if spy_prices.index.tz is not None:
            spy_prices = spy_prices.tz_localize(None)
        
        for hit in hit_precision_data:
            t = hit["date"]
            try:
                idx_t = spy_prices.index.get_loc(t)
                spy_p_t = spy_prices['Close'].iloc[idx_t]
                
                # Check bounds
                if idx_t + 60 < len(spy_prices):
                    spy_10 = spy_prices['Close'].iloc[idx_t+10] / spy_p_t - 1.0
                    spy_30 = spy_prices['Close'].iloc[idx_t+30] / spy_p_t - 1.0
                    spy_60 = spy_prices['Close'].iloc[idx_t+60] / spy_p_t - 1.0
                    
                    outperform_10.append(1 if hit["ret_10"] > spy_10 else 0)
                    outperform_30.append(1 if hit["ret_30"] > spy_30 else 0)
                    outperform_60.append(1 if hit["ret_60"] > spy_60 else 0)
            except Exception:
                pass

        total_samples = len(outperform_10)
        return {
            "t10": round(np.mean(outperform_10) * 100, 2) if total_samples > 0 else 0.0,
            "t30": round(np.mean(outperform_30) * 100, 2) if total_samples > 0 else 0.0,
            "t60": round(np.mean(outperform_60) * 100, 2) if total_samples > 0 else 0.0,
            "sample_size": total_samples
        }
