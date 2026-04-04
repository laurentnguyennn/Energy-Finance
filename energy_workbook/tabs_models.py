"""
Tabs 6–10: Multi-Factor Regression, Volatility Modeling (GARCH),
Portfolio Construction, Fundamental Valuation (DCF), Value at Risk.

Enhanced: Excel formula-based calculations with cross-sheet references.
Each tab stores cell positions so downstream tabs can reference them.
"""
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import norm, t as t_dist
from openpyxl.chart import BarChart, ScatterChart, LineChart, Reference
from openpyxl.utils import get_column_letter

from .config import (
    ALL_TICKERS, EQUITY_TICKERS, FUNDAMENTALS, RF_RATE, PORTFOLIO_VALUE,
    MAX_WEIGHT, MIN_BIL_WEIGHT, EQUITY_RISK_PREMIUM, TERMINAL_GROWTH,
    EWMA_LAMBDA, TAB_NAMES, TAB_COLORS, REGIME_NAMES,
    DCF_STOCKS, DCF_PARAMS, OIL_PRICE_PATH, OIL_TERMINAL, BOND_ISSUERS,
)
from .styles import (
    FONT_HEADER, FONT_TITLE, FONT_SUBTITLE, FONT_NORMAL, FONT_INPUT,
    FONT_LINKED,
    FILL_HEADER, FILL_INPUT, FILL_LIGHT_GREEN, FILL_LIGHT_RED,
    FILL_LIGHT_BLUE,
    THIN_BORDER, BOTTOM_BORDER, ALIGN_CENTER,
    FMT_PCT, FMT_NUM2, FMT_NUM3, FMT_NUM4, FMT_DATE, FMT_MONEY, FMT_INT,
    style_header_row, write_table, auto_width, set_tab_color,
)
from .formulas import (
    sheet_ref, sheet_range, f_ewma_init, f_ewma_step, f_ewma_annualized_vol,
    f_parametric_var, f_historical_var, f_cvar, f_cornish_fisher_z,
    f_sharpe, add_definition,
)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 6 — MULTI-FACTOR REGRESSION ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════
def build_tab_06(wb, data, results):
    ws = wb.create_sheet(title=TAB_NAMES[6])
    set_tab_color(ws, TAB_COLORS["blue"])

    log_ret = data["log_returns"]
    diffs = data["diffs"]
    master = data["master"]
    regime = results.get("regime", pd.Series(0, index=master.index))

    ws["A1"] = "MULTI-FACTOR REGRESSION ANALYSIS"
    ws["A1"].font = FONT_TITLE

    # Build factor matrix
    factor_names = ["R_WTI", "dVIX", "dSpread_2s10s", "dDXY_log", "dT10YIE", "dOVX"]
    factor_sources = {
        "R_WTI": ("log_returns", "WTI"),
        "dVIX": ("diffs", "dVIX"),
        "dSpread_2s10s": ("diffs", "dSpread_2s10s"),
        "dDXY_log": ("diffs", "dDXY_log"),
        "dT10YIE": ("diffs", "dT10YIE"),
        "dOVX": ("diffs", "dOVX"),
    }

    factors = pd.DataFrame(index=master.index)
    for fname, (source, col) in factor_sources.items():
        src = data[source] if source in data else pd.DataFrame()
        if col in src.columns:
            factors[fname] = src[col]

    factors = factors.dropna()

    # Run regression for each equity
    row = 3
    reg_results = {}

    for ticker in EQUITY_TICKERS:
        ws.cell(row=row, column=1, value=f"REGRESSION: {ticker}").font = FONT_SUBTITLE
        row += 1

        y = log_ret.get(ticker, pd.Series(dtype=float))
        common_idx = factors.index.intersection(y.dropna().index)
        if len(common_idx) < 30:
            ws.cell(row=row, column=1, value="Insufficient data for regression")
            row += 3
            continue

        Y = y[common_idx].values
        X = factors.loc[common_idx].values
        X_with_const = np.column_stack([np.ones(len(Y)), X])

        try:
            # OLS: beta = (X'X)^-1 X'y
            XtX_inv = np.linalg.inv(X_with_const.T @ X_with_const)
            betas = XtX_inv @ X_with_const.T @ Y

            # Residuals and statistics
            predicted = X_with_const @ betas
            residuals = Y - predicted
            n_obs = len(Y)
            k = X_with_const.shape[1]
            df = n_obs - k
            sse = np.sum(residuals ** 2)
            sst = np.sum((Y - Y.mean()) ** 2)
            r_squared = 1 - sse / sst if sst > 0 else 0
            adj_r_sq = 1 - (1 - r_squared) * (n_obs - 1) / df if df > 0 else 0

            mse = sse / df if df > 0 else 0
            se_betas = np.sqrt(np.diag(XtX_inv) * mse)
            t_stats = betas / se_betas

            # p-values (two-tailed)
            p_values = 2 * (1 - t_dist.cdf(np.abs(t_stats), df))

            # F-statistic
            ssr = sst - sse
            f_stat = (ssr / (k - 1)) / mse if mse > 0 and k > 1 else 0

            # Durbin-Watson approximation
            dw = 2 * (1 - np.corrcoef(residuals[1:], residuals[:-1])[0, 1]) if len(residuals) > 1 else 2.0

            # Write results
            reg_headers = ["Factor", "Coefficient", "Std Error", "t-Statistic", "p-Value", "Significance"]
            for j, h in enumerate(reg_headers):
                ws.cell(row=row, column=j + 1, value=h).font = FONT_HEADER
                ws.cell(row=row, column=j + 1).fill = FILL_HEADER
            row += 1

            beta_names = ["Intercept (α)"] + factor_names
            for i, name in enumerate(beta_names):
                ws.cell(row=row, column=1, value=name)
                ws.cell(row=row, column=2, value=round(betas[i], 6)).number_format = '0.000000'
                ws.cell(row=row, column=3, value=round(se_betas[i], 6)).number_format = '0.000000'
                ws.cell(row=row, column=4, value=round(t_stats[i], 3)).number_format = FMT_NUM3
                ws.cell(row=row, column=5, value=round(p_values[i], 4)).number_format = FMT_NUM4
                sig = "***" if p_values[i] < 0.001 else "**" if p_values[i] < 0.01 else "*" if p_values[i] < 0.05 else ""
                ws.cell(row=row, column=6, value=sig)
                row += 1

            # Summary stats
            ws.cell(row=row, column=1, value="R²")
            ws.cell(row=row, column=2, value=round(r_squared, 4)).number_format = FMT_NUM4
            row += 1
            ws.cell(row=row, column=1, value="Adjusted R²")
            ws.cell(row=row, column=2, value=round(adj_r_sq, 4)).number_format = FMT_NUM4
            row += 1
            ws.cell(row=row, column=1, value="F-Statistic")
            ws.cell(row=row, column=2, value=round(f_stat, 2)).number_format = FMT_NUM2
            row += 1
            ws.cell(row=row, column=1, value="Durbin-Watson")
            ws.cell(row=row, column=2, value=round(dw, 3)).number_format = FMT_NUM3
            row += 1
            ws.cell(row=row, column=1, value="N observations")
            ws.cell(row=row, column=2, value=n_obs)
            row += 2

            # FIX #1: Also compute market beta (vs SPY) for CAPM usage in DCF
            spy_ret = log_ret.get("SPY", pd.Series(dtype=float))
            spy_common = spy_ret.dropna().index.intersection(y.dropna().index)
            if len(spy_common) > 30:
                cov_stock_mkt = np.cov(y[spy_common].values, spy_ret[spy_common].values)[0, 1]
                var_mkt = np.var(spy_ret[spy_common].values, ddof=1)
                market_beta_val = cov_stock_mkt / var_mkt if var_mkt > 0 else 1.0
            else:
                market_beta_val = 1.0

            reg_results[ticker] = {
                "betas": betas,
                "r_squared": r_squared,
                "oil_beta": betas[1],  # WTI beta
                "market_beta": market_beta_val,  # CAPM beta vs SPY
                "residuals": residuals,
            }

        except Exception as e:
            ws.cell(row=row, column=1, value=f"Regression failed: {str(e)}")
            row += 3

    # ── Fix 1 & 2: Regime-Conditional Regressions ───────────────────────
    row += 2
    ws.cell(row=row, column=1, value="REGIME-CONDITIONAL REGRESSIONS").font = FONT_SUBTITLE
    row += 1

    regime_oil_betas = {}  # {reg_id: {ticker: beta1}}
    regime_r2 = {}         # {reg_id: {ticker: r2}}

    regime_names_local = {1: "Risk-On Growth", 2: "Inflation Shock", 3: "Geopolitical Crisis", 4: "Recession/Risk-Off"}

    for reg_id, reg_name in regime_names_local.items():
        reg_mask = (regime == reg_id)
        # Align mask with factors index
        aligned_mask = reg_mask.reindex(factors.index, fill_value=False)
        n_days = int(aligned_mask.sum())

        ws.cell(row=row, column=1, value=f"Regime {reg_id}: {reg_name} (N={n_days})").font = FONT_HEADER
        row += 1

        if n_days < 30:
            ws.cell(row=row, column=1, value="Insufficient data for regression (need ≥30 obs)")
            row += 2
            regime_oil_betas[reg_id] = {}
            regime_r2[reg_id] = {}
            continue

        reg_headers = ["Ticker", "α", "β₁(WTI)", "β₂(VIX)", "β₃(2s10s)", "β₄(DXY)", "β₅(Break)", "β₆(OVX)", "R²", "N"]
        for j, h in enumerate(reg_headers):
            ws.cell(row=row, column=j + 1, value=h).font = FONT_HEADER
            ws.cell(row=row, column=j + 1).fill = FILL_HEADER
        row += 1

        regime_oil_betas[reg_id] = {}
        regime_r2[reg_id] = {}

        for ticker in EQUITY_TICKERS:
            y = log_ret.get(ticker, pd.Series(dtype=float))
            common_idx = factors.index.intersection(y.dropna().index)
            reg_idx = common_idx[aligned_mask.reindex(common_idx, fill_value=False)]

            ws.cell(row=row, column=1, value=ticker)

            if len(reg_idx) < 20:
                ws.cell(row=row, column=2, value="N/A (insufficient data)")
                row += 1
                continue

            Y_reg = y[reg_idx].values
            X_reg = factors.loc[reg_idx].values
            X_reg_c = np.column_stack([np.ones(len(Y_reg)), X_reg])

            try:
                betas_reg, _, _, _ = np.linalg.lstsq(X_reg_c, Y_reg, rcond=None)
                pred_reg = X_reg_c @ betas_reg
                res_reg = Y_reg - pred_reg
                sst_reg = np.sum((Y_reg - Y_reg.mean()) ** 2)
                sse_reg = np.sum(res_reg ** 2)
                r2_reg = 1 - sse_reg / sst_reg if sst_reg > 0 else 0

                ws.cell(row=row, column=2, value=round(betas_reg[0], 6)).number_format = '0.000000'
                ws.cell(row=row, column=3, value=round(betas_reg[1], 4)).number_format = FMT_NUM4
                ws.cell(row=row, column=4, value=round(betas_reg[2], 4)).number_format = FMT_NUM4
                ws.cell(row=row, column=5, value=round(betas_reg[3], 4)).number_format = FMT_NUM4
                ws.cell(row=row, column=6, value=round(betas_reg[4], 4)).number_format = FMT_NUM4
                ws.cell(row=row, column=7, value=round(betas_reg[5], 4)).number_format = FMT_NUM4
                ws.cell(row=row, column=8, value=round(betas_reg[6], 4)).number_format = FMT_NUM4
                ws.cell(row=row, column=9, value=round(r2_reg, 4)).number_format = FMT_NUM4
                ws.cell(row=row, column=10, value=len(reg_idx))

                regime_oil_betas[reg_id][ticker] = betas_reg[1]
                regime_r2[reg_id][ticker] = r2_reg

            except Exception as e:
                ws.cell(row=row, column=2, value=f"Failed: {str(e)}")

            row += 1

        row += 1  # blank separator between regimes

    results["regime_oil_betas"] = regime_oil_betas
    results["reg_results"] = reg_results

    # ── Fix 2: Oil Beta Summary Table with regime columns ───────────────
    row += 1
    ws.cell(row=row, column=1, value="OIL BETA SUMMARY (FULL PERIOD + REGIME-CONDITIONAL)").font = FONT_SUBTITLE
    row += 1
    ob_headers = ["Ticker", "Full Period β₁ (WTI)", "R² (Full)",
                  "Growth β₁", "Inflation β₁", "Crisis β₁", "Recession β₁"]
    for j, h in enumerate(ob_headers):
        ws.cell(row=row, column=j + 1, value=h).font = FONT_HEADER
        ws.cell(row=row, column=j + 1).fill = FILL_HEADER
    row += 1

    oil_beta_summary_start = row  # save for chart

    for ticker in EQUITY_TICKERS:
        ws.cell(row=row, column=1, value=ticker)
        if ticker in reg_results:
            ws.cell(row=row, column=2, value=round(reg_results[ticker]["oil_beta"], 4)).number_format = FMT_NUM4
            ws.cell(row=row, column=3, value=round(reg_results[ticker]["r_squared"], 4)).number_format = FMT_NUM4
        for col_offset, reg_id in enumerate([1, 2, 3, 4], start=4):
            beta_val = regime_oil_betas.get(reg_id, {}).get(ticker)
            if beta_val is not None:
                ws.cell(row=row, column=col_offset, value=round(beta_val, 4)).number_format = FMT_NUM4
            else:
                ws.cell(row=row, column=col_offset, value="N/A")
        row += 1

    # ── Fix 3: LNG-Specific Supplementary Regression ────────────────────
    row += 2
    ws.cell(row=row, column=1, value="SUPPLEMENTARY REGRESSION — LNG/VG (Natural Gas Model)").font = FONT_SUBTITLE
    row += 1
    ws.cell(row=row, column=1, value="Model: R = α + β₁(R_WTI) + β₂(ΔTTF_HH_Spread) + β₃(ΔOVX) + β₄(ΔDXY) + ε")
    row += 1

    lng_factor_names = ["R_WTI", "dTTF_HH_Spread", "dOVX", "dDXY_log"]
    lng_factors = pd.DataFrame(index=master.index)
    lng_factor_sources = {
        "R_WTI":          ("log_returns", "WTI"),
        "dTTF_HH_Spread": ("diffs",       "dTTF_HH_Spread"),
        "dOVX":           ("diffs",       "dOVX"),
        "dDXY_log":       ("diffs",       "dDXY_log"),
    }
    for fname, (source, col) in lng_factor_sources.items():
        src = data.get(source, pd.DataFrame())
        if col in src.columns:
            lng_factors[fname] = src[col]
        else:
            lng_factors[fname] = np.nan

    lng_factors = lng_factors.dropna()

    lng_reg_headers = ["Ticker", "α", "β₁(WTI)", "β₂(TTF-HH)", "β₃(OVX)", "β₄(DXY)", "R²", "N"]
    for j, h in enumerate(lng_reg_headers):
        ws.cell(row=row, column=j + 1, value=h).font = FONT_HEADER
        ws.cell(row=row, column=j + 1).fill = FILL_HEADER
    row += 1

    for ticker in ["LNG", "VG"]:
        y = log_ret.get(ticker, pd.Series(dtype=float))
        common_idx = lng_factors.index.intersection(y.dropna().index)
        ws.cell(row=row, column=1, value=ticker)
        if len(common_idx) < 20:
            ws.cell(row=row, column=2, value="N/A (insufficient data)")
            row += 1
            continue
        Y_lng = y[common_idx].values
        X_lng = lng_factors.loc[common_idx].values
        X_lng_c = np.column_stack([np.ones(len(Y_lng)), X_lng])
        try:
            betas_lng, _, _, _ = np.linalg.lstsq(X_lng_c, Y_lng, rcond=None)
            pred_lng = X_lng_c @ betas_lng
            sst_lng = np.sum((Y_lng - Y_lng.mean()) ** 2)
            sse_lng = np.sum((Y_lng - pred_lng) ** 2)
            r2_lng = 1 - sse_lng / sst_lng if sst_lng > 0 else 0

            ws.cell(row=row, column=2, value=round(betas_lng[0], 6)).number_format = '0.000000'
            ws.cell(row=row, column=3, value=round(betas_lng[1], 4)).number_format = FMT_NUM4
            ws.cell(row=row, column=4, value=round(betas_lng[2], 4)).number_format = FMT_NUM4
            ws.cell(row=row, column=5, value=round(betas_lng[3], 4)).number_format = FMT_NUM4
            ws.cell(row=row, column=6, value=round(betas_lng[4], 4)).number_format = FMT_NUM4
            ws.cell(row=row, column=7, value=round(r2_lng, 4)).number_format = FMT_NUM4
            ws.cell(row=row, column=8, value=len(common_idx))
        except Exception as e:
            ws.cell(row=row, column=2, value=f"Failed: {str(e)}")
        row += 1

    ws.cell(row=row, column=1, value="Note: β₂(TTF-HH) is the LNG export arbitrage beta — expected to be the dominant driver for both names.")
    ws.cell(row=row, column=1).font = FONT_NORMAL
    row += 2

    # ── Fix 4: Shipping-Specific Supplementary Regression ───────────────
    ws.cell(row=row, column=1, value="SUPPLEMENTARY REGRESSION — FRO/STNG (Shipping Model)").font = FONT_SUBTITLE
    row += 1
    ws.cell(row=row, column=1, value="Model: R = α + β₁(R_WTI) + β₂(ΔBrent_WTI_Spread) + β₃(ΔOVX) + β₄(ΔVIX) + ε")
    row += 1

    ship_factor_names = ["R_WTI", "dBrent_WTI_Spread", "dOVX", "dVIX"]
    ship_factors = pd.DataFrame(index=master.index)
    ship_factor_sources = {
        "R_WTI":              ("log_returns", "WTI"),
        "dBrent_WTI_Spread":  ("diffs",       "dBrent_WTI_Spread"),
        "dOVX":               ("diffs",       "dOVX"),
        "dVIX":               ("diffs",       "dVIX"),
    }
    for fname, (source, col) in ship_factor_sources.items():
        src = data.get(source, pd.DataFrame())
        if col in src.columns:
            ship_factors[fname] = src[col]
        else:
            ship_factors[fname] = np.nan

    ship_factors = ship_factors.dropna()

    ship_reg_headers = ["Ticker", "α", "β₁(WTI)", "β₂(Brent-WTI)", "β₃(OVX)", "β₄(VIX)", "R²", "N"]
    for j, h in enumerate(ship_reg_headers):
        ws.cell(row=row, column=j + 1, value=h).font = FONT_HEADER
        ws.cell(row=row, column=j + 1).fill = FILL_HEADER
    row += 1

    for ticker in ["FRO", "STNG"]:
        y = log_ret.get(ticker, pd.Series(dtype=float))
        common_idx = ship_factors.index.intersection(y.dropna().index)
        ws.cell(row=row, column=1, value=ticker)
        if len(common_idx) < 20:
            ws.cell(row=row, column=2, value="N/A (insufficient data)")
            row += 1
            continue
        Y_ship = y[common_idx].values
        X_ship = ship_factors.loc[common_idx].values
        X_ship_c = np.column_stack([np.ones(len(Y_ship)), X_ship])
        try:
            betas_ship, _, _, _ = np.linalg.lstsq(X_ship_c, Y_ship, rcond=None)
            pred_ship = X_ship_c @ betas_ship
            sst_ship = np.sum((Y_ship - Y_ship.mean()) ** 2)
            sse_ship = np.sum((Y_ship - pred_ship) ** 2)
            r2_ship = 1 - sse_ship / sst_ship if sst_ship > 0 else 0

            ws.cell(row=row, column=2, value=round(betas_ship[0], 6)).number_format = '0.000000'
            ws.cell(row=row, column=3, value=round(betas_ship[1], 4)).number_format = FMT_NUM4
            ws.cell(row=row, column=4, value=round(betas_ship[2], 4)).number_format = FMT_NUM4
            ws.cell(row=row, column=5, value=round(betas_ship[3], 4)).number_format = FMT_NUM4
            ws.cell(row=row, column=6, value=round(betas_ship[4], 4)).number_format = FMT_NUM4
            ws.cell(row=row, column=7, value=round(r2_ship, 4)).number_format = FMT_NUM4
            ws.cell(row=row, column=8, value=len(common_idx))
        except Exception as e:
            ws.cell(row=row, column=2, value=f"Failed: {str(e)}")
        row += 1

    ws.cell(row=row, column=1, value="Note: β₁(WTI) expected ≈0 for shipping; β₂(Brent-WTI spread) captures logistics disruption premium driving tanker demand.")
    ws.cell(row=row, column=1).font = FONT_NORMAL
    row += 2

    # ── CAPM Market Beta (vs SPY) — referenced by Tab 9 DCF ───────────
    ws.cell(row=row, column=1, value="CAPM MARKET BETA (vs SPY)").font = FONT_SUBTITLE
    row += 1
    ws.cell(row=row, column=1, value="Used by Tab 9 (DCF) for cost of equity: Re = Rf + β × ERP").font = FONT_NORMAL
    row += 1
    mb_headers = ["Ticker", "Market Beta (vs SPY)"]
    for j, h in enumerate(mb_headers):
        ws.cell(row=row, column=j + 1, value=h).font = FONT_HEADER
        ws.cell(row=row, column=j + 1).fill = FILL_HEADER
    row += 1
    tab6_market_beta_positions = {}
    for ticker in EQUITY_TICKERS:
        ws.cell(row=row, column=1, value=ticker)
        beta_val = reg_results.get(ticker, {}).get("market_beta", 1.0)
        ws.cell(row=row, column=2, value=round(beta_val, 4)).number_format = FMT_NUM4
        tab6_market_beta_positions[ticker] = f"B{row}"
        row += 1
    row += 1

    # ── Definitions ────────────────────────────────────────────────────
    row = add_definition(ws, row, 1, "Oil Beta (β₁)",
        "Sensitivity of stock return to WTI crude oil return. β₁=1.0 means stock moves 1:1 with oil. "
        "COP/OXY expected >1.0 (pure E&P), FRO/STNG ≈0 (driven by freight, not oil price), ET lowest (fee-based).",
        "XOM ≈0.4-0.7, COP ≈1.0-1.5, ET ≈0.1-0.3, FRO ≈0")
    row = add_definition(ws, row, 1, "R² (Coefficient of Determination)",
        "Fraction of stock return variance explained by the 6-factor model. "
        "Higher R² means the stock is driven primarily by these macro factors; lower R² means idiosyncratic factors dominate.",
        "E&P stocks: 0.15-0.40, Shipping: 0.05-0.15, ET: 0.10-0.20")

    # ── Oil Beta Bar Chart ──────────────────────────────────────────────
    chart_start = oil_beta_summary_start
    chart = BarChart()
    chart.type = "col"
    chart.title = "Oil Beta (WTI) by Security"
    chart.y_axis.title = "Beta Coefficient"
    data_ref = Reference(ws, min_col=2, min_row=chart_start - 1, max_row=chart_start + len(EQUITY_TICKERS) - 1)
    cats = Reference(ws, min_col=1, min_row=chart_start, max_row=chart_start + len(EQUITY_TICKERS) - 1)
    chart.add_data(data_ref, titles_from_data=True)
    chart.set_categories(cats)
    chart.width = 20
    chart.height = 12
    ws.add_chart(chart, f"I{chart_start}")

    results["tab6_name"] = TAB_NAMES[6]
    results["tab6_market_beta_positions"] = tab6_market_beta_positions

    auto_width(ws)
    return results


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 7 — VOLATILITY MODELING (GARCH)
# ═══════════════════════════════════════════════════════════════════════════════
def build_tab_07(wb, data, results):
    ws = wb.create_sheet(title=TAB_NAMES[7])
    set_tab_color(ws, TAB_COLORS["blue"])

    log_ret = data["log_returns"]

    ws["A1"] = "VOLATILITY MODELING (EWMA & GJR-GARCH)"
    ws["A1"].font = FONT_TITLE

    lam = EWMA_LAMBDA
    tab1_name = results.get("tab1_name", TAB_NAMES[1])
    ret_col_map = results.get("tab1_ret_col_map", {})
    t1_start = results.get("tab1_ret_start_row", 4)
    t1_end = results.get("tab1_ret_end_row", 1000)

    # ── Definition ──────────────────────────────────────────────────────
    row = add_definition(ws, 3, 1, "EWMA Volatility (λ=0.94)",
        "σ²_t = λ·σ²_{t-1} + (1-λ)·r²_{t-1}. Each variance cell is a LIVE Excel formula "
        "referencing the previous row + Tab 1 returns. Init = VARP(first 60 returns).",
        "Annualized vol: 15-25% (ET, BIL), 30-80% (FRO, OXY)")

    # ── Tier 1: EWMA Volatility (Excel Formula Chain) ──────────────────
    ws.cell(row=row, column=1, value="TIER 1 — EWMA VOLATILITY (λ=0.94) [LIVE EXCEL FORMULAS]").font = FONT_SUBTITLE
    row += 1

    vol_cols = ALL_TICKERS + ["WTI", "Brent"]
    avail = [c for c in vol_cols if c in ret_col_map]

    # Headers: Date | Ticker1_σ² | Ticker1_AnnVol | ...
    ws.cell(row=row, column=1, value="Date").font = FONT_HEADER
    ws.cell(row=row, column=1).fill = FILL_HEADER
    col_idx = 2
    ewma_col_info = {}
    for ticker in avail:
        ws.cell(row=row, column=col_idx, value=f"{ticker}_σ²").font = FONT_HEADER
        ws.cell(row=row, column=col_idx).fill = FILL_HEADER
        ws.cell(row=row, column=col_idx + 1, value=f"{ticker}_AnnVol").font = FONT_HEADER
        ws.cell(row=row, column=col_idx + 1).fill = FILL_HEADER
        ewma_col_info[ticker] = (col_idx, col_idx + 1,
                                 get_column_letter(col_idx), get_column_letter(col_idx + 1))
        col_idx += 2
    header_row = row
    row += 1
    ewma_data_start = row

    n_data_rows = t1_end - t1_start + 1

    # Write date references linked to Tab 1
    for i in range(n_data_rows):
        ws.cell(row=ewma_data_start + i, column=1,
                value=f"='{tab1_name}'!A{t1_start + i}")
        ws.cell(row=ewma_data_start + i, column=1).number_format = FMT_DATE

    # Write EWMA variance + annualized vol formulas for each ticker
    for ticker in avail:
        ret_cl = ret_col_map[ticker]
        var_cn, vol_cn, var_cl, vol_cl = ewma_col_info[ticker]
        init_rng = sheet_range(tab1_name, ret_cl, t1_start, t1_start + 59)

        for i in range(n_data_rows):
            t7r = ewma_data_start + i
            if i < 60:
                # Init: population variance of first 60 returns
                ws.cell(row=t7r, column=var_cn, value=f_ewma_init(init_rng))
            else:
                # Recursive: σ²_t = λ·σ²_{t-1} + (1-λ)·r²_{t-1}
                prev_var = f"{var_cl}{t7r - 1}"
                prev_ret = sheet_ref(tab1_name, ret_cl, t1_start + i - 1)
                ws.cell(row=t7r, column=var_cn,
                        value=f_ewma_step(prev_var, prev_ret, lam))

            # Annualized vol = SQRT(variance) * SQRT(252)
            ws.cell(row=t7r, column=vol_cn,
                    value=f_ewma_annualized_vol(f"{var_cl}{t7r}"))
            ws.cell(row=t7r, column=vol_cn).number_format = FMT_PCT

    ewma_end_row = ewma_data_start + n_data_rows

    # Store positions for downstream tabs (Tab 10, Tab 13)
    results["tab7_name"] = TAB_NAMES[7]
    results["tab7_ewma_col_map"] = {t: (vcl, acl) for t, (_, _, vcl, acl) in ewma_col_info.items()}
    results["tab7_data_start"] = ewma_data_start
    results["tab7_data_end"] = ewma_end_row - 1

    # Compute EWMA in Python for downstream tabs that need values at build time
    ewma_vols = {}
    for ticker in avail:
        rets = log_ret.get(ticker, pd.Series(dtype=float)).dropna()
        if len(rets) < 61:
            continue
        init_var = float(rets.iloc[:60].var(ddof=0))
        variances = [init_var] * 60
        for i in range(60, len(rets)):
            var_t = lam * variances[-1] + (1 - lam) * rets.iloc[i - 1] ** 2
            variances.append(var_t)
        vol_series = pd.Series(np.sqrt(variances) * np.sqrt(252), index=rets.index)
        ewma_vols[ticker] = vol_series

    # EWMA Volatility Chart
    if avail:
        chart = LineChart()
        chart.title = "EWMA Annualized Volatility"
        chart.y_axis.title = "Annualized Vol"
        chart.width = 30
        chart.height = 15
        dates_ref = Reference(ws, min_col=1, min_row=header_row, max_row=ewma_end_row - 1)
        for ticker in avail[:5]:
            _, vol_cn, _, _ = ewma_col_info[ticker]
            data_ref = Reference(ws, min_col=vol_cn, min_row=header_row, max_row=ewma_end_row - 1)
            chart.add_data(data_ref, titles_from_data=True)
        chart.set_categories(dates_ref)
        ws.add_chart(chart, f"{get_column_letter(col_idx + 2)}{header_row}")

    # ── Tier 2: GJR-GARCH ──────────────────────────────────────────────
    gjr_row = ewma_end_row + 3
    ws.cell(row=gjr_row, column=1, value="TIER 2 — GJR-GARCH(1,1) ESTIMATION").font = FONT_SUBTITLE
    gjr_row += 1

    # Determine top-5 highest-beta stocks
    reg_results = results.get("reg_results", {})
    oil_betas = {t: abs(reg_results[t]["oil_beta"]) for t in reg_results}
    gjr_stocks = sorted(oil_betas, key=oil_betas.get, reverse=True)[:5] if oil_betas else ["COP", "OXY", "FRO", "STNG", "LNG"]

    gjr_headers = ["Security", "ω", "α", "γ (asymmetry)", "β", "Persistence", "Half-Life (days)", "Log-Likelihood"]
    for j, h in enumerate(gjr_headers):
        ws.cell(row=gjr_row, column=j + 1, value=h).font = FONT_HEADER
        ws.cell(row=gjr_row, column=j + 1).fill = FILL_HEADER
    gjr_row += 1

    gjr_results = {}
    for ticker in gjr_stocks:
        rets = log_ret.get(ticker, pd.Series(dtype=float)).dropna().values
        if len(rets) < 100:
            continue

        try:
            omega, alpha, gamma, beta_g, ll = _fit_gjr_garch(rets)
            persistence = alpha + gamma / 2 + beta_g
            half_life = np.log(0.5) / np.log(persistence) if 0 < persistence < 1 else np.nan

            ws.cell(row=gjr_row, column=1, value=ticker)
            ws.cell(row=gjr_row, column=2, value=omega).number_format = '0.00000000'
            ws.cell(row=gjr_row, column=3, value=round(alpha, 4)).number_format = FMT_NUM4
            ws.cell(row=gjr_row, column=4, value=round(gamma, 4)).number_format = FMT_NUM4
            ws.cell(row=gjr_row, column=5, value=round(beta_g, 4)).number_format = FMT_NUM4
            ws.cell(row=gjr_row, column=6, value=round(persistence, 4)).number_format = FMT_NUM4
            ws.cell(row=gjr_row, column=7, value=round(half_life, 1) if not np.isnan(half_life) else "N/A")
            ws.cell(row=gjr_row, column=8, value=round(ll, 2)).number_format = FMT_NUM2

            gjr_results[ticker] = {"omega": omega, "alpha": alpha, "gamma": gamma, "beta": beta_g}
        except Exception as e:
            ws.cell(row=gjr_row, column=1, value=ticker)
            ws.cell(row=gjr_row, column=2, value=f"Failed: {str(e)}")

        gjr_row += 1

    results["ewma_vols"] = ewma_vols
    results["gjr_results"] = gjr_results

    auto_width(ws)
    return results


