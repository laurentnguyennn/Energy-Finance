"""
Tabs 16–20: Macro Transmission Channels, Pair Trade & Relative Value,
Sector-Level Factor Decomposition, Backtesting, Executive Dashboard.
"""
import numpy as np
import pandas as pd
from openpyxl.chart import BarChart, LineChart, ScatterChart, Reference
from openpyxl.utils import get_column_letter

from .config import (
    ALL_TICKERS, EQUITY_TICKERS, FUNDAMENTALS, RF_RATE, PORTFOLIO_VALUE,
    TAB_NAMES, TAB_COLORS, REGIME_NAMES, PAIRS, EVENT_WINDOWS,
    SCENARIO_NAMES, SCENARIO_PROBS,
)
from .styles import (
    FONT_HEADER, FONT_TITLE, FONT_SUBTITLE, FONT_NORMAL, FONT_INPUT,
    FONT_LINKED,
    FILL_HEADER, FILL_INPUT, FILL_LIGHT_GREEN, FILL_LIGHT_RED, FILL_LIGHT_BLUE,
    THIN_BORDER, BOTTOM_BORDER, ALIGN_CENTER,
    FMT_PCT, FMT_NUM2, FMT_NUM3, FMT_NUM4, FMT_DATE, FMT_MONEY, FMT_INT,
    style_header_row, write_table, auto_width, set_tab_color,
    add_correlation_coloring,
)
from .formulas import (
    sheet_ref, sheet_range, f_log_spread, f_z_score,
    add_definition,
)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 16 — MACRO TRANSMISSION CHANNELS
# ═══════════════════════════════════════════════════════════════════════════════
def build_tab_16(wb, data, results):
    ws = wb.create_sheet(title=TAB_NAMES[16])
    set_tab_color(ws, TAB_COLORS["purple"])

    log_ret = data["log_returns"]
    master = data["master"]
    diffs = data["diffs"]

    ws["A1"] = "MACRO TRANSMISSION CHANNELS"
    ws["A1"].font = FONT_TITLE

    row = add_definition(ws, 2, 1, "Macro Transmission Channels",
        "Five channels transmit the Iran conflict shock to each security: "
        "(1) Oil Supply → E&P equity via WTI β, (2) Freight Rate → Tankers via Brent-WTI spread, "
        "(3) LNG Substitution → LNG exporters via TTF-HH spread, "
        "(4) Oil → Inflation → Yield Curve → All equities (lagged), "
        "(5) OVX Regime → conditional risk metrics.",
        "OXY/COP: Ch1 dominant. FRO/STNG: Ch2. LNG/VG: Ch3. ET: minimal all channels")
    row += 1

    # ── Channel 1: Oil Supply → E&P Returns ─────────────────────────────
    ws.cell(row=row, column=1, value="CHANNEL 1: OIL SUPPLY DISRUPTION → E&P EQUITY RETURNS").font = FONT_SUBTITLE
    row += 1
    ws.cell(row=row, column=1, value="Lead-lag analysis: COP/OXY returns regressed on lagged WTI returns (OLS β coefficients)")
    row += 1

    lag_list = list(range(0, 11))  # lags 0 through 10
    lag_headers = ["Ticker"] + [f"β Lag {lag}d" for lag in lag_list] + ["Cumul. Response"]
    for j, h in enumerate(lag_headers):
        ws.cell(row=row, column=j + 1, value=h).font = FONT_HEADER
        ws.cell(row=row, column=j + 1).fill = FILL_HEADER
    row += 1

    wti_ret = log_ret.get("WTI", pd.Series(dtype=float)).dropna()
    for ticker in ["COP", "OXY", "XOM", "CVX"]:
        stock_ret = log_ret.get(ticker, pd.Series(dtype=float)).dropna()
        ws.cell(row=row, column=1, value=ticker)
        cumul = 0.0
        for j, lag in enumerate(lag_list):
            wti_lagged = wti_ret.shift(lag)
            c_idx = wti_lagged.dropna().index.intersection(stock_ret.dropna().index)
            if len(c_idx) > 10:
                x_vals = wti_lagged[c_idx].values
                y_vals = stock_ret[c_idx].values
                X = np.column_stack([np.ones(len(x_vals)), x_vals])
                beta = np.linalg.lstsq(X, y_vals, rcond=None)[0]
                # beta[1] is the regression coefficient, beta[0] is intercept
                b1 = float(beta[1])
                cumul += b1
                ws.cell(row=row, column=j + 2, value=round(b1, 4)).number_format = FMT_NUM4
            else:
                ws.cell(row=row, column=j + 2, value="N/A")
        ws.cell(row=row, column=len(lag_list) + 2, value=round(cumul, 4)).number_format = FMT_NUM4
        row += 1

    # ── Channel 2: Freight Rate → Tanker Returns ────────────────────────
    row += 2
    ws.cell(row=row, column=1, value="CHANNEL 2: FREIGHT RATE SHOCK → TANKER EQUITY RETURNS").font = FONT_SUBTITLE
    row += 1
    ws.cell(row=row, column=1, value="OLS regression of FRO/STNG returns on ΔBrent-WTI Spread")
    row += 1

    ch2_headers = ["Security", "β (regression coeff)", "Std Error", "R²"]
    for j, h in enumerate(ch2_headers):
        ws.cell(row=row, column=j + 1, value=h).font = FONT_HEADER
        ws.cell(row=row, column=j + 1).fill = FILL_HEADER
    row += 1

    bws_diff = diffs.get("dBrent_WTI_Spread", pd.Series(dtype=float)).dropna()
    for ticker in ["FRO", "STNG"]:
        stock_ret = log_ret.get(ticker, pd.Series(dtype=float)).dropna()
        common = bws_diff.index.intersection(stock_ret.index)
        ws.cell(row=row, column=1, value=ticker)
        if len(common) > 30:
            x_vals = bws_diff[common].values
            y_vals = stock_ret[common].values
            X = np.column_stack([np.ones(len(x_vals)), x_vals])
            beta = np.linalg.lstsq(X, y_vals, rcond=None)[0]
            b1 = float(beta[1])
            resid = y_vals - X @ beta
            n, k = len(y_vals), 2
            mse = np.sum(resid ** 2) / (n - k)
            try:
                XtX_inv = np.linalg.inv(X.T @ X)
                se = float(np.sqrt(np.diag(XtX_inv) * mse)[1])
            except Exception:
                se = np.nan
            sst = np.sum((y_vals - y_vals.mean()) ** 2)
            sse = np.sum(resid ** 2)
            r2 = float(1 - sse / sst) if sst > 0 else 0.0
            ws.cell(row=row, column=2, value=round(b1, 4)).number_format = FMT_NUM4
            ws.cell(row=row, column=3, value=round(se, 4) if not np.isnan(se) else "N/A").number_format = FMT_NUM4
            ws.cell(row=row, column=4, value=round(r2, 4)).number_format = FMT_NUM4
        row += 1

    # ── Channel 3: LNG Substitution ─────────────────────────────────────
    row += 2
    ws.cell(row=row, column=1, value="CHANNEL 3: LNG SUPPLY SUBSTITUTION → LNG EQUITY RETURNS").font = FONT_SUBTITLE
    row += 1
    ws.cell(row=row, column=1, value="OLS regression of LNG/VG returns on ΔTTF-HH Spread")
    row += 1

    ch3_headers = ["Security", "β (regression coeff)", "R²"]
    for j, h in enumerate(ch3_headers):
        ws.cell(row=row, column=j + 1, value=h).font = FONT_HEADER
        ws.cell(row=row, column=j + 1).fill = FILL_HEADER
    row += 1

    ttf_diff = diffs.get("dTTF_HH_Spread", pd.Series(dtype=float)).dropna()
    for ticker in ["LNG", "VG"]:
        stock_ret = log_ret.get(ticker, pd.Series(dtype=float)).dropna()
        common = ttf_diff.index.intersection(stock_ret.index)
        ws.cell(row=row, column=1, value=ticker)
        if len(common) > 30:
            x_vals = ttf_diff[common].values
            y_vals = stock_ret[common].values
            X = np.column_stack([np.ones(len(x_vals)), x_vals])
            beta = np.linalg.lstsq(X, y_vals, rcond=None)[0]
            b1 = float(beta[1])
            resid = y_vals - X @ beta
            sst = np.sum((y_vals - y_vals.mean()) ** 2)
            sse = np.sum(resid ** 2)
            r2 = float(1 - sse / sst) if sst > 0 else 0.0
            ws.cell(row=row, column=2, value=round(b1, 4)).number_format = FMT_NUM4
            ws.cell(row=row, column=3, value=round(r2, 4)).number_format = FMT_NUM4
        row += 1

    # ── Channel 4: Oil → Inflation → Yield Curve → Equities ────────────
    row += 2
    ws.cell(row=row, column=1, value="CHANNEL 4: OIL → INFLATION → FED → YIELD CURVE → EQUITIES").font = FONT_SUBTITLE
    row += 1

    lag_chain_headers = ["Link", "Lag 0", "Lag 5d", "Lag 10d", "Lag 20d", "Lag 40d", "Lag 60d"]
    for j, h in enumerate(lag_chain_headers):
        ws.cell(row=row, column=j + 1, value=h).font = FONT_HEADER
        ws.cell(row=row, column=j + 1).fill = FILL_HEADER
    row += 1

    # WTI → Breakeven
    bev_diff = diffs.get("dT10YIE", pd.Series(dtype=float)).dropna()
    links = [
        ("ΔWTI → ΔBreakeven", wti_ret, bev_diff),
    ]
    s2s10_diff = diffs.get("dSpread_2s10s", pd.Series(dtype=float)).dropna()
    if len(bev_diff) > 0 and len(s2s10_diff) > 0:
        links.append(("ΔBreakeven → Δ2s10s", bev_diff, s2s10_diff))

    for label, x_series, y_series in links:
        ws.cell(row=row, column=1, value=label)
        for j, lag in enumerate([0, 5, 10, 20, 40, 60]):
            x_lagged = x_series.shift(lag)
            common = x_lagged.dropna().index.intersection(y_series.dropna().index)
            if len(common) > 10:
                corr = np.corrcoef(x_lagged[common], y_series[common])[0, 1]
                ws.cell(row=row, column=j + 2, value=round(corr, 3)).number_format = FMT_NUM3
        row += 1

    # Link 3: Yield Curve → Equity Returns
    row += 1
    ws.cell(row=row, column=1, value="Link 3: Δ2s10s → Stock Returns").font = FONT_HEADER
    row += 1

    # Headers: Lag, then one column per equity ticker
    link3_tickers = [t for t in ["XOM", "CVX", "COP", "OXY", "LNG", "VG", "FRO", "STNG", "ET"] if t in log_ret.columns]
    link3_headers = ["Lag (days)"] + link3_tickers
    for j, h in enumerate(link3_headers):
        ws.cell(row=row, column=j + 1, value=h).font = FONT_HEADER
        ws.cell(row=row, column=j + 1).fill = FILL_HEADER
    row += 1

    spread_diff = diffs.get("dSpread_2s10s", pd.Series(dtype=float))
    for lag in [0, 5, 10, 20, 40, 60]:
        ws.cell(row=row, column=1, value=lag)
        x_shifted = spread_diff.shift(lag)
        for j, t in enumerate(link3_tickers):
            if t in log_ret.columns:
                y = log_ret[t]
                common = pd.DataFrame({"x": x_shifted, "y": y}).dropna()
                if len(common) > 30:
                    corr = common["x"].corr(common["y"])
                    ws.cell(row=row, column=j + 2, value=round(corr, 4)).number_format = FMT_NUM4
        row += 1

    # ── Channel 5: OVX Regime Conditional Metrics ───────────────────────
    row += 2
    ws.cell(row=row, column=1, value="CHANNEL 5: OVX REGIME → CONDITIONAL RISK METRICS").font = FONT_SUBTITLE
    row += 1

    ovx = master.get("OVX", pd.Series(dtype=float))
    ovx_90 = ovx.expanding().quantile(0.9)
    stress_mask = ovx > ovx_90
    calm_mask = ~stress_mask & ovx.notna()

    ch5_headers = ["Security", "Calm Vol (ann)", "Stress Vol (ann)", "Vol Multiplier", "Calm Mean (ann)", "Stress Mean (ann)"]
    for j, h in enumerate(ch5_headers):
        ws.cell(row=row, column=j + 1, value=h).font = FONT_HEADER
        ws.cell(row=row, column=j + 1).fill = FILL_HEADER
    row += 1

    for ticker in ALL_TICKERS:
        rets = log_ret.get(ticker, pd.Series(dtype=float)).dropna()
        calm_rets = rets[calm_mask.reindex(rets.index, fill_value=False)]
        stress_rets = rets[stress_mask.reindex(rets.index, fill_value=False)]

        ws.cell(row=row, column=1, value=ticker)
        if len(calm_rets) > 5:
            calm_vol = float(calm_rets.std() * np.sqrt(252))
            calm_mean = float(calm_rets.mean() * 252)
            ws.cell(row=row, column=2, value=calm_vol).number_format = FMT_PCT
            ws.cell(row=row, column=5, value=calm_mean).number_format = FMT_PCT
        else:
            calm_vol = 0
        if len(stress_rets) > 5:
            stress_vol = float(stress_rets.std() * np.sqrt(252))
            stress_mean = float(stress_rets.mean() * 252)
            ws.cell(row=row, column=3, value=stress_vol).number_format = FMT_PCT
            ws.cell(row=row, column=6, value=stress_mean).number_format = FMT_PCT
        else:
            stress_vol = 0
        multiplier = stress_vol / calm_vol if calm_vol > 0 else 0
        ws.cell(row=row, column=4, value=round(multiplier, 2)).number_format = '0.00x'
        row += 1

    # ── Channel Summary Table ───────────────────────────────────────────
    row += 2
    ws.cell(row=row, column=1, value="CHANNEL CONTRIBUTION SUMMARY").font = FONT_SUBTITLE
    row += 1
    summary_data = [
        ["Oil Supply", "COP, OXY, XOM, CVX", "ET (if prolonged)", "WTI β₁", "Tab 6"],
        ["Freight Rate", "FRO, STNG", "—", "Brent-WTI spread β", "Tab 6 (ship)"],
        ["LNG Substitution", "LNG, VG", "—", "TTF-HH spread β", "Tab 6 (LNG)"],
        ["Inflation Chain", "BIL, Gold", "All equities (lagged)", "Lead-lag corr", "Tab 16 Ch4"],
        ["Vol Regime", "VIX hedges, BIL", "High-beta equities", "Stress/Calm ratio", "Tab 16 Ch5"],
    ]
    sum_headers = ["Channel", "Primary Beneficiaries", "Primary Victims", "Key Metric", "Tab Reference"]
    for j, h in enumerate(sum_headers):
        ws.cell(row=row, column=j + 1, value=h).font = FONT_HEADER
        ws.cell(row=row, column=j + 1).fill = FILL_HEADER
    row += 1
    for srow in summary_data:
        for j, val in enumerate(srow):
            ws.cell(row=row, column=j + 1, value=val)
        row += 1

    auto_width(ws)
    return results


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 17 — PAIR TRADE & RELATIVE VALUE ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════
def build_tab_17(wb, data, results):
    ws = wb.create_sheet(title=TAB_NAMES[17])
    set_tab_color(ws, TAB_COLORS["purple"])

    log_ret = data["log_returns"]
    master = data["master"]

    ws["A1"] = "PAIR TRADE & RELATIVE VALUE ANALYSIS"
    ws["A1"].font = FONT_TITLE

    row = add_definition(ws, 2, 1, "Pair Trade / Relative Value",
        "Log Spread = LN(Price_A) - LN(Price_B). Z-Score = (Spread - RollingMean) / RollingStdDev. "
        "Signal: Z > +2 → short A / long B; Z < -2 → long A / short B. "
        "Half-life = -LN(2)/LN(1+β) from ΔSpread regressed on Spread_{t-1}.",
        "Cointegrated pairs (half-life < 30d) are tradeable. Current Z-scores and signals below.")
    row += 1

    tab1_name = results.get("tab1_name", TAB_NAMES[1])
    price_col_map = results.get("tab1_price_col_map", {})
    t1_end = results.get("tab1_last_data_row", 1000)

    pair_summary_data = []

    for ticker_a, ticker_b, label in PAIRS:
        ws.cell(row=row, column=1, value=f"PAIR: {ticker_a} vs {ticker_b} ({label})").font = FONT_SUBTITLE
        row += 1

        if ticker_a not in master.columns or ticker_b not in master.columns:
            ws.cell(row=row, column=1, value="Price data not available for this pair")
            row += 2
            continue

        pa = master[ticker_a].dropna()
        pb = master[ticker_b].dropna()
        common = pa.index.intersection(pb.index)
        if len(common) < 60:
            ws.cell(row=row, column=1, value="Insufficient overlapping data")
            row += 2
            continue

        pa = pa[common]
        pb = pb[common]

        # Log spread
        spread = np.log(pa) - np.log(pb)

        # Rolling stats (60-day)
        roll_mean = spread.rolling(60).mean()
        roll_std = spread.rolling(60).std()
        z_score = (spread - roll_mean) / roll_std

        # Mean reversion half-life
        spread_lag = spread.shift(1)
        d_spread = spread.diff()
        valid = spread_lag.notna() & d_spread.notna()
        if valid.sum() > 10:
            x = spread_lag[valid].values
            y = d_spread[valid].values
            # FIX #10: OLS with intercept instead of zero-intercept regression
            X_ols = np.column_stack([np.ones(len(x)), x])
            betas_mr = np.linalg.lstsq(X_ols, y, rcond=None)[0]
            beta_mr = betas_mr[1]  # slope coefficient
            half_life = -np.log(2) / np.log(1 + beta_mr) if beta_mr < 0 and (1 + beta_mr) > 0 else np.nan
        else:
            half_life = np.nan

        # Pair correlation
        ra = log_ret.get(ticker_a, pd.Series(dtype=float)).dropna()
        rb = log_ret.get(ticker_b, pd.Series(dtype=float)).dropna()
        common_r = ra.index.intersection(rb.index)
        pair_corr = np.corrcoef(ra[common_r], rb[common_r])[0, 1] if len(common_r) > 10 else np.nan

        # Current signal
        current_z = float(z_score.iloc[-1]) if len(z_score.dropna()) > 0 else np.nan

        # Cointegration flag: half-life < 30 days → treat as cointegrated
        coint_flag = "Cointegrated" if (not np.isnan(half_life) and 0 < half_life < 30) else "Not Cointegrated"

        # ── Cross-sheet linked current prices ──────────────────────────
        ws.cell(row=row, column=1, value=f"Price {ticker_a} (→Tab 1)")
        if ticker_a in price_col_map:
            c = ws.cell(row=row, column=2,
                        value=f"='{tab1_name}'!{price_col_map[ticker_a]}{t1_end}")
            c.number_format = FMT_MONEY
            c.font = FONT_LINKED
        else:
            ws.cell(row=row, column=2, value=round(float(pa.iloc[-1]), 2)).number_format = FMT_MONEY
        pa_cell = f"B{row}"
        row += 1

        ws.cell(row=row, column=1, value=f"Price {ticker_b} (→Tab 1)")
        if ticker_b in price_col_map:
            c = ws.cell(row=row, column=2,
                        value=f"='{tab1_name}'!{price_col_map[ticker_b]}{t1_end}")
            c.number_format = FMT_MONEY
            c.font = FONT_LINKED
        else:
            ws.cell(row=row, column=2, value=round(float(pb.iloc[-1]), 2)).number_format = FMT_MONEY
        pb_cell = f"B{row}"
        row += 1

        # Current log spread as Excel formula referencing the linked prices
        ws.cell(row=row, column=1, value="Current Log Spread (formula)")
        ws.cell(row=row, column=2, value=f_log_spread(pa_cell, pb_cell)).number_format = FMT_NUM4
        row += 1

        # Write summary metrics
        metrics = [
            ("Current Z-Score", round(current_z, 2) if not np.isnan(current_z) else "N/A"),
            ("Half-Life (days)", round(half_life, 1) if not np.isnan(half_life) else "N/A"),
            ("Cointegration", coint_flag),
            ("Pair Correlation", round(pair_corr, 3) if not np.isnan(pair_corr) else "N/A"),
            ("Signal", "SHORT A/LONG B" if current_z > 2 else "LONG A/SHORT B" if current_z < -2 else "NEUTRAL"),
        ]
        for label_m, val in metrics:
            ws.cell(row=row, column=1, value=label_m)
            c = ws.cell(row=row, column=2, value=val)
            if label_m == "Signal":
                if val == "NEUTRAL":
                    c.fill = FILL_INPUT
                else:
                    c.fill = FILL_LIGHT_GREEN
            elif label_m == "Cointegration":
                c.fill = FILL_LIGHT_GREEN if val == "Cointegrated" else FILL_LIGHT_RED
            row += 1

        pair_summary_data.append({
            "pair": f"{ticker_a}/{ticker_b}",
            "z_score": current_z,
            "half_life": half_life,
            "correlation": pair_corr,
        })

        # Write Z-score time series (sampled for chart)
        row += 1
        ws.cell(row=row, column=1, value="Date").font = FONT_HEADER
        ws.cell(row=row, column=2, value="Z-Score").font = FONT_HEADER
        ws.cell(row=row, column=3, value="+2σ").font = FONT_HEADER
        ws.cell(row=row, column=4, value="-2σ").font = FONT_HEADER
        row += 1

        z_clean = z_score.dropna()
        sample = z_clean.iloc[::5]  # every 5th day
        chart_start_row = row
        for dt, val in sample.items():
            ws.cell(row=row, column=1, value=dt.date()).number_format = FMT_DATE
            ws.cell(row=row, column=2, value=round(float(val), 3)).number_format = FMT_NUM3
            ws.cell(row=row, column=3, value=2.0)
            ws.cell(row=row, column=4, value=-2.0)
            row += 1

        # Z-score chart
        if row > chart_start_row + 5:
            chart = LineChart()
            chart.title = f"Z-Score: {ticker_a} vs {ticker_b}"
            chart.y_axis.title = "Z-Score"
            chart.width = 25
            chart.height = 12
            for col_idx in [2, 3, 4]:
                data_ref = Reference(ws, min_col=col_idx, min_row=chart_start_row - 1, max_row=row - 1)
                chart.add_data(data_ref, titles_from_data=True)
            cats = Reference(ws, min_col=1, min_row=chart_start_row, max_row=row - 1)
            chart.set_categories(cats)
            ws.add_chart(chart, f"F{chart_start_row}")

        row += 2

    results["pair_summary"] = pair_summary_data
    auto_width(ws)
    return results


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 18 — SECTOR-LEVEL FACTOR DECOMPOSITION
# ═══════════════════════════════════════════════════════════════════════════════
def build_tab_18(wb, data, results):
    ws = wb.create_sheet(title=TAB_NAMES[18])
    set_tab_color(ws, TAB_COLORS["purple"])

    log_ret = data["log_returns"]
    diffs = data["diffs"]

    ws["A1"] = "SECTOR-LEVEL FACTOR DECOMPOSITION"
    ws["A1"].font = FONT_TITLE

    row = add_definition(ws, 2, 1, "Fama-French Style Factor Decomposition",
        "R_i - Rf = α + β_mkt(Mkt-Rf) + β_oil(WTI) + β_size(SMB) + β_value(HML) "
        "+ β_gas(ΔGas) + β_freight(ΔFreight) + ε. "
        "SMB = avg(FRO,STNG) - avg(XOM,CVX). HML = avg(OXY,ET) - avg(LNG,VG). "
        "Target stock excluded from its own factor to avoid endogeneity.",
        "Significant α (t>2) = genuine stock-specific outperformance beyond factor exposure")
    row += 1

    # Build factors
    spy_ret = log_ret.get("SPY", pd.Series(dtype=float))
    wti_ret = log_ret.get("WTI", pd.Series(dtype=float))

    # Size factor: small energy - large energy
    small = pd.DataFrame()
    large = pd.DataFrame()
    for t in ["FRO", "STNG"]:
        if t in log_ret.columns:
            small[t] = log_ret[t]
    for t in ["XOM", "CVX"]:
        if t in log_ret.columns:
            large[t] = log_ret[t]
    smb = small.mean(axis=1) - large.mean(axis=1) if len(small.columns) > 0 and len(large.columns) > 0 else pd.Series(dtype=float)

    # Value factor: high B/M - low B/M
    high_bm = pd.DataFrame()
    low_bm = pd.DataFrame()
    for t in ["OXY", "ET"]:
        if t in log_ret.columns:
            high_bm[t] = log_ret[t]
    for t in ["LNG", "VG"]:
        if t in log_ret.columns:
            low_bm[t] = log_ret[t]
    hml = high_bm.mean(axis=1) - low_bm.mean(axis=1) if len(high_bm.columns) > 0 and len(low_bm.columns) > 0 else pd.Series(dtype=float)

    gas_factor = diffs.get("dTTF_HH_Spread", pd.Series(dtype=float))
    freight_factor = diffs.get("dBrent_WTI_Spread", pd.Series(dtype=float))

    # Build factor matrix
    factors = pd.DataFrame({
        "Mkt-Rf": spy_ret - RF_RATE / 252,
        "Oil": wti_ret,
        "SMB": smb,
        "HML": hml,
        "Gas": gas_factor,
        "Freight": freight_factor,
    }).dropna()

    if len(factors) < 30:
        ws["A3"] = "Insufficient data for factor decomposition"
        return results

    # ── Factor Regression for each security ─────────────────────────────
    ws.cell(row=row, column=1, value="ALPHA TABLE").font = FONT_SUBTITLE
    row += 1
    alpha_headers = ["Security", "α (annualized)", "t-stat(α)", "R²", "Mkt β", "Oil β", "SMB β", "HML β", "Gas β", "Freight β"]
    for j, h in enumerate(alpha_headers):
        ws.cell(row=row, column=j + 1, value=h).font = FONT_HEADER
        ws.cell(row=row, column=j + 1).fill = FILL_HEADER
    row += 1

    factor_results = {}
    # FIX #19: Pre-define factor groups so we can exclude the target stock
    smb_small_tickers = ["FRO", "STNG"]
    smb_large_tickers = ["XOM", "CVX"]
    hml_high_tickers = ["OXY", "ET"]
    hml_low_tickers = ["LNG", "VG"]

    for ticker in EQUITY_TICKERS:
        y = log_ret.get(ticker, pd.Series(dtype=float))

        # Rebuild SMB/HML excluding the target ticker to avoid endogeneity
        small_ex = pd.DataFrame({t: log_ret[t] for t in smb_small_tickers if t in log_ret.columns and t != ticker})
        large_ex = pd.DataFrame({t: log_ret[t] for t in smb_large_tickers if t in log_ret.columns and t != ticker})
        smb_ex = (small_ex.mean(axis=1) - large_ex.mean(axis=1)) if len(small_ex.columns) > 0 and len(large_ex.columns) > 0 else smb

        high_ex = pd.DataFrame({t: log_ret[t] for t in hml_high_tickers if t in log_ret.columns and t != ticker})
        low_ex = pd.DataFrame({t: log_ret[t] for t in hml_low_tickers if t in log_ret.columns and t != ticker})
        hml_ex = (high_ex.mean(axis=1) - low_ex.mean(axis=1)) if len(high_ex.columns) > 0 and len(low_ex.columns) > 0 else hml

        # Build ticker-specific factor matrix
        factors_ex = pd.DataFrame({
            "Mkt-Rf": spy_ret - RF_RATE / 252,
            "Oil": wti_ret,
            "SMB": smb_ex,
            "HML": hml_ex,
            "Gas": gas_factor,
            "Freight": freight_factor,
        }).dropna()

        common = factors_ex.index.intersection(y.dropna().index)
        if len(common) < 30:
            ws.cell(row=row, column=1, value=ticker)
            row += 1
            continue

        Y = y[common].values - RF_RATE / 252  # excess returns
        X = factors_ex.loc[common].values
        X_c = np.column_stack([np.ones(len(Y)), X])

        try:
            XtX_inv = np.linalg.inv(X_c.T @ X_c)
            betas = XtX_inv @ X_c.T @ Y
            resid = Y - X_c @ betas
            n_obs = len(Y)
            k = X_c.shape[1]
            mse = np.sum(resid ** 2) / (n_obs - k)
            se = np.sqrt(np.diag(XtX_inv) * mse)
            t_stats = betas / se
            sst = np.sum((Y - Y.mean()) ** 2)
            sse = np.sum(resid ** 2)
            r_sq = 1 - sse / sst if sst > 0 else 0

            alpha_ann = betas[0] * 252
            t_alpha = t_stats[0]

            ws.cell(row=row, column=1, value=ticker)
            ws.cell(row=row, column=2, value=alpha_ann).number_format = FMT_PCT
            ws.cell(row=row, column=3, value=round(t_alpha, 2)).number_format = FMT_NUM2
            ws.cell(row=row, column=4, value=round(r_sq, 4)).number_format = FMT_NUM4
            for j in range(6):
                ws.cell(row=row, column=5 + j, value=round(betas[1 + j], 4)).number_format = FMT_NUM4

            factor_results[ticker] = {"alpha": alpha_ann, "t_alpha": t_alpha, "r_sq": r_sq, "betas": betas[1:]}
        except Exception:
            ws.cell(row=row, column=1, value=ticker)
            ws.cell(row=row, column=2, value="Failed")

        row += 1

    # ── Factor Exposure Heatmap (as table with conditional formatting) ───
    row += 2
    ws.cell(row=row, column=1, value="FACTOR EXPOSURE MATRIX").font = FONT_SUBTITLE
    row += 1
    factor_names = ["Mkt", "Oil", "SMB", "HML", "Gas", "Freight"]
    fe_headers = ["Security"] + factor_names
    for j, h in enumerate(fe_headers):
        ws.cell(row=row, column=j + 1, value=h).font = FONT_HEADER
        ws.cell(row=row, column=j + 1).fill = FILL_HEADER
    row += 1
    fe_start = row

    for ticker in EQUITY_TICKERS:
        ws.cell(row=row, column=1, value=ticker)
        if ticker in factor_results:
            for j, b in enumerate(factor_results[ticker]["betas"]):
                ws.cell(row=row, column=j + 2, value=round(b, 3)).number_format = FMT_NUM3
        row += 1

    # Add color scale to factor exposure
    if row > fe_start:
        add_correlation_coloring(ws, fe_start, row - 1, 2, 7)

    # ── R² Comparison: Multi-Factor vs Single-Factor (Oil Only) ─────────
    row += 2
    ws.cell(row=row, column=1, value="R² COMPARISON: MULTI-FACTOR vs SINGLE-FACTOR (OIL ONLY)").font = FONT_SUBTITLE
    row += 1
    comp_headers = ["Security", "Multi-Factor R²", "Oil-Only R²", "Improvement", "Factors Add Value?"]
    for j, h in enumerate(comp_headers):
        ws.cell(row=row, column=j + 1, value=h).font = FONT_HEADER
        ws.cell(row=row, column=j + 1).fill = FILL_HEADER
    row += 1

    # Collect multi-factor R² from factor_results (stored during the regression loop above)
    stored_r2 = {t: factor_results[t]["r_sq"] for t in factor_results}

    for ticker in EQUITY_TICKERS:
        if ticker in log_ret.columns and "WTI" in log_ret.columns:
            y = log_ret[ticker]
            x_oil = log_ret["WTI"]
            common = pd.DataFrame({"y": y, "x": x_oil}).dropna()
            if len(common) > 30:
                X = np.column_stack([np.ones(len(common)), common["x"].values])
                beta_oil, res_oil, _, _ = np.linalg.lstsq(X, common["y"].values, rcond=None)
                sse_oil = float(np.sum((common["y"].values - X @ beta_oil) ** 2))
                sst_oil = float(np.sum((common["y"].values - common["y"].values.mean()) ** 2))
                r2_oil = float(1 - sse_oil / sst_oil) if sst_oil > 0 else 0.0

                r2_multi = stored_r2.get(ticker, 0.0)
                improvement = r2_multi - r2_oil
                adds_value = "Yes" if improvement > 0.01 else "Marginal" if improvement > 0 else "No"

                ws.cell(row=row, column=1, value=ticker)
                ws.cell(row=row, column=2, value=round(r2_multi, 4)).number_format = FMT_NUM4
                ws.cell(row=row, column=3, value=round(r2_oil, 4)).number_format = FMT_NUM4
                ws.cell(row=row, column=4, value=round(improvement, 4)).number_format = FMT_NUM4
                c = ws.cell(row=row, column=5, value=adds_value)
                c.fill = FILL_LIGHT_GREEN if adds_value == "Yes" else FILL_INPUT if adds_value == "Marginal" else FILL_LIGHT_RED
                row += 1

    results["factor_results"] = factor_results
    auto_width(ws)
    return results


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 19 — BACKTESTING & MODEL VALIDATION
# ═══════════════════════════════════════════════════════════════════════════════
def build_tab_19(wb, data, results):
    ws = wb.create_sheet(title=TAB_NAMES[19])
    set_tab_color(ws, TAB_COLORS["purple"])

    log_ret = data["log_returns"]
    diffs = data["diffs"]
    master = data["master"]

    ws["A1"] = "BACKTESTING & MODEL VALIDATION"
    ws["A1"].font = FONT_TITLE

    row = add_definition(ws, 2, 1, "Out-of-Sample Backtesting",
        "Train on 2019-2021, validate on 2022-2023 (Russia-Ukraine), test on 2024-present (Iran). "
        "RMSE degradation ratio (Val/Train) > 2.0 flags overfitting. "
        "VaR backtest: count actual breaches vs expected 5% breach rate.",
        "Degradation < 2.0 = stable model. VaR breach ratio 0.8-1.5 = well-calibrated")
    row += 1

    # Define periods
    train_end = "2021-12-31"
    val_start = "2022-01-01"
    val_end = "2023-12-31"
    test_start = "2024-01-01"

    ws.cell(row=row, column=1, value="OUT-OF-SAMPLE BACKTEST DESIGN").font = FONT_SUBTITLE
    row += 1
    ws.cell(row=row, column=1, value=f"Training: 2019-01-01 to {train_end}")
    row += 1
    ws.cell(row=row, column=1, value=f"Validation: {val_start} to {val_end}")
    row += 1
    ws.cell(row=row, column=1, value=f"Test: {test_start} to present")
    row += 2

    # Build factor matrix
    factor_names = ["R_WTI", "dVIX", "dSpread_2s10s", "dDXY_log", "dT10YIE", "dOVX"]
    factors = pd.DataFrame(index=master.index)
    factor_map = {
        "R_WTI": ("log_returns", "WTI"),
        "dVIX": ("diffs", "dVIX"),
        "dSpread_2s10s": ("diffs", "dSpread_2s10s"),
        "dDXY_log": ("diffs", "dDXY_log"),
        "dT10YIE": ("diffs", "dT10YIE"),
        "dOVX": ("diffs", "dOVX"),
    }
    for fname, (src, col) in factor_map.items():
        s = data[src] if src in data else pd.DataFrame()
        if col in s.columns:
            factors[fname] = s[col]
    factors = factors.dropna()

    # ── Regression Backtest ──────────────────────────────────────────────
    ws.cell(row=row, column=1, value="REGRESSION BACKTEST — RMSE & MAE ANALYSIS").font = FONT_SUBTITLE
    row += 1

    bt_headers = [
        "Security",
        "RMSE (Train)", "RMSE (Validation)", "RMSE (Test)",
        "MAE (Train)", "MAE (Validation)", "MAE (Test)",
        "Degradation (Val/Train)",
    ]
    for j, h in enumerate(bt_headers):
        ws.cell(row=row, column=j + 1, value=h).font = FONT_HEADER
        ws.cell(row=row, column=j + 1).fill = FILL_HEADER
    row += 1

    for ticker in EQUITY_TICKERS:
        y = log_ret.get(ticker, pd.Series(dtype=float))
        common = factors.index.intersection(y.dropna().index)
        if len(common) < 30:
            ws.cell(row=row, column=1, value=ticker)
            row += 1
            continue

        # Split into periods
        train_mask = common <= train_end
        val_mask = (common >= val_start) & (common <= val_end)
        test_mask = common >= test_start

        train_idx = common[train_mask]
        val_idx = common[val_mask]
        test_idx = common[test_mask]

        if len(train_idx) < 20:
            ws.cell(row=row, column=1, value=ticker)
            row += 1
            continue

        # Fit on training data
        Y_train = y[train_idx].values
        X_train = factors.loc[train_idx].values
        X_train_c = np.column_stack([np.ones(len(Y_train)), X_train])

        try:
            betas = np.linalg.lstsq(X_train_c, Y_train, rcond=None)[0]

            train_errors = Y_train - X_train_c @ betas
            rmse_train = float(np.sqrt(np.mean(train_errors ** 2)))
            mae_train = float(np.mean(np.abs(train_errors)))

            rmse_val = np.nan
            mae_val = np.nan
            if len(val_idx) > 5:
                Y_val = y[val_idx].values
                X_val_c = np.column_stack([np.ones(len(Y_val)), factors.loc[val_idx].values])
                val_errors = Y_val - X_val_c @ betas
                rmse_val = float(np.sqrt(np.mean(val_errors ** 2)))
                mae_val = float(np.mean(np.abs(val_errors)))

            rmse_test = np.nan
            mae_test = np.nan
            if len(test_idx) > 5:
                Y_test = y[test_idx].values
                X_test_c = np.column_stack([np.ones(len(Y_test)), factors.loc[test_idx].values])
                test_errors = Y_test - X_test_c @ betas
                rmse_test = float(np.sqrt(np.mean(test_errors ** 2)))
                mae_test = float(np.mean(np.abs(test_errors)))

            degradation = rmse_val / rmse_train if rmse_train > 0 and not np.isnan(rmse_val) else np.nan

            ws.cell(row=row, column=1, value=ticker)
            ws.cell(row=row, column=2, value=rmse_train).number_format = '0.0000'

            c_val = ws.cell(row=row, column=3, value=rmse_val if not np.isnan(rmse_val) else "N/A")
            if not np.isnan(rmse_val):
                c_val.number_format = '0.0000'
            c_test = ws.cell(row=row, column=4, value=rmse_test if not np.isnan(rmse_test) else "N/A")
            if not np.isnan(rmse_test):
                c_test.number_format = '0.0000'

            # MAE columns
            ws.cell(row=row, column=5, value=mae_train).number_format = '0.0000'
            c_mae_val = ws.cell(row=row, column=6, value=mae_val if not np.isnan(mae_val) else "N/A")
            if not np.isnan(mae_val):
                c_mae_val.number_format = '0.0000'
            c_mae_test = ws.cell(row=row, column=7, value=mae_test if not np.isnan(mae_test) else "N/A")
            if not np.isnan(mae_test):
                c_mae_test.number_format = '0.0000'

            c = ws.cell(row=row, column=8, value=round(degradation, 2) if not np.isnan(degradation) else "N/A")
            if not np.isnan(degradation):
                c.number_format = FMT_NUM2
                c.fill = FILL_LIGHT_RED if degradation > 2.0 else FILL_LIGHT_GREEN

        except Exception:
            ws.cell(row=row, column=1, value=ticker)
            ws.cell(row=row, column=2, value="Failed")

        row += 1

    # ── Portfolio Backtest ───────────────────────────────────────────────
    row += 2
    ws.cell(row=row, column=1, value="PORTFOLIO BACKTEST (Validation Period)").font = FONT_SUBTITLE
    row += 1

    portfolios = results.get("portfolios", {})
    port_tickers = results.get("port_tickers", ALL_TICKERS)

    pb_headers = ["Portfolio", "Cumulative Return", "Ann Volatility", "Sharpe Ratio", "Max Drawdown"]
    for j, h in enumerate(pb_headers):
        ws.cell(row=row, column=j + 1, value=h).font = FONT_HEADER
        ws.cell(row=row, column=j + 1).fill = FILL_HEADER
    row += 1

    for pname, pdata in portfolios.items():
        w = pdata["weights"]
        # FIX: Don't fillna(0) — it treats pre-IPO missing data as 0% returns
        # Instead, only compute portfolio returns where ALL constituents have data
        port_ret_df = pd.DataFrame()
        for i, t in enumerate(port_tickers):
            if t in log_ret.columns:
                port_ret_df[t] = log_ret[t] * w[i]
        port_rets = port_ret_df.dropna().sum(axis=1)

        val_rets = port_rets[(port_rets.index >= val_start) & (port_rets.index <= val_end)].dropna()
        if len(val_rets) < 10:
            continue

        cum_ret = float(np.exp(val_rets.sum()) - 1)
        ann_vol = float(val_rets.std() * np.sqrt(252))
        ann_ret = float(val_rets.mean() * 252)
        sharpe = (ann_ret - RF_RATE) / ann_vol if ann_vol > 0 else 0

        cum = np.exp(val_rets.cumsum())
        max_dd = float(((cum - cum.cummax()) / cum.cummax()).min())

        ws.cell(row=row, column=1, value=pname)
        ws.cell(row=row, column=2, value=cum_ret).number_format = FMT_PCT
        ws.cell(row=row, column=3, value=ann_vol).number_format = FMT_PCT
        ws.cell(row=row, column=4, value=sharpe).number_format = FMT_NUM2
        ws.cell(row=row, column=5, value=max_dd).number_format = FMT_PCT
        row += 1

    # ── VaR Backtest ────────────────────────────────────────────────────
    row += 2
    ws.cell(row=row, column=1, value="VaR BACKTEST (VALIDATION PERIOD)").font = FONT_SUBTITLE
    row += 1

    var_results = results.get("var_results", {})
    vb_headers = ["Security", "Expected 95% Breaches", "Actual Breaches", "Breach Ratio"]
    for j, h in enumerate(vb_headers):
        ws.cell(row=row, column=j + 1, value=h).font = FONT_HEADER
        ws.cell(row=row, column=j + 1).fill = FILL_HEADER
    row += 1

    for ticker in ALL_TICKERS:
        rets = log_ret.get(ticker, pd.Series(dtype=float))
        val_rets = rets[(rets.index >= val_start) & (rets.index <= val_end)].dropna()
        # FIX #4: Compute VaR using only training-period data (avoid look-ahead bias)
        train_rets = rets[rets.index <= train_end].dropna()
        if len(train_rets) < 30 or len(val_rets) < 10:
            continue

        n = len(val_rets)
        expected = n * 0.05
        # Parametric VaR from training period only
        train_mean = float(train_rets.mean())
        train_std = float(train_rets.std())
        var_95 = -train_mean + 1.645 * train_std
        actual = int(np.sum(val_rets < -var_95))
        ratio = actual / expected if expected > 0 else 0

        ws.cell(row=row, column=1, value=ticker)
        ws.cell(row=row, column=2, value=round(expected, 1))
        ws.cell(row=row, column=3, value=actual)
        c = ws.cell(row=row, column=4, value=round(ratio, 2))
        c.number_format = FMT_NUM2
        c.fill = FILL_LIGHT_RED if ratio > 2.0 else FILL_LIGHT_GREEN
        row += 1

    auto_width(ws)
    return results


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 20 — EXECUTIVE DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
def build_tab_20(wb, data, results):
    ws = wb.create_sheet(title=TAB_NAMES[20])
    set_tab_color(ws, TAB_COLORS["purple"])

    master = data["master"]
    log_ret = data["log_returns"]

    ws["A1"] = "EXECUTIVE DASHBOARD [CROSS-SHEET REFERENCES → ALL TABS]"
    ws["A1"].font = FONT_TITLE
    ws["A2"] = f"Last Updated: {master.index[-1].date() if len(master) > 0 else 'N/A'}"

    tab1_name = results.get("tab1_name", TAB_NAMES[1])
    price_col_map = results.get("tab1_price_col_map", {})
    macro_col_map = results.get("tab1_macro_col_map", {})
    t1_end = results.get("tab1_last_data_row", 1000)

    # ── Top Strip: Current Prices (linked to Tab 1) ──────────────────────
    row = 4
    ws.cell(row=row, column=1, value="CURRENT PRICES & KEY METRICS [→ Tab 1]").font = FONT_SUBTITLE
    row += 1
    macro_display_cols = ["WTI", "Brent", "VIX", "OVX", "Gold", "2s10s"]
    price_headers = ["Metric"] + ALL_TICKERS + macro_display_cols
    for j, h in enumerate(price_headers):
        ws.cell(row=row, column=j + 1, value=h).font = FONT_HEADER
        ws.cell(row=row, column=j + 1).fill = FILL_HEADER
    row += 1

    # Last price — CROSS-SHEET FORMULAS to Tab 1
    ws.cell(row=row, column=1, value="Last Price")
    for j, ticker in enumerate(ALL_TICKERS):
        if ticker in price_col_map:
            pcl = price_col_map[ticker]
            c = ws.cell(row=row, column=j + 2,
                        value=f"='{tab1_name}'!{pcl}{t1_end}")
            c.number_format = FMT_MONEY
            c.font = FONT_LINKED
        elif ticker in master.columns:
            prices = master[ticker].dropna()
            if len(prices) > 0:
                ws.cell(row=row, column=j + 2, value=round(float(prices.iloc[-1]), 2)).number_format = FMT_MONEY
    # Macro prices — cross-sheet refs where available
    macro_tickers = ["WTI", "Brent", "VIX", "OVX", "Gold"]
    for j, col in enumerate(macro_tickers):
        mcol = len(ALL_TICKERS) + 2 + j
        if col in price_col_map:
            pcl = price_col_map[col]
            c = ws.cell(row=row, column=mcol,
                        value=f"='{tab1_name}'!{pcl}{t1_end}")
            c.number_format = FMT_NUM2
            c.font = FONT_LINKED
        elif col in macro_col_map:
            mcl = macro_col_map[col]
            c = ws.cell(row=row, column=mcol,
                        value=f"='{tab1_name}'!{mcl}{t1_end}")
            c.number_format = FMT_NUM2
            c.font = FONT_LINKED
        elif col in master.columns:
            s = master[col].dropna()
            if len(s) > 0:
                ws.cell(row=row, column=mcol, value=round(float(s.iloc[-1]), 2)).number_format = FMT_NUM2
    # 2s10s spread — cross-sheet ref
    col_2s10s = len(ALL_TICKERS) + 2 + len(macro_tickers)
    if "Spread_2s10s" in macro_col_map:
        s2s10_cl = macro_col_map["Spread_2s10s"]
        c = ws.cell(row=row, column=col_2s10s,
                    value=f"='{tab1_name}'!{s2s10_cl}{t1_end}")
        c.number_format = FMT_NUM2
        c.font = FONT_LINKED
    else:
        s2s10 = master.get("Spread_2s10s", pd.Series(dtype=float))
        if len(s2s10.dropna()) > 0:
            ws.cell(row=row, column=col_2s10s, value=round(float(s2s10.dropna().iloc[-1]), 2)).number_format = FMT_NUM2
    row += 1

    # 1-day return
    ws.cell(row=row, column=1, value="1-Day Return")
    for j, ticker in enumerate(ALL_TICKERS):
        rets = log_ret.get(ticker, pd.Series(dtype=float)).dropna()
        if len(rets) > 0:
            val = float(rets.iloc[-1])
            c = ws.cell(row=row, column=j + 2, value=val)
            c.number_format = FMT_PCT
            c.fill = FILL_LIGHT_GREEN if val > 0 else FILL_LIGHT_RED
    row += 1

    # YTD return
    ws.cell(row=row, column=1, value="YTD Return")
    ytd_start = f"{master.index[-1].year}-01-01" if len(master) > 0 else "2026-01-01"
    for j, ticker in enumerate(ALL_TICKERS):
        rets = log_ret.get(ticker, pd.Series(dtype=float))
        ytd_rets = rets[rets.index >= ytd_start].dropna()
        if len(ytd_rets) > 0:
            val = float(np.exp(ytd_rets.sum()) - 1)
            c = ws.cell(row=row, column=j + 2, value=val)
            c.number_format = FMT_PCT
            c.fill = FILL_LIGHT_GREEN if val > 0 else FILL_LIGHT_RED
    row += 2

    # ── Current Regime ───────────────────────────────────────────────────
    regime = results.get("regime", pd.Series(dtype=float))
    if len(regime) > 0:
        current_regime = int(regime.iloc[-1])
        ws.cell(row=row, column=1, value="Current Macro Regime").font = FONT_SUBTITLE
        c = ws.cell(row=row, column=2, value=REGIME_NAMES.get(current_regime, "Unknown"))
        c.font = FONT_TITLE
        if current_regime == 1:
            c.fill = FILL_LIGHT_GREEN
        elif current_regime == 3:
            c.fill = FILL_LIGHT_RED
        elif current_regime == 2:
            c.fill = FILL_INPUT
        row += 2

    # ── Oil Beta Ranking ─────────────────────────────────────────────────
    ws.cell(row=row, column=1, value="OIL BETA RANKING").font = FONT_SUBTITLE
    row += 1
    reg_results = results.get("reg_results", {})
    betas_sorted = sorted(reg_results.items(), key=lambda x: abs(x[1].get("oil_beta", 0)), reverse=True)

    ob_headers = ["Rank", "Ticker", "Oil Beta", "R²"]
    for j, h in enumerate(ob_headers):
        ws.cell(row=row, column=j + 1, value=h).font = FONT_HEADER
        ws.cell(row=row, column=j + 1).fill = FILL_HEADER
    row += 1
    ob_start = row

    for rank, (ticker, rr) in enumerate(betas_sorted, 1):
        ws.cell(row=row, column=1, value=rank)
        ws.cell(row=row, column=2, value=ticker)
        ws.cell(row=row, column=3, value=round(rr["oil_beta"], 4)).number_format = FMT_NUM4
        ws.cell(row=row, column=4, value=round(rr["r_squared"], 4)).number_format = FMT_NUM4
        row += 1

    # Oil beta chart
    if betas_sorted:
        chart = BarChart()
        chart.type = "col"
        chart.title = "Oil Beta by Security"
        chart.y_axis.title = "β₁"
        chart.width = 18
        chart.height = 10
        data_ref = Reference(ws, min_col=3, min_row=ob_start - 1, max_row=ob_start + len(betas_sorted) - 1)
        cats = Reference(ws, min_col=2, min_row=ob_start, max_row=ob_start + len(betas_sorted) - 1)
        chart.add_data(data_ref, titles_from_data=True)
        chart.set_categories(cats)
        ws.add_chart(chart, "F" + str(ob_start - 1))

    row += 2

    # ── Portfolio Summary ────────────────────────────────────────────────
    portfolios = results.get("portfolios", {})
    if portfolios:
        ws.cell(row=row, column=1, value="PORTFOLIO SUMMARY").font = FONT_SUBTITLE
        row += 1
        ps_headers = ["Portfolio", "Ann Return", "Ann Volatility", "Sharpe"]
        for j, h in enumerate(ps_headers):
            ws.cell(row=row, column=j + 1, value=h).font = FONT_HEADER
            ws.cell(row=row, column=j + 1).fill = FILL_HEADER
        row += 1

        for pname, pdata in portfolios.items():
            ws.cell(row=row, column=1, value=pname)
            ws.cell(row=row, column=2, value=pdata["return"]).number_format = FMT_PCT
            ws.cell(row=row, column=3, value=pdata["vol"]).number_format = FMT_PCT
            ws.cell(row=row, column=4, value=pdata["sharpe"]).number_format = FMT_NUM2
            row += 1
        row += 1

    # ── Scenario Recommendations ─────────────────────────────────────────
    scenario_returns = results.get("scenario_returns", {})
    if scenario_returns:
        ws.cell(row=row, column=1, value="INVESTMENT RECOMMENDATIONS").font = FONT_SUBTITLE
        row += 1
        rec_headers = ["Security", "Weighted Expected Return", "Recommendation"]
        for j, h in enumerate(rec_headers):
            ws.cell(row=row, column=j + 1, value=h).font = FONT_HEADER
            ws.cell(row=row, column=j + 1).fill = FILL_HEADER
        row += 1

        sorted_recs = sorted(scenario_returns.items(), key=lambda x: x[1].get("weighted", 0), reverse=True)
        for ticker, sr in sorted_recs:
            ws.cell(row=row, column=1, value=ticker)
            ws.cell(row=row, column=2, value=sr.get("weighted", 0)).number_format = FMT_PCT
            rec = sr.get("recommendation", "HOLD")
            c = ws.cell(row=row, column=3, value=rec)
            c.fill = FILL_LIGHT_GREEN if rec == "BUY" else FILL_LIGHT_RED if rec == "SELL" else FILL_INPUT
            row += 1
        row += 1

    # ── Pair Trade Z-Scores ──────────────────────────────────────────────
    pair_summary = results.get("pair_summary", [])
    if pair_summary:
        ws.cell(row=row, column=1, value="PAIR TRADE SIGNALS").font = FONT_SUBTITLE
        row += 1
        pt_headers = ["Pair", "Z-Score", "Half-Life (days)", "Signal"]
        for j, h in enumerate(pt_headers):
            ws.cell(row=row, column=j + 1, value=h).font = FONT_HEADER
            ws.cell(row=row, column=j + 1).fill = FILL_HEADER
        row += 1

        for ps in pair_summary:
            ws.cell(row=row, column=1, value=ps["pair"])
            z = ps["z_score"]
            ws.cell(row=row, column=2, value=round(z, 2) if not np.isnan(z) else "N/A").number_format = FMT_NUM2
            hl = ps["half_life"]
            ws.cell(row=row, column=3, value=round(hl, 1) if not np.isnan(hl) else "N/A")
            signal = "SHORT A/LONG B" if z > 2 else "LONG A/SHORT B" if z < -2 else "NEUTRAL"
            c = ws.cell(row=row, column=4, value=signal)
            c.fill = FILL_LIGHT_GREEN if signal != "NEUTRAL" else FILL_INPUT
            row += 1

    # ── Correlation Heatmap (summary) ────────────────────────────────────
    row += 2
    corr_matrix = results.get("corr_matrix")
    if corr_matrix is not None:
        ws.cell(row=row, column=1, value="CORRELATION MATRIX (SUMMARY)").font = FONT_SUBTITLE
        row += 1
        corr_tickers = [t for t in ALL_TICKERS if t in corr_matrix.index]
        for j, t in enumerate(corr_tickers):
            ws.cell(row=row, column=j + 2, value=t).font = FONT_HEADER
        row += 1
        cm_start = row
        for i, ti in enumerate(corr_tickers):
            ws.cell(row=row + i, column=1, value=ti).font = FONT_HEADER
            for j, tj in enumerate(corr_tickers):
                val = corr_matrix.loc[ti, tj]
                if pd.notna(val):
                    ws.cell(row=row + i, column=j + 2, value=round(float(val), 2)).number_format = FMT_NUM2
        add_correlation_coloring(ws, cm_start, cm_start + len(corr_tickers) - 1, 2, 1 + len(corr_tickers))

    auto_width(ws)
    return results
