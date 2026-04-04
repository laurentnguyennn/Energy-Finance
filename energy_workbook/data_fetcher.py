"""
Data acquisition module.
Fetches price data and macro data via OpenBB Platform.
"""
import os
import warnings
import numpy as np
import pandas as pd

from .config import (
    START_DATE, END_DATE, ALL_TICKERS, MARKET_TICKER,
    COMMODITY_YAHOO, FRED_SERIES, FRED_API_KEY, VG_IPO_DATE,
    EVENT_WINDOWS,
)

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message="invalid value encountered in log", category=RuntimeWarning)

# ---------------------------------------------------------------------------
# OpenBB initialisation
# ---------------------------------------------------------------------------
from openbb import obb

# Configure FRED API key for OpenBB if available
_fred_key = FRED_API_KEY or os.environ.get("FRED_API_KEY")
if _fred_key:
    try:
        obb.user.credentials.fred_api_key = _fred_key
    except Exception:
        pass  # key will be picked up from env or user_settings.json


# ---------------------------------------------------------------------------
# Price helpers
# ---------------------------------------------------------------------------

def fetch_equity_prices(tickers, start=START_DATE, end=END_DATE):
    """Fetch adjusted close prices via OpenBB (yfinance provider)."""
    print(f"  Fetching OpenBB equity data for {len(tickers)} tickers...")
    frames = {}
    for ticker in tickers:
        try:
            result = obb.equity.price.historical(
                symbol=ticker,
                start_date=start,
                end_date=end,
                provider="yfinance",
                adjustment="splits_and_dividends",
            )
            df = result.to_df()
            if not df.empty:
                frames[ticker] = df["close"]
        except Exception as e:
            print(f"    WARNING: Failed to fetch {ticker}: {e}")

    if not frames:
        return pd.DataFrame()

    prices = pd.DataFrame(frames)
    prices.index = pd.to_datetime(prices.index)
    prices.index.name = "Date"
    return prices


def fetch_commodity_prices(tickers_map, start=START_DATE, end=END_DATE):
    """Fetch commodity / index prices via OpenBB (yfinance provider).

    tickers_map: dict mapping friendly name -> Yahoo symbol, e.g. {"Gold": "GC=F"}
    """
    print(f"  Fetching OpenBB commodity/index data for {len(tickers_map)} tickers...")
    frames = {}
    for name, yahoo_sym in tickers_map.items():
        try:
            result = obb.equity.price.historical(
                symbol=yahoo_sym,
                start_date=start,
                end_date=end,
                provider="yfinance",
            )
            df = result.to_df()
            if not df.empty:
                frames[name] = df["close"]
        except Exception as e:
            print(f"    WARNING: Failed to fetch {name} ({yahoo_sym}): {e}")

    if not frames:
        return pd.DataFrame()

    prices = pd.DataFrame(frames)
    prices.index = pd.to_datetime(prices.index)
    prices.index.name = "Date"
    return prices


# ---------------------------------------------------------------------------
# FRED macro data
# ---------------------------------------------------------------------------

def fetch_fred_data(start=START_DATE, end=END_DATE):
    """Fetch macro series from FRED via OpenBB. Returns DataFrame with all series."""
    if not _fred_key:
        print("  WARNING: No FRED API key found. Set FRED_API_KEY env var or config.FRED_API_KEY.")
        print("  Creating empty FRED columns — fill manually or re-run with key.")
        return _create_empty_fred(start, end)

    frames = {}
    for name, series_id in FRED_SERIES.items():
        try:
            print(f"    Fetching FRED via OpenBB: {name} ({series_id})...")
            result = obb.economy.fred_series(
                symbol=series_id,
                start_date=start,
                end_date=end,
                provider="fred",
            )
            df = result.to_df()
            if not df.empty:
                # fred_series returns a 'value' column
                col = "value" if "value" in df.columns else df.columns[0]
                frames[name] = df[col]
        except Exception as e:
            print(f"    FAILED to fetch {name}: {e}")
            frames[name] = pd.Series(dtype=float)

    df = pd.DataFrame(frames)
    df.index = pd.to_datetime(df.index)
    return df


def _create_empty_fred(start, end):
    """Create empty DataFrame with FRED column names for manual population."""
    idx = pd.bdate_range(start, end)
    return pd.DataFrame(index=idx, columns=list(FRED_SERIES.keys()), dtype=float)


# ---------------------------------------------------------------------------
# Master fetch
# ---------------------------------------------------------------------------