def _fit_gjr_garch(returns, max_iter=500):
    """Fit GJR-GARCH(1,1) model using scipy.optimize."""
    r = returns
    T = len(r)
    var_init = np.var(r[:60]) if len(r) >= 60 else np.var(r)

    def neg_log_likelihood(params):
        omega, alpha, gamma, beta = params
        sigma2 = np.empty(T)
        sigma2[0] = var_init
        for t in range(1, T):
            indicator = 1.0 if r[t - 1] < 0 else 0.0
            sigma2[t] = omega + alpha * r[t - 1] ** 2 + gamma * r[t - 1] ** 2 * indicator + beta * sigma2[t - 1]
            sigma2[t] = max(sigma2[t], 1e-12)
        # FIX #15: Include -0.5*T*log(2π) constant for correct log-likelihood value
        ll = -0.5 * (T * np.log(2 * np.pi) + np.sum(np.log(sigma2) + r ** 2 / sigma2))
        return -ll  # minimize negative log-likelihood

    x0 = [1e-5, 0.05, 0.04, 0.90]
    bounds = [(1e-10, 0.01), (0.001, 0.5), (0.0, 0.5), (0.5, 0.999)]
    # FIX #14: Add constraint alpha + gamma >= 0 to prevent negative variance
    constraints = [
        {"type": "ineq", "fun": lambda p: 0.9999 - (p[1] + p[2] / 2 + p[3])},  # stationarity
        {"type": "ineq", "fun": lambda p: p[1] + p[2]},  # alpha + gamma >= 0
    ]

    result = minimize(neg_log_likelihood, x0, method="SLSQP", bounds=bounds,
                      constraints=constraints, options={"maxiter": max_iter})

    omega, alpha, gamma, beta = result.x
    ll = -result.fun
    return omega, alpha, gamma, beta, ll


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 8 — PORTFOLIO CONSTRUCTION (MEAN-VARIANCE)
# ═══════════════════════════════════════════════════════════════════════════════
def build_tab_08(wb, data, results):
    ws = wb.create_sheet(title=TAB_NAMES[8])
    set_tab_color(ws, TAB_COLORS["blue"])

    log_ret = data["log_returns"]
    regime = results.get("regime", pd.Series(dtype=float))

    ws["A1"] = "PORTFOLIO CONSTRUCTION (MEAN-VARIANCE)"
    ws["A1"].font = FONT_TITLE

    port_tickers = [t for t in ALL_TICKERS if t in log_ret.columns]
    n = len(port_tickers)
    ret_df = log_ret[port_tickers].dropna()

    if len(ret_df) < 30:
        ws["A3"] = "Insufficient data for portfolio optimization"
        return results

    # Fix 5: Regime-probability-weighted expected returns (annualized)
    # E[R_i] = sum_k P(Regime_k) * mu_i|Regime_k
    mu = np.zeros(len(port_tickers))
    total_regime_days = 0
    regime_aligned = regime.reindex(log_ret.index, fill_value=0)
    for reg_id in [1, 2, 3, 4]:
        reg_mask = (regime_aligned == reg_id)
        n_reg = int(reg_mask.sum())
        if n_reg > 0:
            total_regime_days += n_reg
            for i, t in enumerate(port_tickers):
                if t in log_ret.columns:
                    reg_rets = log_ret.loc[reg_mask, t].dropna()
                    if len(reg_rets) > 0:
                        mu[i] += n_reg * float(reg_rets.mean()) * 252
    if total_regime_days > 0:
        mu /= total_regime_days
    else:
        # Fallback: simple full-period mean
        mu = ret_df.mean().values * 252

    cov = ret_df.cov().values * 252

    results["port_tickers"] = port_tickers
    results["port_mu"] = mu
    results["port_cov"] = cov

    bil_idx = port_tickers.index("BIL") if "BIL" in port_tickers else None

    # ── Portfolio 1: Minimum Variance ───────────────────────────────────
    def port_vol(w):
        return np.sqrt(w @ cov @ w)

    def port_ret(w):
        return w @ mu

    constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1}]
    bounds = [(0, MAX_WEIGHT) for _ in range(n)]
    if bil_idx is not None:
        bounds[bil_idx] = (MIN_BIL_WEIGHT, MAX_WEIGHT)

    w0 = np.ones(n) / n

    # MVP
    res_mvp = minimize(port_vol, w0, method="SLSQP", bounds=bounds, constraints=constraints)
    w_mvp = res_mvp.x

    # ── Portfolio 2: Tangency (Max Sharpe) ───────────────────────────────
    def neg_sharpe(w):
        ret = w @ mu
        vol = np.sqrt(w @ cov @ w)
        return -(ret - RF_RATE) / vol if vol > 1e-10 else 1e10

    res_tang = minimize(neg_sharpe, w0, method="SLSQP", bounds=bounds, constraints=constraints)
    w_tang = res_tang.x

    # ── Portfolio 3: Crisis-Optimized ────────────────────────────────────
    regime_corrs = results.get("regime_corrs", {})
    if 3 in regime_corrs:
        crisis_mask = (regime == 3).reindex(ret_df.index, fill_value=False)
        if crisis_mask.sum() > 10:
            crisis_ret = ret_df[crisis_mask].dropna()
            cov_crisis = crisis_ret.cov().values * 252
        else:
            cov_crisis = cov
    else:
        cov_crisis = cov

    def port_vol_crisis(w):
        return np.sqrt(w @ cov_crisis @ w)

    res_crisis = minimize(port_vol_crisis, w0, method="SLSQP", bounds=bounds, constraints=constraints)
    w_crisis = res_crisis.x

    # ── Portfolio 4: Risk Parity ─────────────────────────────────────────
    def risk_parity_obj(w):
        sigma = np.sqrt(w @ cov @ w)
        if sigma < 1e-10:
            return 1e10
        mrc = cov @ w / sigma
        rc = w * mrc
        rc_pct = rc / sigma
        target = 1.0 / n
        return np.sum((rc_pct - target) ** 2)

    res_rp = minimize(risk_parity_obj, w0, method="SLSQP", bounds=bounds, constraints=constraints)
    w_rp = res_rp.x

    # ── Portfolio 5: Equal Weight ────────────────────────────────────────
    w_eq = np.ones(n) / n

    portfolios = {
        "Minimum Variance": w_mvp,
        "Tangency (Max Sharpe)": w_tang,
        "Crisis-Optimized": w_crisis,
        "Risk Parity": w_rp,
        "Equal Weight": w_eq,
    }

    # ── Write Portfolio Summary ──────────────────────────────────────────
    row = 3
    ws.cell(row=row, column=1, value="PORTFOLIO SUMMARY").font = FONT_SUBTITLE
    row += 1

    sum_headers = ["Portfolio", "Ann Return", "Ann Volatility", "Sharpe Ratio"]
    for j, h in enumerate(sum_headers):
        ws.cell(row=row, column=j + 1, value=h).font = FONT_HEADER
        ws.cell(row=row, column=j + 1).fill = FILL_HEADER
    row += 1

    port_stats = {}
    for name, w in portfolios.items():
        ret = float(w @ mu)
        vol = float(np.sqrt(w @ cov @ w))
        sharpe = (ret - RF_RATE) / vol if vol > 0 else 0
        ws.cell(row=row, column=1, value=name)
        ws.cell(row=row, column=2, value=ret).number_format = FMT_PCT
        ws.cell(row=row, column=3, value=vol).number_format = FMT_PCT
        ws.cell(row=row, column=4, value=sharpe).number_format = FMT_NUM2
        port_stats[name] = {"return": ret, "vol": vol, "sharpe": sharpe, "weights": w}
        row += 1

    results["portfolios"] = port_stats

    # ── Weight Table ─────────────────────────────────────────────────────
    row += 2
    ws.cell(row=row, column=1, value="PORTFOLIO WEIGHTS").font = FONT_SUBTITLE
    row += 1
    w_headers = ["Ticker"] + list(portfolios.keys())
    for j, h in enumerate(w_headers):
        ws.cell(row=row, column=j + 1, value=h).font = FONT_HEADER
        ws.cell(row=row, column=j + 1).fill = FILL_HEADER
    row += 1

    tab8_weight_start_row = row
    for i, ticker in enumerate(port_tickers):
        ws.cell(row=row, column=1, value=ticker)
        for j, (name, w) in enumerate(portfolios.items()):
            ws.cell(row=row, column=j + 2, value=round(w[i], 4)).number_format = FMT_PCT
        row += 1

    # Store weight positions for downstream tabs (Tab 10 portfolio VaR, Tab 11 MC)
    results["tab8_name"] = TAB_NAMES[8]
    results["tab8_weight_start_row"] = tab8_weight_start_row
    results["tab8_weight_col_map"] = {
        name: get_column_letter(j + 2) for j, name in enumerate(portfolios.keys())
    }

    # ── Efficient Frontier Points ────────────────────────────────────────
    row += 2
    ws.cell(row=row, column=1, value="EFFICIENT FRONTIER").font = FONT_SUBTITLE
    row += 1
    ef_headers = ["Target Return", "Min Volatility"]
    for j, h in enumerate(ef_headers):
        ws.cell(row=row, column=j + 1, value=h).font = FONT_HEADER
        ws.cell(row=row, column=j + 1).fill = FILL_HEADER
    row += 1

    min_ret = float(port_ret(w_mvp))
    max_ret = float(np.max(mu))
    ef_points = []

    for target in np.linspace(min_ret, max_ret, 20):
        cons = [
            {"type": "eq", "fun": lambda w: np.sum(w) - 1},
            {"type": "eq", "fun": lambda w, t=target: w @ mu - t},
        ]
        try:
            res = minimize(port_vol, w0, method="SLSQP", bounds=bounds, constraints=cons)
            if res.success:
                v = float(port_vol(res.x))
                ws.cell(row=row, column=1, value=target).number_format = FMT_PCT
                ws.cell(row=row, column=2, value=v).number_format = FMT_PCT
                ef_points.append((v, target))
                row += 1
        except Exception:
            pass

    # Efficient frontier scatter chart
    if ef_points:
        ef_start = row - len(ef_points) - 1
        chart = ScatterChart()
        chart.title = "Efficient Frontier"
        chart.x_axis.title = "Volatility"
        chart.y_axis.title = "Return"
        chart.width = 25
        chart.height = 18
        x_vals = Reference(ws, min_col=2, min_row=ef_start + 1, max_row=ef_start + len(ef_points))
        y_vals = Reference(ws, min_col=1, min_row=ef_start + 1, max_row=ef_start + len(ef_points))
        chart.add_data(y_vals, titles_from_data=False)
        chart.series[0].xvalues = x_vals
        from openpyxl.chart.series import SeriesLabel
        chart.series[0].tx = SeriesLabel(v="Efficient Frontier")
        ws.add_chart(chart, "H3")

    auto_width(ws)
    return results


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 9 — FUNDAMENTAL VALUATION (DCF)
# ═══════════════════════════════════════════════════════════════════════════════
def build_tab_09(wb, data, results):
    ws = wb.create_sheet(title=TAB_NAMES[9])
    set_tab_color(ws, TAB_COLORS["red"])

    master = data["master"]

    ws["A1"] = "FUNDAMENTAL VALUATION (DCF & MULTIPLES) [EXCEL FORMULA CHAIN]"
    ws["A1"].font = FONT_TITLE

    tab1_name = results.get("tab1_name", TAB_NAMES[1])
    tab6_name = results.get("tab6_name", TAB_NAMES[6])
    tab6_betas = results.get("tab6_market_beta_positions", {})
    price_col_map = results.get("tab1_price_col_map", {})
    t1_end = results.get("tab1_ret_end_row", 1000)

    row = add_definition(ws, 2, 1, "Discounted Cash Flow (DCF)",
        "Projects free cash flow for 5 years + terminal value, discounts at WACC. "
        "Yellow cells are INPUT assumptions (editable). All other cells are LIVE formulas. "
        "WACC beta is linked to Tab 6 via cross-sheet reference. Current price from Tab 1.",
        "Implied share price vs current price → Upside/Downside %")

    row += 1
    dcf_values = {}

    for ticker in DCF_STOCKS:
        fd = FUNDAMENTALS.get(ticker, {})
        params = DCF_PARAMS.get(ticker, {})
        if not params:
            continue

        ws.cell(row=row, column=1, value=f"DCF MODEL: {ticker} — {fd.get('name', '')}").font = FONT_SUBTITLE
        row += 1

        # ── INPUT ASSUMPTIONS (yellow cells — user-editable) ────────────
        ws.cell(row=row, column=1, value="INPUTS (editable)").font = FONT_HEADER
        ws.cell(row=row, column=1).fill = FILL_INPUT
        row += 1

        def _input(r, c, label, val, fmt=FMT_NUM2):
            ws.cell(row=r, column=c, value=label).font = FONT_NORMAL
            cell = ws.cell(row=r, column=c + 1, value=val)
            cell.font = FONT_INPUT
            cell.fill = FILL_INPUT
            cell.number_format = fmt
            return f"{get_column_letter(c + 1)}{r}"

        # Base revenue, tax, capex%, da%, wc%
        base_rev_cell = _input(row, 1, "Base Revenue ($B)", fd["revenue"] / 1e9, '$#,##0.0')
        row += 1
        tax_cell = _input(row, 1, "Tax Rate", params["tax_rate"], FMT_PCT)
        row += 1
        capex_cell = _input(row, 1, "Capex / Revenue", params["capex_pct"], FMT_PCT)
        row += 1
        da_cell = _input(row, 1, "D&A / Revenue", params["da_pct"], FMT_PCT)
        row += 1
        wc_cell = _input(row, 1, "ΔWC / Revenue", params["wc_change_pct"], FMT_PCT)
        row += 1
        shares_cell = _input(row, 1, "Shares Outstanding (B)", params["shares_out"] / 1e9, '0.000')
        row += 1
        eq_val_cell = _input(row, 1, "Equity Value ($B)", fd["mkt_cap"] / 1e9, '$#,##0.0')
        row += 1
        gross_debt = max(fd.get("net_debt_ebitda", 0) * fd.get("ebitda", 0), 0) if fd.get("ebitda") else 0
        debt_cell = _input(row, 1, "Debt ($B)", gross_debt / 1e9, '$#,##0.0')
        row += 1
        rd_cell = _input(row, 1, "Cost of Debt (Rd)", fd.get("wacc_rd", 0.05), FMT_PCT)
        row += 1
        rf_cell = _input(row, 1, "Risk-Free Rate (Rf)", RF_RATE, FMT_PCT)
        row += 1
        erp_cell = _input(row, 1, "Equity Risk Premium", EQUITY_RISK_PREMIUM, FMT_PCT)
        row += 1
        tg_cell = _input(row, 1, "Terminal Growth (g)", TERMINAL_GROWTH, FMT_PCT)
        row += 1

        # Oil prices and per-year assumptions (columns D-H for years 1-5)
        ws.cell(row=row, column=1, value="Year Assumptions").font = FONT_HEADER
        for yr in range(5):
            ws.cell(row=row, column=4 + yr, value=f"FY{2026 + yr}E").font = FONT_HEADER
        row += 1

        # Oil prices
        ws.cell(row=row, column=1, value="Oil Price ($/bbl)")
        oil_cells = []
        for yr in range(5):
            c = ws.cell(row=row, column=4 + yr, value=OIL_PRICE_PATH[yr])
            c.font = FONT_INPUT
            c.fill = FILL_INPUT
            c.number_format = '$#,##0'
            oil_cells.append(f"{get_column_letter(4 + yr)}{row}")
        oil_base_cell = _input(row, 1, "Oil Price ($/bbl)", OIL_PRICE_PATH[0], '$#,##0')
        # overwrite label
        ws.cell(row=row, column=1, value="Oil Price ($/bbl)")
        ws.cell(row=row, column=2, value=f"Base: ${OIL_PRICE_PATH[0]}")
        row += 1

        # Growth rates
        ws.cell(row=row, column=1, value="Production Growth")
        growth_cells = []
        for yr in range(5):
            c = ws.cell(row=row, column=4 + yr, value=params["prod_growth"][yr])
            c.font = FONT_INPUT
            c.fill = FILL_INPUT
            c.number_format = FMT_PCT
            growth_cells.append(f"{get_column_letter(4 + yr)}{row}")
        row += 1

        # EBITDA margins
        ws.cell(row=row, column=1, value="EBITDA Margin")
        margin_cells = []
        for yr in range(5):
            c = ws.cell(row=row, column=4 + yr, value=params["ebitda_margin"][yr])
            c.font = FONT_INPUT
            c.fill = FILL_INPUT
            c.number_format = FMT_PCT
            margin_cells.append(f"{get_column_letter(4 + yr)}{row}")
        row += 1

        # ── WACC CALCULATION (formula chain, beta linked to Tab 6) ──────
        row += 1
        ws.cell(row=row, column=1, value="WACC CALCULATION").font = FONT_HEADER
        row += 1

        # Beta — cross-sheet reference to Tab 6
        ws.cell(row=row, column=1, value="Market Beta (→Tab 6)")
        beta_ref = tab6_betas.get(ticker, "1.0")
        if ticker in tab6_betas:
            beta_formula = f"='{tab6_name}'!{beta_ref}"
            ws.cell(row=row, column=2, value=beta_formula).number_format = FMT_NUM4
            ws.cell(row=row, column=2).font = FONT_LINKED
        else:
            ws.cell(row=row, column=2, value=1.0).number_format = FMT_NUM4
        beta_cell = f"B{row}"
        row += 1

        # Re = Rf + Beta * ERP
        ws.cell(row=row, column=1, value="Cost of Equity (Re)")
        ws.cell(row=row, column=2, value=f"={rf_cell}+{beta_cell}*{erp_cell}").number_format = FMT_PCT
        re_cell = f"B{row}"
        row += 1

        # WACC = E/(E+D)*Re + D/(E+D)*Rd*(1-Tax)
        ws.cell(row=row, column=1, value="WACC")
        ws.cell(row=row, column=2,
                value=f"={eq_val_cell}/({eq_val_cell}+{debt_cell})*{re_cell}"
                      f"+{debt_cell}/({eq_val_cell}+{debt_cell})*{rd_cell}*(1-{tax_cell})")
        ws.cell(row=row, column=2).number_format = FMT_PCT
        ws.cell(row=row, column=2).font = FONT_TITLE
        wacc_cell = f"B{row}"
        row += 1

        # ── PROJECTION TABLE (all Excel formulas) ──────────────────────
        row += 1
        ws.cell(row=row, column=1, value="PROJECTION [FORMULAS]").font = FONT_HEADER
        proj_headers = ["Year", "Oil $/bbl", "Revenue $B", "EBITDA $B", "D&A $B",
                        "EBIT $B", "NOPAT $B", "Capex $B", "ΔWC $B", "FCF $B", "PV(FCF) $B"]
        for j, h in enumerate(proj_headers):
            ws.cell(row=row, column=j + 1, value=h).font = FONT_HEADER
            ws.cell(row=row, column=j + 1).fill = FILL_HEADER
        row += 1

        fcf_cells = []
        pv_cells = []
        prev_rev_cell = base_rev_cell
        prev_oil_cell = None

        for yr in range(5):
            ws.cell(row=row, column=1, value=f"FY{2026 + yr}E")
            # Oil price (linked to input)
            ws.cell(row=row, column=2, value=f"={oil_cells[yr]}").number_format = '$#,##0'
            oil_ref = f"B{row}"

            # Revenue: base_rev * (1+growth) * (oil_t/oil_prev)
            if yr == 0:
                rev_formula = f"={prev_rev_cell}*(1+{growth_cells[yr]})*({oil_ref}/{OIL_PRICE_PATH[0]})"
            else:
                rev_formula = f"={prev_rev_cell}*(1+{growth_cells[yr]})*({oil_ref}/{prev_oil_cell})"
            ws.cell(row=row, column=3, value=rev_formula).number_format = '$#,##0.0'
            rev_cell = f"C{row}"

            # EBITDA = Revenue * Margin
            ws.cell(row=row, column=4, value=f"={rev_cell}*{margin_cells[yr]}").number_format = '$#,##0.0'
            ebitda_c = f"D{row}"

            # D&A = Revenue * DA_pct
            ws.cell(row=row, column=5, value=f"={rev_cell}*{da_cell}").number_format = '$#,##0.0'
            da_c = f"E{row}"

            # EBIT = EBITDA - D&A
            ws.cell(row=row, column=6, value=f"={ebitda_c}-{da_c}").number_format = '$#,##0.0'
            ebit_c = f"F{row}"

            # NOPAT = EBIT * (1-Tax)
            ws.cell(row=row, column=7, value=f"={ebit_c}*(1-{tax_cell})").number_format = '$#,##0.0'
            nopat_c = f"G{row}"

            # Capex = Revenue * Capex_pct
            ws.cell(row=row, column=8, value=f"={rev_cell}*{capex_cell}").number_format = '$#,##0.0'
            capex_c = f"H{row}"

            # ΔWC = Revenue * WC_pct
            ws.cell(row=row, column=9, value=f"={rev_cell}*{wc_cell}").number_format = '$#,##0.0'
            wc_c = f"I{row}"

            # FCF = NOPAT + D&A - Capex - ΔWC
            ws.cell(row=row, column=10, value=f"={nopat_c}+{da_c}-{capex_c}-{wc_c}").number_format = '$#,##0.0'
            fcf_c = f"J{row}"
            fcf_cells.append(fcf_c)

            # PV(FCF) = FCF / (1+WACC)^year
            ws.cell(row=row, column=11,
                    value=f"={fcf_c}/(1+{wacc_cell})^{yr + 1}").number_format = '$#,##0.0'
            pv_cells.append(f"K{row}")

            prev_rev_cell = rev_cell
            prev_oil_cell = oil_ref
            row += 1

        # ── VALUATION SUMMARY (all formulas) ───────────────────────────
        row += 1
        ws.cell(row=row, column=1, value="VALUATION SUMMARY").font = FONT_HEADER
        row += 1

        # Terminal Value = FCF_yr5 * (1+g) / (WACC-g)
        ws.cell(row=row, column=1, value="Terminal Value ($B)")
        ws.cell(row=row, column=2,
                value=f"={fcf_cells[-1]}*(1+{tg_cell})/({wacc_cell}-{tg_cell})").number_format = '$#,##0.0'
        tv_cell = f"B{row}"
        row += 1

        # PV of FCFs = SUM(PV cells)
        ws.cell(row=row, column=1, value="PV of FCFs ($B)")
        pv_sum_formula = f"={'+'.join(pv_cells)}"
        ws.cell(row=row, column=2, value=pv_sum_formula).number_format = '$#,##0.0'
        pv_fcfs_cell = f"B{row}"
        row += 1

        # PV of Terminal = TV / (1+WACC)^5
        ws.cell(row=row, column=1, value="PV of Terminal ($B)")
        ws.cell(row=row, column=2, value=f"={tv_cell}/(1+{wacc_cell})^5").number_format = '$#,##0.0'
        pv_tv_cell = f"B{row}"
        row += 1

        # Enterprise Value = PV_FCFs + PV_TV
        ws.cell(row=row, column=1, value="Enterprise Value ($B)")
        ws.cell(row=row, column=2, value=f"={pv_fcfs_cell}+{pv_tv_cell}").number_format = '$#,##0.0'
        ev_cell = f"B{row}"
        row += 1

        # Equity Value = EV - Debt
        ws.cell(row=row, column=1, value="Equity Value ($B)")
        ws.cell(row=row, column=2, value=f"={ev_cell}-{debt_cell}").number_format = '$#,##0.0'
        equity_val_cell = f"B{row}"
        row += 1

        # Implied Price = Equity_Value / Shares (convert $B to $ per share)
        ws.cell(row=row, column=1, value="Implied Share Price")
        ws.cell(row=row, column=2, value=f"={equity_val_cell}/{shares_cell}").number_format = FMT_MONEY
        ws.cell(row=row, column=2).font = FONT_TITLE
        implied_cell = f"B{row}"
        row += 1

        # Current Price (linked to Tab 1)
        ws.cell(row=row, column=1, value="Current Price (→Tab 1)")
        if ticker in price_col_map:
            price_cl = price_col_map[ticker]
            ws.cell(row=row, column=2,
                    value=f"='{tab1_name}'!{price_cl}{t1_end}").number_format = FMT_MONEY
            ws.cell(row=row, column=2).font = FONT_LINKED
        else:
            current_price = fd["eps"] * fd["pe"]
            ws.cell(row=row, column=2, value=current_price).number_format = FMT_MONEY
        current_cell = f"B{row}"
        row += 1

        # Upside/Downside = (Implied - Current) / Current
        ws.cell(row=row, column=1, value="Upside / Downside")
        ws.cell(row=row, column=2,
                value=f"=({implied_cell}-{current_cell})/{current_cell}").number_format = FMT_PCT
        row += 2

        # Python values for downstream tabs
        reg_results = results.get("reg_results", {})
        equity_beta = abs(reg_results.get(ticker, {}).get("market_beta", 1.0))
        re = RF_RATE + equity_beta * EQUITY_RISK_PREMIUM
        rd_val = fd.get("wacc_rd", 0.05)
        tax = params["tax_rate"]
        ev = fd["mkt_cap"]
        d = gross_debt
        wacc_val = (ev / (ev + d)) * re + (d / (ev + d)) * rd_val * (1 - tax) if (ev + d) > 0 else 0.10
        if ticker in master.columns and len(master[ticker].dropna()) > 0:
            cp = float(master[ticker].dropna().iloc[-1])
        else:
            cp = fd["eps"] * fd["pe"]
        # Compute implied price in Python for downstream
        base_rev = fd["revenue"] / 1e9
        prev_rev_py = base_rev
        prev_oil_py = OIL_PRICE_PATH[0]
        fcfs_py = []
        for yr in range(5):
            oil_p = OIL_PRICE_PATH[yr]
            rev_py = prev_rev_py * (1 + params["prod_growth"][yr]) * (oil_p / prev_oil_py)
            ebitda_py = rev_py * params["ebitda_margin"][yr]
            da_py = rev_py * params["da_pct"]
            fcf_py = (ebitda_py - da_py) * (1 - tax) + da_py - rev_py * params["capex_pct"] - rev_py * params["wc_change_pct"]
            fcfs_py.append(fcf_py)
            prev_rev_py = rev_py
            prev_oil_py = oil_p
        if wacc_val > TERMINAL_GROWTH:
            tv_py = fcfs_py[-1] * (1 + TERMINAL_GROWTH) / (wacc_val - TERMINAL_GROWTH)
        else:
            tv_py = fcfs_py[-1] * 20
        pv_fcfs_py = sum(f / (1 + wacc_val) ** (i + 1) for i, f in enumerate(fcfs_py))
        pv_tv_py = tv_py / (1 + wacc_val) ** 5
        ev_py = pv_fcfs_py + pv_tv_py
        eq_py = ev_py - d / 1e9
        ip = eq_py / (params["shares_out"] / 1e9) if params["shares_out"] > 0 else 0
        dcf_values[ticker] = {
            "implied_price": ip,
            "current_price": cp,
            "upside": (ip - cp) / cp if cp > 0 else 0,
            "wacc": wacc_val,
        }

    # ── Sensitivity Table (WACC vs Terminal Growth) ──────────────────────
    ws.cell(row=row, column=1, value="SENSITIVITY: WACC vs Terminal Growth").font = FONT_SUBTITLE
    row += 1
    # Use last DCF stock as example
    if dcf_values:
        last_ticker = DCF_STOCKS[-1]
        last_fcf = fcfs_py[-1] if fcfs_py else 1e9
        last_shares = DCF_PARAMS.get(last_ticker, {}).get("shares_out", 1e9)
        # FIX: Use same debt calculation as main DCF (net_debt_ebitda * ebitda)
        # instead of EV - mkt_cap, for consistency with the DCF model above
        last_fd = FUNDAMENTALS.get(last_ticker, {})
        last_debt_ebitda = last_fd.get("net_debt_ebitda", 0) or 0
        last_ebitda = last_fd.get("ebitda", 0) or 0
        last_debt = max(last_debt_ebitda * last_ebitda, 0)

        ws.cell(row=row, column=1, value=f"Sensitivity for {last_ticker}")
        row += 1
        g_range = [0.01, 0.015, 0.02, 0.025, 0.03]
        wacc_range = [0.06, 0.07, 0.08, 0.09, 0.10, 0.11, 0.12]

        ws.cell(row=row, column=1, value="WACC \\ g")
        for j, g in enumerate(g_range):
            ws.cell(row=row, column=j + 2, value=g).number_format = FMT_PCT
        row += 1

        for w in wacc_range:
            ws.cell(row=row, column=1, value=w).number_format = FMT_PCT
            for j, g in enumerate(g_range):
                if w > g:
                    tv_sens = last_fcf * (1 + g) / (w - g)
                    ev_sens = sum(fcf / (1 + w) ** (i + 1) for i, fcf in enumerate(fcfs_py)) + tv_sens / (1 + w) ** 5
                    eq_sens = ev_sens - last_debt
                    price_sens = eq_sens / last_shares if last_shares > 0 else 0
                    ws.cell(row=row, column=j + 2, value=price_sens).number_format = FMT_MONEY
                else:
                    ws.cell(row=row, column=j + 2, value="N/A")
            row += 1

    results["dcf_values"] = dcf_values

    # ── Multiples-Based Valuation ────────────────────────────────────────
    row += 2
    ws.cell(row=row, column=1, value="MULTIPLES-BASED VALUATION").font = FONT_SUBTITLE
    row += 1
    mult_headers = ["Ticker", "P/E", "Peer Median P/E", "P/E Implied Price", "EV/EBITDA", "Peer Median EV/EBITDA"]
    for j, h in enumerate(mult_headers):
        ws.cell(row=row, column=j + 1, value=h).font = FONT_HEADER
        ws.cell(row=row, column=j + 1).fill = FILL_HEADER
    row += 1

    # Peer groups
    peer_groups = {
        "Integrated": ["XOM", "CVX"],
        "E&P": ["COP", "OXY"],
        "LNG": ["LNG", "VG"],
        "Shipping": ["FRO", "STNG"],
        "Midstream": ["ET"],
    }

    for group_name, peers in peer_groups.items():
        pe_vals = [FUNDAMENTALS[t]["pe"] for t in peers if t in FUNDAMENTALS and FUNDAMENTALS[t]["pe"]]
        ev_vals = [FUNDAMENTALS[t]["ev_ebitda"] for t in peers if t in FUNDAMENTALS and FUNDAMENTALS[t]["ev_ebitda"]]
        median_pe = np.median(pe_vals) if pe_vals else None
        median_ev = np.median(ev_vals) if ev_vals else None

        for ticker in peers:
            fd = FUNDAMENTALS.get(ticker, {})
            ws.cell(row=row, column=1, value=ticker)
            ws.cell(row=row, column=2, value=fd.get("pe")).number_format = FMT_NUM2
            ws.cell(row=row, column=3, value=median_pe).number_format = FMT_NUM2 if median_pe else None
            if median_pe and fd.get("eps"):
                ws.cell(row=row, column=4, value=median_pe * fd["eps"]).number_format = FMT_MONEY
            ws.cell(row=row, column=5, value=fd.get("ev_ebitda")).number_format = FMT_NUM2
            ws.cell(row=row, column=6, value=median_ev).number_format = FMT_NUM2 if median_ev else None
            row += 1

    auto_width(ws)
    return results


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 10 — VALUE AT RISK (COMPREHENSIVE)
# ═══════════════════════════════════════════════════════════════════════════════
def build_tab_10(wb, data, results):
    ws = wb.create_sheet(title=TAB_NAMES[10])
    set_tab_color(ws, TAB_COLORS["red"])

    log_ret = data["log_returns"]

    ws["A1"] = "VALUE AT RISK — COMPREHENSIVE [LIVE EXCEL FORMULAS]"
    ws["A1"].font = FONT_TITLE
    ws.cell(row=2, column=1, value="Portfolio Value ($):").font = FONT_NORMAL
    pv_cell = ws.cell(row=2, column=2, value=PORTFOLIO_VALUE)
    pv_cell.number_format = '$#,##0'
    pv_cell.font = FONT_INPUT
    pv_cell.fill = FILL_INPUT

    tab1_name = results.get("tab1_name", TAB_NAMES[1])
    ret_col_map = results.get("tab1_ret_col_map", {})
    t1_start = results.get("tab1_ret_start_row", 4)
    t1_end = results.get("tab1_ret_end_row", 1000)

    # ── Definition ──────────────────────────────────────────────────────
    row = add_definition(ws, 3, 1, "Value at Risk (VaR)",
        "Maximum expected loss at a given confidence level. ALL VaR formulas below are "
        "LIVE Excel formulas referencing '01_Data' return columns. Changing data in Tab 1 "
        "automatically recalculates all VaR, Dollar VaR, and backtest results.",
        "VaR 95%: 1-3% for diversified, 3-8% for high-beta energy names")

    # ── Individual Security VaR (Excel formulas) ─────────────────────────
    ws.cell(row=row, column=1, value="INDIVIDUAL SECURITY VaR [EXCEL FORMULAS → Tab 1]").font = FONT_SUBTITLE
    row += 1
    var_headers = [
        "Security", "Gauss VaR 95%", "Hist VaR 95%", "CF VaR 95%", "CVaR 95%",
        "Gauss VaR 99%", "Hist VaR 99%", "CF VaR 99%", "CVaR 99%",
    ]
    for j, h in enumerate(var_headers):
        ws.cell(row=row, column=j + 1, value=h).font = FONT_HEADER
        ws.cell(row=row, column=j + 1).fill = FILL_HEADER

    # Helper columns: Mean, StdDev, Skew, Kurt, z_CF_95, z_CF_99
    hc = 11  # helper start col (K)
    for j, h in enumerate(["Mean", "StdDev", "Skew", "Kurt", "z_CF_95", "z_CF_99"]):
        ws.cell(row=row, column=hc + j, value=h).font = FONT_HEADER
        ws.cell(row=row, column=hc + j).fill = FILL_HEADER
    row += 1

    first_var_row = row
    var_results = {}
    securities = ALL_TICKERS
    mean_cl = get_column_letter(hc)
    std_cl = get_column_letter(hc + 1)
    skew_cl = get_column_letter(hc + 2)
    kurt_cl = get_column_letter(hc + 3)
    zcf95_cl = get_column_letter(hc + 4)
    zcf99_cl = get_column_letter(hc + 5)

    for ticker in securities:
        ws.cell(row=row, column=1, value=ticker)
        if ticker not in ret_col_map:
            row += 1
            continue
        ret_cl = ret_col_map[ticker]
        rng = sheet_range(tab1_name, ret_cl, t1_start, t1_end)

        # Helper columns — statistical moments (Excel formulas → Tab 1)
        ws.cell(row=row, column=hc, value=f"=AVERAGE({rng})").number_format = FMT_NUM4
        ws.cell(row=row, column=hc, value=f"=AVERAGE({rng})").font = FONT_LINKED
        ws.cell(row=row, column=hc + 1, value=f"=STDEV.S({rng})").number_format = FMT_NUM4
        ws.cell(row=row, column=hc + 2, value=f"=SKEW({rng})").number_format = FMT_NUM4
        ws.cell(row=row, column=hc + 3, value=f"=KURT({rng})").number_format = FMT_NUM4
        # Cornish-Fisher adjusted z-scores
        ws.cell(row=row, column=hc + 4,
                value=f_cornish_fisher_z(f"{skew_cl}{row}", f"{kurt_cl}{row}", 0.95)).number_format = FMT_NUM4
        ws.cell(row=row, column=hc + 5,
                value=f_cornish_fisher_z(f"{skew_cl}{row}", f"{kurt_cl}{row}", 0.99)).number_format = FMT_NUM4

        # Gauss VaR 95%: -mean + 1.645*stdev
        ws.cell(row=row, column=2,
                value=f"=-{mean_cl}{row}+1.645*{std_cl}{row}").number_format = FMT_PCT
        # Hist VaR 95%: -PERCENTILE(returns, 0.05)
        ws.cell(row=row, column=3,
                value=f_historical_var(rng, 0.95)).number_format = FMT_PCT
        # CF VaR 95%: -mean + |z_CF|*stdev
        ws.cell(row=row, column=4,
                value=f"=-{mean_cl}{row}+ABS({zcf95_cl}{row})*{std_cl}{row}").number_format = FMT_PCT
        # CVaR 95%: -AVERAGEIF(returns, "<-"&VaR_cell)
        ws.cell(row=row, column=5,
                value=f'=-AVERAGEIF({rng},"<-"&B{row})').number_format = FMT_PCT

        # 99% — same pattern with 2.326 z-score
        ws.cell(row=row, column=6,
                value=f"=-{mean_cl}{row}+2.326*{std_cl}{row}").number_format = FMT_PCT
        ws.cell(row=row, column=7,
                value=f_historical_var(rng, 0.99)).number_format = FMT_PCT
        ws.cell(row=row, column=8,
                value=f"=-{mean_cl}{row}+ABS({zcf99_cl}{row})*{std_cl}{row}").number_format = FMT_PCT
        ws.cell(row=row, column=9,
                value=f'=-AVERAGEIF({rng},"<-"&F{row})').number_format = FMT_PCT

        # Python values for downstream backtest/portfolio VaR
        rets = log_ret.get(ticker, pd.Series(dtype=float)).dropna()
        if len(rets) >= 30:
            mu_r, sigma_r = float(rets.mean()), float(rets.std())
            sk_r, ku_r = float(rets.skew()), float(rets.kurtosis())
            # Cornish-Fisher adjusted z-scores
            z95 = norm.ppf(0.95)
            z99 = norm.ppf(0.99)
            z_cf95 = z95 + (z95**2-1)/6*sk_r + (z95**3-3*z95)/24*ku_r - (2*z95**3-5*z95)/36*sk_r**2
            z_cf99 = z99 + (z99**2-1)/6*sk_r + (z99**3-3*z99)/24*ku_r - (2*z99**3-5*z99)/36*sk_r**2
            # CVaR = expected loss beyond VaR threshold
            var95_threshold = np.percentile(rets, 5)
            var99_threshold = np.percentile(rets, 1)
            cvar95_val = -float(rets[rets <= var95_threshold].mean()) if (rets <= var95_threshold).sum() > 0 else -float(var95_threshold)
            cvar99_val = -float(rets[rets <= var99_threshold].mean()) if (rets <= var99_threshold).sum() > 0 else -float(var99_threshold)
            var_results[ticker] = {
                "gauss_95": -mu_r + z95 * sigma_r,
                "hist_95": -float(var95_threshold),
                "cf_95": -mu_r + abs(z_cf95) * sigma_r,
                "cvar_95": cvar95_val,
                "gauss_99": -mu_r + z99 * sigma_r,
                "hist_99": -float(var99_threshold),
                "cf_99": -mu_r + abs(z_cf99) * sigma_r,
                "cvar_99": cvar99_val,
            }
        row += 1

    last_var_row = row - 1

    # ── Portfolio VaR (Python-computed — requires weighted combination) ──
    portfolios = results.get("portfolios", {})
    port_tickers = results.get("port_tickers", ALL_TICKERS)

    for pname, pdata in portfolios.items():
        w = pdata["weights"]
        # FIX #7: Don't fillna(0) — it treats pre-IPO missing data as 0% returns
        # Instead, only compute portfolio returns where ALL constituents have data
        port_ret_df = pd.DataFrame()
        for i, t in enumerate(port_tickers):
            if t in log_ret.columns:
                port_ret_df[t] = log_ret[t] * w[i]
        port_ret_series = port_ret_df.dropna().sum(axis=1)

        port_rets = port_ret_series.dropna()
        if len(port_rets) < 30:
            continue

        mu_p = float(port_rets.mean())
        sigma_p = float(port_rets.std())
        skew_p = float(port_rets.skew())
        kurt_p = float(port_rets.kurtosis())

        gauss_95 = -mu_p + norm.ppf(0.95) * sigma_p
        gauss_99 = -mu_p + norm.ppf(0.99) * sigma_p
        hist_95 = -float(np.percentile(port_rets, 5))
        hist_99 = -float(np.percentile(port_rets, 1))

        # FIX #6: Portfolio CF-VaR now includes skewness-squared term
        z95 = norm.ppf(0.95)
        z99 = norm.ppf(0.99)
        z_cf_95 = z95 + (z95 ** 2 - 1) / 6 * skew_p + (z95 ** 3 - 3 * z95) / 24 * kurt_p - (2 * z95 ** 3 - 5 * z95) / 36 * skew_p ** 2
        z_cf_99 = z99 + (z99 ** 2 - 1) / 6 * skew_p + (z99 ** 3 - 3 * z99) / 24 * kurt_p - (2 * z99 ** 3 - 5 * z99) / 36 * skew_p ** 2
        cf_95 = -mu_p + abs(z_cf_95) * sigma_p
        cf_99 = -mu_p + abs(z_cf_99) * sigma_p

        thr_95 = np.percentile(port_rets, 5)
        thr_99 = np.percentile(port_rets, 1)
        cvar_95 = -float(port_rets[port_rets <= thr_95].mean()) if len(port_rets[port_rets <= thr_95]) > 0 else hist_95
        cvar_99 = -float(port_rets[port_rets <= thr_99].mean()) if len(port_rets[port_rets <= thr_99]) > 0 else hist_99

        ws.cell(row=row, column=1, value=f"Portfolio: {pname}")
        ws.cell(row=row, column=1).font = FONT_SUBTITLE
        for j, val in enumerate([gauss_95, hist_95, cf_95, cvar_95, gauss_99, hist_99, cf_99, cvar_99]):
            ws.cell(row=row, column=j + 2, value=val).number_format = FMT_PCT
        row += 1

    # ── Dollar VaR Table (Excel formulas referencing main VaR table) ──────
    row += 2
    ws.cell(row=row, column=1, value="DOLLAR VaR TABLE — 1-DAY ($) [FORMULAS → main table × $B$2]").font = FONT_SUBTITLE
    row += 1
    for j, h in enumerate(var_headers):
        ws.cell(row=row, column=j + 1, value=h).font = FONT_HEADER
        ws.cell(row=row, column=j + 1).fill = FILL_HEADER
    row += 1

    dollar_var_start = row
    for i, ticker in enumerate(securities):
        var_row = first_var_row + i
        ws.cell(row=row, column=1, value=ticker)
        for j in range(8):
            src_col = get_column_letter(j + 2)
            ws.cell(row=row, column=j + 2,
                    value=f"={src_col}{var_row}*$B$2").number_format = '$#,##0'
        row += 1

    # ── 10-Day VaR (Excel formulas: main VaR × SQRT(10)) ──────────────
    row += 2
    ws.cell(row=row, column=1, value="10-DAY VaR (%) [FORMULAS → main table × SQRT(10)]").font = FONT_SUBTITLE
    row += 1
    ws.cell(row=row, column=1,
            value="Note: 10-day VaR = 1-day VaR × SQRT(10). Assumes i.i.d. returns.").font = FONT_NORMAL
    row += 1
    var_headers_10d = [
        "Security",
        "Gauss 95% (10d)", "Hist 95% (10d)", "CF 95% (10d)", "CVaR 95% (10d)",
        "Gauss 99% (10d)", "Hist 99% (10d)", "CF 99% (10d)", "CVaR 99% (10d)",
    ]
    for j, h in enumerate(var_headers_10d):
        ws.cell(row=row, column=j + 1, value=h).font = FONT_HEADER
        ws.cell(row=row, column=j + 1).fill = FILL_HEADER
    row += 1

    for i, ticker in enumerate(securities):
        var_row = first_var_row + i
        ws.cell(row=row, column=1, value=ticker)
        for j in range(8):
            src_col = get_column_letter(j + 2)
            ws.cell(row=row, column=j + 2,
                    value=f"={src_col}{var_row}*SQRT(10)").number_format = FMT_PCT
        row += 1

    row += 1
    ws.cell(row=row, column=1, value="10-DAY DOLLAR VaR ($) [FORMULAS → main table × SQRT(10) × $B$2]").font = FONT_SUBTITLE
    row += 1
    for j, h in enumerate(var_headers_10d):
        ws.cell(row=row, column=j + 1, value=h).font = FONT_HEADER
        ws.cell(row=row, column=j + 1).fill = FILL_HEADER
    row += 1

    for i, ticker in enumerate(securities):
        var_row = first_var_row + i
        ws.cell(row=row, column=1, value=ticker)
        for j in range(8):
            src_col = get_column_letter(j + 2)
            ws.cell(row=row, column=j + 2,
                    value=f"={src_col}{var_row}*SQRT(10)*$B$2").number_format = '$#,##0'
        row += 1

    # ── VaR Backtest (Excel formulas: COUNTIF referencing Tab 1) ──────
    row += 2
    ws.cell(row=row, column=1, value="VaR BACKTEST [EXCEL FORMULAS → COUNTIF on Tab 1]").font = FONT_SUBTITLE
    row += 1
    ws.cell(row=row, column=1,
            value="Expected breach rate: 5.0% at 95% VaR, 1.0% at 99% VaR. All counts use COUNTIF formulas.").font = FONT_NORMAL
    row += 1

    bt_headers = [
        "Security", "N Days",
        "Gauss 95% — Exp%", "Gauss 95% — Breaches", "Gauss 95% — Act%", "Gauss 95% — Ratio",
        "Hist 95% — Exp%",  "Hist 95% — Breaches",  "Hist 95% — Act%",  "Hist 95% — Ratio",
        "Gauss 99% — Exp%", "Gauss 99% — Breaches", "Gauss 99% — Act%", "Gauss 99% — Ratio",
        "Hist 99% — Exp%",  "Hist 99% — Breaches",  "Hist 99% — Act%",  "Hist 99% — Ratio",
    ]
    for j, h in enumerate(bt_headers):
        ws.cell(row=row, column=j + 1, value=h).font = FONT_HEADER
        ws.cell(row=row, column=j + 1).fill = FILL_HEADER
    row += 1

    for i, ticker in enumerate(securities):
        if ticker not in ret_col_map:
            continue
        var_row = first_var_row + i
        ret_cl = ret_col_map[ticker]
        rng = sheet_range(tab1_name, ret_cl, t1_start, t1_end)
        n_col = get_column_letter(2)

        ws.cell(row=row, column=1, value=ticker)
        # N Days = COUNT(return_range)
        ws.cell(row=row, column=2, value=f"=COUNT({rng})")

        col = 3
        # (VaR col in main table, expected %)
        for var_src_col, exp_pct in [("B", 0.05), ("C", 0.05), ("F", 0.01), ("G", 0.01)]:
            # Expected %
            ws.cell(row=row, column=col, value=exp_pct).number_format = FMT_PCT
            # Breach count: COUNTIF(returns, "<-"&VaR_cell)
            ws.cell(row=row, column=col + 1,
                    value=f'=COUNTIF({rng},"<-"&{var_src_col}{var_row})')
            # Actual %: breaches / N
            breach_cl = get_column_letter(col + 1)
            ws.cell(row=row, column=col + 2,
                    value=f"={breach_cl}{row}/{n_col}{row}").number_format = FMT_PCT
            # Ratio: actual % / expected %
            act_cl = get_column_letter(col + 2)
            exp_cl = get_column_letter(col)
            ws.cell(row=row, column=col + 3,
                    value=f"={act_cl}{row}/{exp_cl}{row}").number_format = FMT_NUM2
            col += 4

        row += 1

    results["var_results"] = var_results

    # ── VaR Comparison Chart ─────────────────────────────────────────────
    first_var_row = 5
    if len(var_results) > 0:
        chart = BarChart()
        chart.type = "col"
        chart.grouping = "clustered"
        chart.title = "VaR Comparison (95%)"
        chart.y_axis.title = "VaR %"
        chart.width = 28
        chart.height = 15
        data_ref = Reference(ws, min_col=2, max_col=5, min_row=first_var_row - 1, max_row=first_var_row + len(securities) - 1)
        cats = Reference(ws, min_col=1, min_row=first_var_row, max_row=first_var_row + len(securities) - 1)
        chart.add_data(data_ref, titles_from_data=True)
        chart.set_categories(cats)
        ws.add_chart(chart, "K4")

    auto_width(ws)
    return results
