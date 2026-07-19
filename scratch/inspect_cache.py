import os
import sys
import pickle
import pandas as pd

# Add project root to path
sys.path.append(r"c:\Users\umers\OneDrive\Desktop\stock evaluator\project")

from backtesting.engine import RuleBasedBacktester

backtester = RuleBasedBacktester(
    tickers=["AAPL"],
    start_date="2023-01-01",
    end_date="2024-06-01"
)

ticker_data = backtester.data_manager.get_ticker_data("AAPL")
timestamp = pd.to_datetime("2023-06-01")
price = 180.0

fin = ticker_data.get("financials")
bs = ticker_data.get("balance_sheet")
cf = ticker_data.get("cashflow")
info = ticker_data.get("info", {})
sector = info.get("sector", "Technology")

# Sort columns chronologically descending (newest first)
all_cols = sorted(list(fin.columns), key=lambda x: pd.to_datetime(x), reverse=True) if fin is not None else []

cutoff_date = timestamp - pd.Timedelta(days=45)
available_cols = [c for c in all_cols if pd.to_datetime(c) <= cutoff_date]

print("Initial available columns:", available_cols)

if len(available_cols) < 2:
    needed = 2 - len(available_cols)
    remaining_cols = [c for c in all_cols if c not in available_cols]
    remaining_cols.sort(key=lambda x: pd.to_datetime(x))
    available_cols.extend(remaining_cols[:needed])

available_cols.sort(key=lambda x: pd.to_datetime(x), reverse=True)
print("Padded available columns:", available_cols)

if len(available_cols) >= 2:
    fin_sub = fin.loc[:, available_cols]
    bs_sub = bs.loc[:, available_cols]
    cf_sub = cf.loc[:, available_cols]
    
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
    fcf = operating_cashflow - (abs(cap_exp) if cap_exp is not None else 0) if operating_cashflow is not None else None

    # Let's see if yfinance statements are shaped properly for ScoringEngine
    info_t = {
        'sector': sector,
        'trailingPE': info.get("trailingPE", 25.0),
        'priceToBook': info.get("priceToBook", 3.0),
        'returnOnEquity': roe,
        'returnOnAssets': roa,
        'debtToEquity': debt_eq,
        'revenueGrowth': 0.1,  # mock
        'profitMargins': margins,
        'operatingMargins': margins,
        'freeCashflow': fcf,
        'marketCap': price * 1e9,
        'earningsGrowth': 0.1, # mock
        'insider_buys': info.get("insider_buys", 0),
        'insider_sells': info.get("insider_sells", 0),
        '_financials': fin_sub,
        '_balance_sheet': bs_sub,
        '_cashflow': cf_sub
    }
    
    score, meta = backtester.scoring_engine.calculate_fundamental(info_t)
    print("Final Score computed by engine:", score)
    print("Meta keys:", list(meta.keys()))