def fetch_all_data():
    """Master data fetch. Returns a dict with all needed DataFrames."""
    print("=" * 60)
    print("FETCHING MARKET DATA (via OpenBB)")
    print("=" * 60)

    # 1) Equity + BIL prices
    print("\n[1/4] Equity & ETF prices...")
    equity_prices = fetch_equity_prices(ALL_TICKERS)

    # 2) Market benchmark (SPY)
    print("\n[2/4] Market benchmark (SPY)...")
    spy_prices = fetch_equity_prices([MARKET_TICKER])

    # 3) Commodity / volatility indices
    print("\n[3/4] Commodity & volatility indices...")
    try:
        yahoo_macro = fetch_commodity_prices(COMMODITY_YAHOO)
    except Exception as e:
        print(f"  WARNING: Failed to fetch some macro tickers: {e}")
        yahoo_macro = pd.DataFrame(index=equity_prices.index,
                                   columns=list(COMMODITY_YAHOO.keys()), dtype=float)

    # 4) FRED data
    print("\n[4/4] FRED macro data...")
    fred_data = fetch_fred_data()

    # ── Assemble master DataFrame ───────────────────────────────────────
    print("\nAssembling master data frame...")
    master = equity_prices.copy()
    master = master.join(spy_prices.rename(columns={MARKET_TICKER: "SPY"}), how="outer")

    # Join FRED daily data — reindex to business days
    fred_daily = fred_data.reindex(master.index)
    master = master.join(fred_daily, how="left", rsuffix="_fred")

    # Join Yahoo macro data
    master = master.join(yahoo_macro, how="left", rsuffix="_ymacro")

    # ── Computed series ─────────────────────────────────────────────────
    if "Brent" in master.columns and "WTI" in master.columns:
        master["Brent_WTI_Spread"] = master["Brent"] - master["WTI"]
    else:
        master["Brent_WTI_Spread"] = np.nan

    if "TTF" in master.columns and "HenryHub" in master.columns:
        master["TTF_HH_Spread"] = master["TTF"] - master["HenryHub"]
    else:
        master["TTF_HH_Spread"] = np.nan

    if "DGS10" in master.columns and "DGS2" in master.columns:
        master["Spread_2s10s"] = master["DGS10"] - master["DGS2"]
    else:
        master["Spread_2s10s"] = np.nan

    # ── Forward-fill monthly series to daily ────────────────────────────
    for col in ["CPI", "CPI_Energy", "IndProd", "UMich"]:
        if col in master.columns:
            master[col] = master[col].ffill()

    # ── VG: blank before IPO ────────────────────────────────────────────
    if "VG" in master.columns:
        master.loc[master.index < VG_IPO_DATE, "VG"] = np.nan

    # ── Drop fully empty rows ───────────────────────────────────────────
    master = master.dropna(how="all")

    # ── Compute log returns ─────────────────────────────────────────────
    return_cols = ALL_TICKERS + ["SPY"]
    if "WTI" in master.columns:
        return_cols.append("WTI")
    if "Brent" in master.columns:
        return_cols.append("Brent")

    log_returns = pd.DataFrame(index=master.index)
    for col in return_cols:
        if col in master.columns:
            log_returns[col] = np.log(master[col] / master[col].shift(1))

    # First differences for VIX, OVX, 2s10s, DXY, Breakeven, MOVE
    diffs = pd.DataFrame(index=master.index)
    diff_cols = {
        "dVIX": "VIX", "dOVX": "OVX", "dSpread_2s10s": "Spread_2s10s",
        "dT10YIE": "T10YIE", "dBrent_WTI_Spread": "Brent_WTI_Spread",
        "dTTF_HH_Spread": "TTF_HH_Spread", "dMOVE": "MOVE",
    }
    for new_name, src in diff_cols.items():
        if src in master.columns:
            diffs[new_name] = master[src].diff()

    # DXY log return
    if "DXY" in master.columns:
        diffs["dDXY_log"] = np.log(master["DXY"] / master["DXY"].shift(1))

    # ── Event labels ────────────────────────────────────────────────────
    master["Event_ID"] = 0
    master["Event_Label"] = "Unclassified"
    for eid, (label, start_dt, end_dt) in EVENT_WINDOWS.items():
        mask = (master.index >= start_dt) & (master.index <= end_dt)
        master.loc[mask, "Event_ID"] = eid
        master.loc[mask, "Event_Label"] = label

    # ── Regime flags ─────────────────────────────────────────────────────
    # OVX_Stress and VIX_Stress: expanding 90th percentile (min 60 obs before flagging)
    ovx_series = master.get("OVX", pd.Series(dtype=float))
    vix_series = master.get("VIX", pd.Series(dtype=float))
    ovx_90 = ovx_series.expanding(min_periods=60).quantile(0.9)
    vix_90 = vix_series.expanding(min_periods=60).quantile(0.9)
    master["OVX_Stress"] = (ovx_series > ovx_90).astype(int).fillna(0)
    master["VIX_Stress"] = (vix_series > vix_90).astype(int).fillna(0)

    master["Conflict_Period"] = 0
    conflict_windows = [
        ("2020-02-20", "2020-06-30"),   # COVID
        ("2022-02-24", "2022-12-31"),   # Russia-Ukraine
        ("2025-06-01", "2025-06-30"),   # 12-Day War
        ("2026-02-28", END_DATE),       # Iran Conflict
    ]
    for cs_start, cs_end in conflict_windows:
        mask = (master.index >= cs_start) & (master.index <= cs_end)
        master.loc[mask, "Conflict_Period"] = 1

    print(f"\nData assembled: {len(master)} rows, {len(master.columns)} columns")
    print(f"Date range: {master.index[0].date()} to {master.index[-1].date()}")

    return {
        "master": master,
        "log_returns": log_returns,
        "diffs": diffs,
        "equity_prices": equity_prices,
    }
