import argparse
import sys
import os
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backtesting.data_manager import BacktestingDataManager, SECTORS, ALL_TICKERS
from backtesting.engine import RuleBasedBacktester

def main():
    parser = argparse.ArgumentParser(description="AI Stock Evaluator Backtester CLI")
    parser.add_argument("--download-only", action="store_true", help="Download Yahoo Finance data and build cache, then exit.")
    parser.add_argument("--force-download", action="store_true", help="Force re-downloading data and overwrite cache.")
    parser.add_argument("--tickers", type=str, default="", help="Comma-separated list of tickers (e.g. AAPL,MSFT). Default: uses whole sector universe.")
    parser.add_argument("--sector", type=str, default="All", choices=["All"] + list(SECTORS.keys()), help="Backtest a specific sector's tickers. Default: All.")
    parser.add_argument("--start", type=str, default="2023-01-01", help="Backtest start date (YYYY-MM-DD).")
    parser.add_argument("--end", type=str, default="2024-06-01", help="Backtest end date (YYYY-MM-DD).")
    parser.add_argument("--capital", type=float, default=100000.0, help="Initial capital. Default: 100000.0.")
    parser.add_argument("--portfolio-size", type=int, default=3, help="Portfolio size (Top-K selection).")
    parser.add_argument("--horizons", type=str, default="21,63,126,252", help="Comma-separated list of rebalance intervals (trading days).")
    
    args = parser.parse_args()

    # Handle data cache loading/downloading
    manager = BacktestingDataManager()
    if args.download_only or args.force_download or not os.path.exists(manager.cache_file):
        print("Building data cache from Yahoo Finance. This will download historical prices and financials...")
        manager.build_cache(start_date=args.start, end_date=args.end, force=args.force_download)
        if args.download_only:
            print("Download finished. Cache created successfully.")
            return

    # Select tickers
    if args.tickers:
        selected_tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
    elif args.sector != "All":
        selected_tickers = SECTORS[args.sector]
        print(f"Selecting tickers in sector: {args.sector} (Total: {len(selected_tickers)})")
    else:
        selected_tickers = ALL_TICKERS
        print(f"Selecting all {len(selected_tickers)} tickers in universe.")

    # Instantiate and run backtester
    print(f"Running simulation from {args.start} to {args.end} with initial capital ${args.capital:,.2f}...")
    print(f"Portfolio Rebalancing Rules: Hold Top-{args.portfolio_size} assets. Rebalance every interval.")
    
    backtester = RuleBasedBacktester(
        tickers=selected_tickers,
        start_date=args.start,
        end_date=args.end,
        initial_capital=args.capital,
        portfolio_size=args.portfolio_size
    )
    
    try:
        horizons_list = [int(h.strip()) for h in args.horizons.split(",") if h.strip().isdigit()]
    except Exception:
        horizons_list = [21, 63, 126, 252]
    if not horizons_list:
        horizons_list = [21, 63, 126, 252]

    results = backtester.run_simulation(horizons_list=horizons_list)
    
    if not results or "horizons" not in results:
        print("No simulation results. Please verify that data cache contains historical data for the selected range.")
        return

    # Output results nicely
    print("\n" + "="*80)
    print("           PORTFOLIO BACKTEST SUMMARY")
    print("="*80)
    print("{:<12} | {:<10} | {:<12} | {:<8} | {:<8} | {:<8}".format(
        "Horizon", "Return", "Bench Return", "Sharpe", "Sortino", "Max DD"
    ))
    print("-"*80)
    for name, horizon_data in results["horizons"].items():
        summary = horizon_data["summary"]
        print("{:<12} | {:>9}% | {:>11}% | {:>8} | {:>8} | {:>7}%".format(
            name, summary["cumulative_return"], summary["benchmark_return"],
            summary["sharpe_ratio"], summary["sortino_ratio"], summary["max_drawdown"]
        ))
    print("="*80)
    
    # Information Hit Precision
    first_horizon_key = list(results["horizons"].keys())[0]
    first_horizon = results["horizons"][first_horizon_key]
    hp = first_horizon["hit_precision"]
    print("\n" + "="*80)
    print("           INFORMATION HIT PRECISION")
    print("="*80)
    print(f"Sample size (Score >= 80):     {hp['sample_size']} observations")
    print(f"T+10 Outperformance vs Median: {hp['t10']}%")
    print(f"T+30 Outperformance vs Median: {hp['t30']}%")
    print(f"T+60 Outperformance vs Median: {hp['t60']}%")
    print("="*80)

    # Print best and worst performing assets in the first horizon
    details = first_horizon["ticker_details"]
    sorted_tickers = sorted(details.items(), key=lambda item: item[1]["cumulative_return"], reverse=True)
    
    clean_h_name = first_horizon_key.replace('_days', '').replace('_', ' ')
    print(f"\nTop 5 Performing Tickers ({clean_h_name} Horizon):")
    for t, m in sorted_tickers[:5]:
        print(f"  {t}: +{m['cumulative_return']}% (Trades: {m['trade_count']}, Days Held: {m['days_held']})")
        
    print(f"\nBottom 5 Performing Tickers ({clean_h_name} Horizon):")
    for t, m in sorted_tickers[-5:]:
        print(f"  {t}: {m['cumulative_return']}% (Trades: {m['trade_count']}, Days Held: {m['days_held']})")

if __name__ == "__main__":
    main()
