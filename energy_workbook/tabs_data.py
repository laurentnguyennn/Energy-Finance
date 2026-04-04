"""
Tabs 1–5: Market Data Hub, Macro Regime Dashboard, Company Profiles,
Historical Performance Analytics, Correlation & Covariance Structure.

Enhanced with Excel formula-based calculations where feasible.
Cross-sheet references use the helpers in .formulas.
"""
import numpy as np
import pandas as pd
from openpyxl.chart import LineChart, BarChart, Reference
from openpyxl.chart.series import DataPoint
from openpyxl.utils import get_column_letter

from .config import (
    ALL_TICKERS, EQUITY_TICKERS, FUNDAMENTALS, EVENT_WINDOWS,
    REGIME_NAMES, RF_RATE, TAB_NAMES, TAB_COLORS, VG_IPO_DATE, PAIRS,
)
from .styles import (
    FONT_HEADER, FONT_TITLE, FONT_SUBTITLE, FONT_NORMAL, FONT_INPUT,
    FILL_HEADER, FILL_INPUT, FILL_LIGHT_GREEN, FILL_LIGHT_RED,
    THIN_BORDER, BOTTOM_BORDER, ALIGN_CENTER, ALIGN_RIGHT,
    FMT_PCT, FMT_NUM2, FMT_NUM3, FMT_NUM4, FMT_DATE, FMT_MONEY, FMT_INT,
    style_header_row, write_table, auto_width, set_tab_color,
    add_correlation_coloring,
)
from .formulas import (
    sheet_ref, sheet_range,
    f_ann_mean, f_ann_vol, f_skew, f_kurt, f_max, f_min, f_count,
    f_correl, f_covariance, f_sharpe, f_averageif, f_countif,
    f_log_return, add_definition,
)


# ── Helper Functions ─────────────────────────────────────────────────────────
def _safe_round(val, decimals=2):
    """Round safely, returning None for NaN."""
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return None
    return round(float(val), decimals)


def _safe_float(val):
    """Convert to float safely."""
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return None
    return float(val)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — MARKET DATA HUB
# ═══════════════════════════════════════════════════════════════════════════════
def build_tab_01(wb, data, results):
    """Central data sheet.  All other tabs reference this tab via cell refs."""
    ws = wb.create_sheet(title=TAB_NAMES[1])
    set_tab_color(ws, TAB_COLORS["green"])

    master = data["master"]
    log_ret = data["log_returns"]
    diffs = data["diffs"]

    # ── Section A: Daily Price Data ─────────────────────────────────────
    ws.merge_cells("A1:M1")
    ws["A1"] = "SECTION A — DAILY PRICE DATA"
    ws["A1"].font = FONT_TITLE

    # Definition row
    def_row = add_definition(ws, 2, 1,
                             "Daily Price Data",
                             "Adjusted closing prices for all 10 securities + WTI + Brent. Source: Yahoo Finance / FRED.")

    price_cols = ALL_TICKERS + ["WTI", "Brent"]
    available_price = [c for c in price_cols if c in master.columns]

    headers_a = ["Date"] + available_price
    row = 3
    for j, h in enumerate(headers_a):
        cell = ws.cell(row=row, column=j + 1, value=h)
        cell.font = FONT_HEADER
        cell.fill = FILL_HEADER
        cell.border = BOTTOM_BORDER

    for i, (dt, series) in enumerate(master.iterrows()):
        r = row + 1 + i
        ws.cell(row=r, column=1, value=dt.date()).number_format = FMT_DATE
        for j, col in enumerate(available_price):
            val = series.get(col, None)
            if pd.notna(val):
                ws.cell(row=r, column=j + 2, value=round(float(val), 4))
    data_end_row = row + len(master)

    # Build price column letter mapping
    _price_col_letters = {}
    for j, col in enumerate(available_price):
        _price_col_letters[col] = get_column_letter(j + 2)  # prices start at column B

    # ── Section B: Daily Log Returns ────────────────────────────────────
    ret_start_col = len(available_price) + 3  # skip a column
    ws.cell(row=2, column=ret_start_col, value="SECTION B — DAILY LOG RETURNS").font = FONT_TITLE
    ret_cols = [c for c in log_ret.columns if c in price_cols or c in ALL_TICKERS + ["SPY"]]
    headers_b = ["Date"] + [f"r_{c}" for c in ret_cols]
    for j, h in enumerate(headers_b):
        cell = ws.cell(row=row, column=ret_start_col + j, value=h)
        cell.font = FONT_HEADER
        cell.fill = FILL_HEADER
        cell.border = BOTTOM_BORDER

    for i, (dt, series) in enumerate(log_ret.iterrows()):
        r = row + 1 + i
        ws.cell(row=r, column=ret_start_col, value=dt.date()).number_format = FMT_DATE
        for j, col in enumerate(ret_cols):
            ret_cell_col = get_column_letter(ret_start_col + 1 + j)
            # Use Excel LN formula referencing Section A price data
            if col in _price_col_letters and r > row + 1:
                price_letter = _price_col_letters[col]
                formula = f_log_return(f"{price_letter}{r}", f"{price_letter}{r-1}")
                c = ws.cell(row=r, column=ret_start_col + 1 + j, value=formula)
                c.number_format = FMT_NUM4
            else:
                # Fallback for SPY or first row: paste value
                val = series.get(col, None)
                if pd.notna(val):
                    c = ws.cell(row=r, column=ret_start_col + 1 + j, value=round(float(val), 6))
                    c.number_format = FMT_NUM4

    # ── Section C: Macro Indicators ─────────────────────────────────────
    macro_cols_map = {
        "VIX": "VIX", "OVX": "OVX", "MOVE": "MOVE",
        "Brent_WTI_Spread": "Brent_WTI_Spread",
        "HenryHub": "HenryHub", "TTF": "TTF",
        "TTF_HH_Spread": "TTF_HH_Spread",
        "FedFunds": "FedFunds", "DGS2": "DGS2", "DGS10": "DGS10",
        "Spread_2s10s": "Spread_2s10s", "T10YIE": "T10YIE",
        "DXY": "DXY", "Gold": "Gold",
        "CPI": "CPI", "IndProd": "IndProd", "UMich": "UMich",
        "CPI_Energy": "CPI Energy",
        "Claims": "Init Jobless Claims",
    }
    macro_start_col = ret_start_col + len(headers_b) + 2
    ws.cell(row=2, column=macro_start_col, value="SECTION C — MACRO INDICATORS").font = FONT_TITLE
    macro_avail = [(label, col) for label, col in macro_cols_map.items() if col in master.columns]
    headers_c = ["Date"] + [m[0] for m in macro_avail]
    for j, h in enumerate(headers_c):
        cell = ws.cell(row=row, column=macro_start_col + j, value=h)
        cell.font = FONT_HEADER
        cell.fill = FILL_HEADER

    # Build macro column letter mapping for formula-based computed columns
    _macro_col_positions = {}
    for j, (label, col) in enumerate(macro_avail):
        _macro_col_positions[label] = get_column_letter(macro_start_col + 1 + j)

    # Identify price columns for Brent and WTI in Section A
    _brent_price_letter = _price_col_letters.get("Brent")
    _wti_price_letter = _price_col_letters.get("WTI")

    for i, (dt, series) in enumerate(master.iterrows()):
        r = row + 1 + i
        ws.cell(row=r, column=macro_start_col, value=dt.date()).number_format = FMT_DATE
        for j, (label, col) in enumerate(macro_avail):
            target_col = macro_start_col + 1 + j
            # Use Excel formulas for computed spread columns
            if label == "Brent_WTI_Spread" and _brent_price_letter and _wti_price_letter:
                ws.cell(row=r, column=target_col,
                        value=f'=IF(AND({_brent_price_letter}{r}<>"",{_wti_price_letter}{r}<>""),{_brent_price_letter}{r}-{_wti_price_letter}{r},"")')
            elif label == "TTF_HH_Spread" and "TTF" in _macro_col_positions and "HenryHub" in _macro_col_positions:
                ttf_l = _macro_col_positions["TTF"]
                hh_l = _macro_col_positions["HenryHub"]
                ws.cell(row=r, column=target_col,
                        value=f'=IF(AND({ttf_l}{r}<>"",{hh_l}{r}<>""),{ttf_l}{r}-{hh_l}{r},"")')
            elif label == "Spread_2s10s" and "DGS10" in _macro_col_positions and "DGS2" in _macro_col_positions:
                d10_l = _macro_col_positions["DGS10"]
                d2_l = _macro_col_positions["DGS2"]
                ws.cell(row=r, column=target_col,
                        value=f'=IF(AND({d10_l}{r}<>"",{d2_l}{r}<>""),{d10_l}{r}-{d2_l}{r},"")')
            else:
                # Raw data: paste value
                val = series.get(col, None)
                if pd.notna(val):
                    ws.cell(row=r, column=target_col, value=round(float(val), 4))

    # ── Section D: Regime Flags ─────────────────────────────────────────
    flag_start_col = macro_start_col + len(headers_c) + 2
    ws.cell(row=2, column=flag_start_col, value="SECTION D — REGIME FLAGS").font = FONT_TITLE
    flag_headers = ["Date", "OVX_Stress", "VIX_Stress", "Conflict_Period"]
    for j, h in enumerate(flag_headers):
        cell = ws.cell(row=row, column=flag_start_col + j, value=h)
        cell.font = FONT_HEADER
        cell.fill = FILL_HEADER

    for i, (dt, series) in enumerate(master.iterrows()):
        r = row + 1 + i
        ws.cell(row=r, column=flag_start_col, value=dt.date()).number_format = FMT_DATE
        ws.cell(row=r, column=flag_start_col + 1, value=int(series.get("OVX_Stress", 0)))
        ws.cell(row=r, column=flag_start_col + 2, value=int(series.get("VIX_Stress", 0)))
        ws.cell(row=r, column=flag_start_col + 3, value=int(series.get("Conflict_Period", 0)))

    # ── Section E: Event Windows ────────────────────────────────────────
    ev_start_col = flag_start_col + len(flag_headers) + 2
    ws.cell(row=2, column=ev_start_col, value="SECTION E — EVENT WINDOWS").font = FONT_TITLE
    ev_headers = ["Date", "Event_Label", "Event_ID"]
    for j, h in enumerate(ev_headers):
        cell = ws.cell(row=row, column=ev_start_col + j, value=h)
        cell.font = FONT_HEADER
        cell.fill = FILL_HEADER

    # Store event_id column letter for downstream formula references
    event_id_col_letter = get_column_letter(ev_start_col + 2)

    for i, (dt, series) in enumerate(master.iterrows()):
        r = row + 1 + i
        ws.cell(row=r, column=ev_start_col, value=dt.date()).number_format = FMT_DATE
        ws.cell(row=r, column=ev_start_col + 1, value=series.get("Event_Label", ""))
        ws.cell(row=r, column=ev_start_col + 2, value=int(series.get("Event_ID", 0)))

    ws.column_dimensions["A"].width = 12
    ws.freeze_panes = "B4"
    results["data_end_row"] = data_end_row

    # Store column positions for other tabs to reference via Excel formulas
    tab1_name = TAB_NAMES[1]
    _ret_col_map = {}
    for j, col in enumerate(ret_cols):
        _ret_col_map[col] = get_column_letter(ret_start_col + 1 + j)
    results["tab1_ret_col_map"] = _ret_col_map
    results["tab1_ret_start_row"] = row + 1  # first data row (row + 1)
    results["tab1_ret_end_row"] = data_end_row
    results["tab1_name"] = tab1_name

    # NEW: Additional metadata for downstream tabs
    results["tab1_price_col_map"] = _price_col_letters
    results["tab1_macro_col_map"] = _macro_col_positions
    results["tab1_event_id_col"] = event_id_col_letter
    results["tab1_last_data_row"] = data_end_row

    return results


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — MACRO REGIME DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
def build_tab_02(wb, data, results):
    ws = wb.create_sheet(title=TAB_NAMES[2])
    set_tab_color(ws, TAB_COLORS["green"])

    master = data["master"]
    log_ret = data["log_returns"]

    # ── Classify regimes (Python — too complex for single Excel formula) ─
    vix = master.get("VIX", pd.Series(dtype=float))
    ovx = master.get("OVX", pd.Series(dtype=float))
    s2s10 = master.get("Spread_2s10s", pd.Series(dtype=float))
    wti = master.get("WTI", pd.Series(dtype=float))
    bev = master.get("T10YIE", pd.Series(dtype=float))
    bws = master.get("Brent_WTI_Spread", pd.Series(dtype=float))
    # FIX #9: Add consumer sentiment for Regime 4 check
    umich = master.get("UMich", pd.Series(dtype=float))
    # FIX #13: Add Industrial Production for Regime 1 check
    indprod = master.get("IndProd", pd.Series(dtype=float))

    regime = pd.Series(0, index=master.index, name="Regime")

    # Expanding percentiles
    ovx_90 = ovx.expanding(min_periods=60).quantile(0.9)
    wti_80 = wti.expanding(min_periods=60).quantile(0.8)
    # FIX #9: Track sentiment peak for decline check
    umich_peak = umich.expanding(min_periods=60).max()
    # FIX #13: IP growth (month-over-month pct change, forward-filled to daily)
    ip_changed = indprod != indprod.shift(1)
    ip_growth_raw = indprod.pct_change()
    ip_growth = ip_growth_raw.where(ip_changed).ffill().fillna(0)

    for dt in master.index:
        v = vix.get(dt, np.nan)
        o = ovx.get(dt, np.nan)
        sp = s2s10.get(dt, np.nan)
        w = wti.get(dt, np.nan)
        be = bev.get(dt, np.nan)
        bw = bws.get(dt, np.nan)

        # Regime 3: Geopolitical Crisis
        if pd.notna(o) and pd.notna(ovx_90.get(dt)):
            if o > ovx_90[dt]:
                regime[dt] = 3
                continue
        if pd.notna(v) and pd.notna(bw) and v > 30 and bw > 5:
            regime[dt] = 3
            continue
        # FIX #9: Regime 4 — requires consumer sentiment decline > 10% from peak
        um_val = umich.get(dt, np.nan)
        um_pk = umich_peak.get(dt, np.nan)
        sentiment_declined = (pd.notna(um_val) and pd.notna(um_pk)
                              and um_pk > 0 and (um_pk - um_val) / um_pk > 0.10)
        if pd.notna(sp) and pd.notna(v) and sp < 0 and v > 25 and sentiment_declined:
            regime[dt] = 4
            continue
        # Regime 2: Inflation Shock
        if pd.notna(w) and pd.notna(wti_80.get(dt)) and pd.notna(be) and pd.notna(v):
            if w > wti_80[dt] and be > 2.5 and v < 30:
                regime[dt] = 2
                continue
        # FIX #13: Regime 1 — requires IP growth > 0
        ip_g = ip_growth.get(dt, np.nan)
        ip_ok = pd.notna(ip_g) and ip_g > 0
        if pd.notna(v) and pd.notna(o) and pd.notna(sp):
            if v < 20 and o < 30 and sp > 0 and ip_ok:
                regime[dt] = 1
                continue

    data["master"]["Regime"] = regime
    results["regime"] = regime

    # ── Write to sheet ──────────────────────────────────────────────────
    ws["A1"] = "MACRO REGIME DASHBOARD"
    ws["A1"].font = FONT_TITLE

    # Definition row
    add_definition(ws, 2, 1,
                   "Regime Classification",
                   "Each trading day classified by severity: Crisis > Recession > Inflation > Growth. Regime 0 = Transition (unclassified).")

    headers = ["Date", "Regime ID", "Regime Name", "VIX", "OVX", "2s10s", "WTI"]
    for j, h in enumerate(headers):
        cell = ws.cell(row=3, column=j + 1, value=h)
        cell.font = FONT_HEADER
        cell.fill = FILL_HEADER

    regime_col_letter = get_column_letter(2)  # column B = Regime ID
    regime_start_row = 4

    for i, dt in enumerate(master.index):
        r = 4 + i
        rid = int(regime[dt])
        ws.cell(row=r, column=1, value=dt.date()).number_format = FMT_DATE
        ws.cell(row=r, column=2, value=rid)
        ws.cell(row=r, column=3, value=REGIME_NAMES.get(rid, "Unknown"))
        ws.cell(row=r, column=4, value=_safe_round(vix.get(dt), 2))
        ws.cell(row=r, column=5, value=_safe_round(ovx.get(dt), 2))
        ws.cell(row=r, column=6, value=_safe_round(s2s10.get(dt), 3))
        ws.cell(row=r, column=7, value=_safe_round(wti.get(dt), 2))

    regime_data_end = 4 + len(master) - 1  # last data row (inclusive)

    # Store regime metadata for downstream tabs
    tab2_name = TAB_NAMES[2]
    results["tab2_name"] = tab2_name
    results["tab2_regime_col"] = regime_col_letter
    results["tab2_regime_start_row"] = regime_start_row
    results["tab2_regime_end_row"] = regime_data_end

    # ── Regime Statistics Table (EXCEL FORMULA-BASED) ────────────────────
    stats_row = regime_data_end + 4
    ws.cell(row=stats_row, column=1, value="REGIME STATISTICS").font = FONT_SUBTITLE

    # Definition for the table
    add_definition(ws, stats_row + 1, 1,
                   "Regime Statistics",
                   "All values computed via COUNTIF/AVERAGEIF formulas referencing the regime column above and Tab 1 return data.")
    stats_row += 3

    stat_headers = ["Regime", "% of Days", "Mean WTI Ret (ann)"]
    for t in ALL_TICKERS:
        stat_headers.append(f"Mean {t} Ret (ann)")
    stat_headers += ["Mean VIX", "Mean OVX"]
    for j, h in enumerate(stat_headers):
        ws.cell(row=stats_row, column=j + 1, value=h).font = FONT_HEADER
        ws.cell(row=stats_row, column=j + 1).fill = FILL_HEADER

    # Build range references
    regime_range = f"{regime_col_letter}{regime_start_row}:{regime_col_letter}{regime_data_end}"

    # Tab 1 references for return data
    tab1_name = results.get("tab1_name", TAB_NAMES[1])
    ret_col_map = results.get("tab1_ret_col_map", {})
    dr_start = results.get("tab1_ret_start_row", 5)
    dr_end = results.get("tab1_ret_end_row", 1000)

    # Tab 2 local VIX/OVX column letters (columns D and E)
    vix_col_letter = get_column_letter(4)
    ovx_col_letter = get_column_letter(5)
    vix_range = f"{vix_col_letter}{regime_start_row}:{vix_col_letter}{regime_data_end}"
    ovx_range = f"{ovx_col_letter}{regime_start_row}:{ovx_col_letter}{regime_data_end}"

    for idx, (rid, rname) in enumerate(REGIME_NAMES.items()):
        r = stats_row + 1 + idx
        ws.cell(row=r, column=1, value=f"{rid}: {rname}")

        # % of Days = COUNTIF(regime_range, rid) / COUNT(regime_range)
        ws.cell(row=r, column=2,
                value=f"=COUNTIF({regime_range},{rid})/COUNT({regime_range})")
        ws.cell(row=r, column=2).number_format = FMT_PCT

        # Mean WTI Return (ann) = AVERAGEIF(regime_range, rid, wti_return_range) * 252
        wti_ret_col = ret_col_map.get("WTI")
        if wti_ret_col:
            wti_ret_range = sheet_range(tab1_name, wti_ret_col, dr_start, dr_end)
            ws.cell(row=r, column=3,
                    value=f"=AVERAGEIF({regime_range},{rid},{wti_ret_range})*252")
            ws.cell(row=r, column=3).number_format = FMT_PCT

        # Mean stock returns (ann) via AVERAGEIF
        col_offset = 4
        for t in ALL_TICKERS:
            stock_ret_col = ret_col_map.get(t)
            if stock_ret_col:
                stock_ret_range = sheet_range(tab1_name, stock_ret_col, dr_start, dr_end)
                ws.cell(row=r, column=col_offset,
                        value=f"=AVERAGEIF({regime_range},{rid},{stock_ret_range})*252")
                ws.cell(row=r, column=col_offset).number_format = FMT_PCT
            col_offset += 1

        # Mean VIX = AVERAGEIF(regime_range, rid, vix_range)
        ws.cell(row=r, column=col_offset,
                value=f"=AVERAGEIF({regime_range},{rid},{vix_range})")
        ws.cell(row=r, column=col_offset).number_format = FMT_NUM2

        # Mean OVX = AVERAGEIF(regime_range, rid, ovx_range)
        ws.cell(row=r, column=col_offset + 1,
                value=f"=AVERAGEIF({regime_range},{rid},{ovx_range})")
        ws.cell(row=r, column=col_offset + 1).number_format = FMT_NUM2

    # ── Regime Transition Matrix ─────────────────────────────────────────
    tm_row = stats_row + 1 + len(REGIME_NAMES) + 3
    ws.cell(row=tm_row, column=1, value="REGIME TRANSITION MATRIX").font = FONT_SUBTITLE
    regime_ids = [0, 1, 2, 3, 4]
    tm_headers = ["From \\ To"] + [REGIME_NAMES.get(r, str(r)) for r in regime_ids]
    for j, h in enumerate(tm_headers):
        ws.cell(row=tm_row + 1, column=j + 1, value=h).font = FONT_HEADER

    regime_arr = regime.values
    for i_idx, ri in enumerate(regime_ids):
        ws.cell(row=tm_row + 2 + i_idx, column=1, value=REGIME_NAMES.get(ri, str(ri)))
        from_mask = np.where(regime_arr[:-1] == ri)[0]
        n_from = len(from_mask)
        for j_idx, rj in enumerate(regime_ids):
            if n_from > 0:
                to_mask = np.sum(regime_arr[from_mask + 1] == rj)
                prob = to_mask / n_from
            else:
                prob = 0
            ws.cell(row=tm_row + 2 + i_idx, column=2 + j_idx, value=prob).number_format = FMT_NUM3

    auto_width(ws)
    return results


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — COMPANY PROFILES & FUNDAMENTAL SNAPSHOT
# ═══════════════════════════════════════════════════════════════════════════════
def build_tab_03(wb, data, results):
    ws = wb.create_sheet(title=TAB_NAMES[3])
    set_tab_color(ws, TAB_COLORS["green"])

    ws["A1"] = "COMPANY PROFILES & FUNDAMENTAL SNAPSHOT"
    ws["A1"].font = FONT_TITLE

    # Tab 1 references for current price formula
    tab1_name = results.get("tab1_name", TAB_NAMES[1])
    price_col_map = results.get("tab1_price_col_map", {})
    last_data_row = results.get("tab1_last_data_row", results.get("data_end_row", 1000))

    # ── Profile Blocks ──────────────────────────────────────────────────
    row_offset = 3
    FMT_MONEY_B = '$#,##0.0,,,"B"'
    fields = [
        ("Company Name", "name", None),
        ("Subsector", "subsector", None),
        ("Market Cap", "mkt_cap", FMT_MONEY_B),
        ("Enterprise Value", "ev", FMT_MONEY_B),
        ("FY2025 Revenue", "revenue", FMT_MONEY_B),
        ("FY2025 EBITDA", "ebitda", FMT_MONEY_B),
        ("FY2025 Net Income", "net_income", FMT_MONEY_B),
        ("FY2025 EPS", "eps", FMT_MONEY),
        ("P/E (TTM)", "pe", FMT_NUM2),
        ("EV/EBITDA", "ev_ebitda", FMT_NUM2),
        ("Dividend Yield", "div_yield", FMT_PCT),
        ("Net Debt / EBITDA", "net_debt_ebitda", '0.0x'),
        ("FCF Yield", "fcf_yield", FMT_PCT),
        ("Production", "production", None),
    ]

    # Track row positions for oil beta / geo sensitivity per ticker
    beta_row_map = {}

    for ticker in ALL_TICKERS:
        fd = FUNDAMENTALS.get(ticker, {})
        ws.cell(row=row_offset, column=1, value=f"{ticker} — {fd.get('name', ticker)}").font = FONT_SUBTITLE
        ws.cell(row=row_offset, column=1).fill = FILL_HEADER
        ws.cell(row=row_offset, column=2).fill = FILL_HEADER
        ws.cell(row=row_offset, column=3).fill = FILL_HEADER
        row_offset += 1

        for field_label, field_key, fmt in fields:
            ws.cell(row=row_offset, column=1, value=field_label).font = FONT_NORMAL
            val = fd.get(field_key)
            if val is not None:
                c = ws.cell(row=row_offset, column=2, value=val)
                if fmt:
                    c.number_format = fmt
            row_offset += 1

        # NEW: Current Price — formula referencing Tab 1 last row
        ws.cell(row=row_offset, column=1, value="Current Price (latest)").font = FONT_NORMAL
        price_col = price_col_map.get(ticker)
        if price_col:
            ws.cell(row=row_offset, column=2,
                    value=f"='{tab1_name}'!{price_col}{last_data_row}")
            ws.cell(row=row_offset, column=2).number_format = FMT_MONEY
        row_offset += 1

        # NEW: Oil Beta placeholder — to be populated by Tab 6
        ws.cell(row=row_offset, column=1, value="Oil Beta (from Tab 6)").font = FONT_NORMAL
        ws.cell(row=row_offset, column=2, value="(see Tab 06_Regression)").font = FONT_NORMAL
        beta_row_map[ticker] = {"oil_beta_row": row_offset, "oil_beta_col": 2}
        row_offset += 1

        # NEW: Geopolitical Sensitivity placeholder
        ws.cell(row=row_offset, column=1, value="Geopolitical Sensitivity").font = FONT_NORMAL
        ws.cell(row=row_offset, column=2, value="(see Tab 06_Regression)").font = FONT_NORMAL
        beta_row_map[ticker]["geo_sens_row"] = row_offset
        beta_row_map[ticker]["geo_sens_col"] = 2
        row_offset += 1

        row_offset += 1  # spacer

    # Store beta row map so Tab 6 can write back
    results["tab3_beta_row_map"] = beta_row_map

    # Note about linked data
    ws.cell(row=row_offset, column=1,
            value="NOTE: Oil Beta and Geopolitical Sensitivity will be populated by Tab 6 regression results.").font = FONT_NORMAL
    row_offset += 2

    # ── Comparative Valuation Table ──────────────────────────────────────
    ws.cell(row=row_offset, column=1, value="COMPARATIVE VALUATION").font = FONT_SUBTITLE
    row_offset += 1
    val_headers = ["Ticker", "P/E", "EV/EBITDA", "FCF Yield", "Div Yield", "Net Debt/EBITDA"]
    for j, h in enumerate(val_headers):
        ws.cell(row=row_offset, column=j + 1, value=h).font = FONT_HEADER
        ws.cell(row=row_offset, column=j + 1).fill = FILL_HEADER
    row_offset += 1

    for ticker in EQUITY_TICKERS:
        fd = FUNDAMENTALS.get(ticker, {})
        ws.cell(row=row_offset, column=1, value=ticker)
        ws.cell(row=row_offset, column=2, value=fd.get("pe")).number_format = FMT_NUM2
        ws.cell(row=row_offset, column=3, value=fd.get("ev_ebitda")).number_format = FMT_NUM2
        ws.cell(row=row_offset, column=4, value=fd.get("fcf_yield")).number_format = FMT_PCT
        ws.cell(row=row_offset, column=5, value=fd.get("div_yield")).number_format = FMT_PCT
        ws.cell(row=row_offset, column=6, value=fd.get("net_debt_ebitda")).number_format = '0.0x'
        row_offset += 1

    # ── Comparative Valuation Bar Chart ──────────────────────────────────
    chart_start_row = row_offset - len(EQUITY_TICKERS) - 1
    chart = BarChart()
    chart.type = "col"
    chart.grouping = "clustered"
    chart.title = "Comparative Valuation Multiples"
    chart.y_axis.title = "Value"
    chart.x_axis.title = "Ticker"
    data_ref = Reference(ws, min_col=2, max_col=4,
                         min_row=chart_start_row, max_row=chart_start_row + len(EQUITY_TICKERS))
    cats = Reference(ws, min_col=1, min_row=chart_start_row + 1,
                     max_row=chart_start_row + len(EQUITY_TICKERS))
    chart.add_data(data_ref, titles_from_data=True)
    chart.set_categories(cats)
    chart.width = 25
    chart.height = 15
    ws.add_chart(chart, f"H{chart_start_row}")

    auto_width(ws)
    return results


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4 — HISTORICAL PERFORMANCE ANALYTICS
# ═══════════════════════════════════════════════════════════════════════════════
def build_tab_04(wb, data, results):
    ws = wb.create_sheet(title=TAB_NAMES[4])
    set_tab_color(ws, TAB_COLORS["blue"])

    log_ret = data["log_returns"]
    master = data["master"]

    ws["A1"] = "HISTORICAL PERFORMANCE ANALYTICS"
    ws["A1"].font = FONT_TITLE

    # ── Section A: Full-Period Descriptive Statistics ────────────────────
    ws["A3"] = "SECTION A — FULL-PERIOD DESCRIPTIVE STATISTICS"
    ws["A3"].font = FONT_SUBTITLE

    # Definition
    add_definition(ws, 4, 1,
                   "Descriptive Statistics",
                   "Annualized mean = AVERAGE(daily log returns) * 252. Annualized vol = STDEV.S * SQRT(252). Sharpe = (AnnMean - Rf) / AnnVol.")

    stat_headers = [
        "Ticker", "N", "Ann Mean Ret", "Ann Volatility", "Skewness",
        "Excess Kurtosis", "Max Daily Ret", "Min Daily Ret",
        "Max Drawdown", "Sharpe Ratio", "Sortino Ratio", "Calmar Ratio",
    ]
    hdr_row = 6
    for j, h in enumerate(stat_headers):
        ws.cell(row=hdr_row, column=j + 1, value=h).font = FONT_HEADER
        ws.cell(row=hdr_row, column=j + 1).fill = FILL_HEADER

    # Use Excel formulas referencing Tab 1 log return data
    tab1_name = results.get("tab1_name", TAB_NAMES[1])
    ret_col_map = results.get("tab1_ret_col_map", {})
    dr_start = results.get("tab1_ret_start_row", 5)
    dr_end = results.get("tab1_ret_end_row", 1000)
    rf_rate = RF_RATE

    stats_dict = {}
    for idx, ticker in enumerate(ALL_TICKERS):
        r = hdr_row + 1 + idx
        ws.cell(row=r, column=1, value=ticker)

        rets = log_ret.get(ticker, pd.Series(dtype=float)).dropna()
        n = len(rets)
        ws.cell(row=r, column=2, value=n)
        if n < 5:
            continue

        col_letter = ret_col_map.get(ticker)
        if col_letter:
            rng = sheet_range(tab1_name, col_letter, dr_start, dr_end)
            # Ann Mean Return
            ws.cell(row=r, column=3, value=f_ann_mean(rng))
            ws.cell(row=r, column=3).number_format = FMT_PCT
            # Ann Volatility
            ws.cell(row=r, column=4, value=f_ann_vol(rng))
            ws.cell(row=r, column=4).number_format = FMT_PCT
            # Skewness
            ws.cell(row=r, column=5, value=f_skew(rng))
            ws.cell(row=r, column=5).number_format = FMT_NUM3
            # Excess Kurtosis
            ws.cell(row=r, column=6, value=f_kurt(rng))
            ws.cell(row=r, column=6).number_format = FMT_NUM3
            # Max Daily Return
            ws.cell(row=r, column=7, value=f_max(rng))
            ws.cell(row=r, column=7).number_format = FMT_PCT
            # Min Daily Return
            ws.cell(row=r, column=8, value=f_min(rng))
            ws.cell(row=r, column=8).number_format = FMT_PCT
        else:
            # Fallback: paste computed values for tickers not in Tab 1
            ann_mean = float(rets.mean() * 252)
            ann_vol = float(rets.std() * np.sqrt(252))
            for j, val in enumerate([ann_mean, ann_vol, float(rets.skew()),
                                     float(rets.kurtosis()), float(rets.max()), float(rets.min())]):
                c = ws.cell(row=r, column=3 + j, value=val)
                c.number_format = FMT_PCT if j in (0, 1, 4, 5) else FMT_NUM3

        # Max Drawdown, Sortino, Calmar — computed in Python
        # (drawdown requires running max which is impractical in Excel)
        ann_mean = float(rets.mean() * 252)
        ann_vol = float(rets.std() * np.sqrt(252))
        cum = np.exp(rets.cumsum())
        running_max = cum.cummax()
        dd = (cum - running_max) / running_max
        max_dd = float(dd.min())

        target_ret = rf_rate / 252
        downside_diffs = np.minimum(rets.values - target_ret, 0)
        down_vol = float(np.sqrt(np.mean(downside_diffs ** 2)) * np.sqrt(252)) if n > 1 else ann_vol

        sortino = (ann_mean - rf_rate) / down_vol if down_vol > 0 else 0
        calmar = ann_mean / abs(max_dd) if max_dd != 0 else 0

        ws.cell(row=r, column=9, value=max_dd).number_format = FMT_PCT

        if col_letter:
            # Sharpe = (C{r} - Rf) / D{r} -- formula referencing formula cells
            ws.cell(row=r, column=10, value=f_sharpe(f"C{r}", f"D{r}", rf_rate))
            ws.cell(row=r, column=10).number_format = FMT_NUM2
        else:
            sharpe = (ann_mean - rf_rate) / ann_vol if ann_vol > 0 else 0
            ws.cell(row=r, column=10, value=sharpe).number_format = FMT_NUM2

        ws.cell(row=r, column=11, value=sortino).number_format = FMT_NUM2
        ws.cell(row=r, column=12, value=calmar).number_format = FMT_NUM2

        stats_dict[ticker] = {
            "ann_mean": ann_mean, "ann_vol": ann_vol,
            "sharpe": (ann_mean - rf_rate) / ann_vol if ann_vol > 0 else 0,
            "max_dd": max_dd, "skew": float(rets.skew()), "kurt": float(rets.kurtosis()),
            "down_vol": down_vol,
        }

    results["full_stats"] = stats_dict

    # ── Section B: Event-Window Statistics (AVERAGEIFS formulas) ─────────
    ew_row = hdr_row + 1 + len(ALL_TICKERS) + 3
    ws.cell(row=ew_row, column=1, value="SECTION B — EVENT-WINDOW STATISTICS").font = FONT_SUBTITLE
    ew_row += 1

    # Definition
    add_definition(ws, ew_row, 1,
                   "Event-Window Stats",
                   "Ann Mean Return and Ann Volatility use AVERAGEIFS/STDEV formulas referencing Tab 1 event IDs. "
                   "Skewness, Kurtosis, Max, Min, Drawdown, Sortino, Calmar remain Python-computed (complex conditionals).")
    ew_row += 2

    # Tab 1 event ID column reference
    tab1_event_col = results.get("tab1_event_id_col")

    for eid, (label, sdt, edt) in EVENT_WINDOWS.items():
        ws.cell(row=ew_row, column=1, value=f"Event {eid}: {label} ({sdt} to {edt})").font = FONT_SUBTITLE
        ew_row += 1
        ew_headers = [
            "Ticker", "N", "Ann Mean Ret", "Ann Volatility", "Sharpe",
            "Skewness", "Excess Kurtosis", "Max Daily Ret", "Min Daily Ret",
            "Max Drawdown", "Sortino Ratio", "Calmar Ratio",
        ]
        for j, h in enumerate(ew_headers):
            ws.cell(row=ew_row, column=j + 1, value=h).font = FONT_HEADER
            ws.cell(row=ew_row, column=j + 1).fill = FILL_HEADER
        ew_row += 1

        mask = (master.index >= sdt) & (master.index <= edt)
        for ticker in ALL_TICKERS:
            rets = log_ret.get(ticker, pd.Series(dtype=float))
            ev_rets = rets[mask].dropna()
            n = len(ev_rets)
            ws.cell(row=ew_row, column=1, value=ticker)
            ws.cell(row=ew_row, column=2, value=n)

            col_letter = ret_col_map.get(ticker)

            if n > 2 and col_letter and tab1_event_col:
                # AVERAGEIFS formula for Ann Mean Return
                ret_range = sheet_range(tab1_name, col_letter, dr_start, dr_end)
                ev_range = sheet_range(tab1_name, tab1_event_col, dr_start, dr_end)
                ws.cell(row=ew_row, column=3,
                        value=f"=AVERAGEIFS({ret_range},{ev_range},{eid})*252")
                ws.cell(row=ew_row, column=3).number_format = FMT_PCT

                # Ann Volatility — no simple single-cell STDEV with IF for AVERAGEIFS,
                # but we can approximate with an array-style approach.
                # Use Python-computed value for robustness.
                av = float(ev_rets.std() * np.sqrt(252))
                ws.cell(row=ew_row, column=4, value=av).number_format = FMT_PCT

                # Sharpe = (C{ew_row} - Rf) / D{ew_row}
                ws.cell(row=ew_row, column=5,
                        value=f_sharpe(f"C{ew_row}", f"D{ew_row}", rf_rate))
                ws.cell(row=ew_row, column=5).number_format = FMT_NUM2

                # Skewness, Kurtosis, Max, Min: keep Python (complex conditionals)
                ws.cell(row=ew_row, column=6, value=float(ev_rets.skew())).number_format = FMT_NUM3
                ws.cell(row=ew_row, column=7, value=float(ev_rets.kurtosis())).number_format = FMT_NUM3
                ws.cell(row=ew_row, column=8, value=float(ev_rets.max())).number_format = FMT_PCT
                ws.cell(row=ew_row, column=9, value=float(ev_rets.min())).number_format = FMT_PCT

                # Max Drawdown (Python)
                cum = np.exp(ev_rets.cumsum())
                running_max = cum.cummax()
                dd = (cum - running_max) / running_max
                max_dd = float(dd.min())
                ws.cell(row=ew_row, column=10, value=max_dd).number_format = FMT_PCT

                # Sortino (Python)
                am = float(ev_rets.mean() * 252)
                target_ret_daily = RF_RATE / 252
                downside_diffs = np.minimum(ev_rets.values - target_ret_daily, 0)
                down_vol = float(np.sqrt(np.mean(downside_diffs ** 2)) * np.sqrt(252)) if n > 1 else av
                sortino = (am - RF_RATE) / down_vol if down_vol > 0 else 0
                ws.cell(row=ew_row, column=11, value=sortino).number_format = FMT_NUM2

                # Calmar (Python)
                calmar = am / abs(max_dd) if max_dd != 0 else 0
                ws.cell(row=ew_row, column=12, value=calmar).number_format = FMT_NUM2

            elif n > 2:
                # Fallback: all Python-computed
                am = float(ev_rets.mean() * 252)
                av = float(ev_rets.std() * np.sqrt(252))
                sh = (am - RF_RATE) / av if av > 0 else 0
                skew = float(ev_rets.skew())
                kurt = float(ev_rets.kurtosis())
                max_ret = float(ev_rets.max())
                min_ret = float(ev_rets.min())
                cum = np.exp(ev_rets.cumsum())
                running_max = cum.cummax()
                dd = (cum - running_max) / running_max
                max_dd = float(dd.min())
                target_ret_daily = RF_RATE / 252
                downside_diffs = np.minimum(ev_rets.values - target_ret_daily, 0)
                down_vol = float(np.sqrt(np.mean(downside_diffs ** 2)) * np.sqrt(252)) if n > 1 else av
                sortino = (am - RF_RATE) / down_vol if down_vol > 0 else 0
                calmar = am / abs(max_dd) if max_dd != 0 else 0

                ws.cell(row=ew_row, column=3, value=am).number_format = FMT_PCT
                ws.cell(row=ew_row, column=4, value=av).number_format = FMT_PCT
                ws.cell(row=ew_row, column=5, value=sh).number_format = FMT_NUM2
                ws.cell(row=ew_row, column=6, value=skew).number_format = FMT_NUM3
                ws.cell(row=ew_row, column=7, value=kurt).number_format = FMT_NUM3
                ws.cell(row=ew_row, column=8, value=max_ret).number_format = FMT_PCT
                ws.cell(row=ew_row, column=9, value=min_ret).number_format = FMT_PCT
                ws.cell(row=ew_row, column=10, value=max_dd).number_format = FMT_PCT
                ws.cell(row=ew_row, column=11, value=sortino).number_format = FMT_NUM2
                ws.cell(row=ew_row, column=12, value=calmar).number_format = FMT_NUM2
            ew_row += 1
        ew_row += 1

    # ── Section C: Cumulative Return Chart ──────────────────────────────
    cr_row = ew_row + 2
    ws.cell(row=cr_row, column=1, value="SECTION C — CUMULATIVE LOG RETURNS (Indexed to 100)").font = FONT_SUBTITLE
    cr_row += 1
    cr_headers = ["Date"] + list(ALL_TICKERS)
    for j, h in enumerate(cr_headers):
        ws.cell(row=cr_row, column=j + 1, value=h).font = FONT_HEADER
        ws.cell(row=cr_row, column=j + 1).fill = FILL_HEADER
    cr_row += 1
    cr_start = cr_row

    # Cumulative return data — keep as Python (EXP of cumulative SUM)
    for i, dt in enumerate(log_ret.index):
        ws.cell(row=cr_row + i, column=1, value=dt.date()).number_format = FMT_DATE
        for j, ticker in enumerate(ALL_TICKERS):
            rets = log_ret.get(ticker, pd.Series(dtype=float))
            cum_val = np.exp(rets.iloc[:i + 1].sum()) * 100 if i < len(rets) and pd.notna(rets.iloc[:i + 1].sum()) else None
            if cum_val is not None and not np.isnan(cum_val):
                ws.cell(row=cr_row + i, column=j + 2, value=round(cum_val, 2))

    cr_end = cr_row + len(log_ret) - 1

    # Add cumulative return chart
    if cr_end > cr_start:
        chart = LineChart()
        chart.title = "Cumulative Log Returns (Indexed to 100)"
        chart.y_axis.title = "Value"
        chart.x_axis.title = "Date"
        chart.width = 35
        chart.height = 20
        chart.style = 10
        for j, ticker in enumerate(ALL_TICKERS):
            data_ref = Reference(ws, min_col=j + 2, min_row=cr_start - 1, max_row=cr_end)
            chart.add_data(data_ref, titles_from_data=True)
        cats = Reference(ws, min_col=1, min_row=cr_start, max_row=cr_end)
        chart.set_categories(cats)
        ws.add_chart(chart, "A" + str(cr_end + 3))

    auto_width(ws)
    return results


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5 — CORRELATION & COVARIANCE STRUCTURE
# ═══════════════════════════════════════════════════════════════════════════════
def build_tab_05(wb, data, results):
    ws = wb.create_sheet(title=TAB_NAMES[5])
    set_tab_color(ws, TAB_COLORS["blue"])

    log_ret = data["log_returns"]
    master = data["master"]
    regime = results.get("regime", pd.Series(dtype=float))

    ws["A1"] = "CORRELATION & COVARIANCE STRUCTURE"
    ws["A1"].font = FONT_TITLE

    # Columns to use for correlation
    corr_cols = [c for c in ALL_TICKERS + ["WTI", "Brent"] if c in log_ret.columns]
    ret_df = log_ret[corr_cols].dropna(how="all")

    # ── Section A: Full-Period Correlation Matrix ────────────────────────
    ws["A3"] = "SECTION A — FULL-PERIOD CORRELATION MATRIX"
    ws["A3"].font = FONT_SUBTITLE

    corr_mat = ret_df.corr()
    n_cols = len(corr_cols)

    # Get Tab 1 references for CORREL formulas
    tab1_name = results.get("tab1_name", TAB_NAMES[1])
    ret_col_map = results.get("tab1_ret_col_map", {})
    dr_start = results.get("tab1_ret_start_row", 5)
    dr_end = results.get("tab1_ret_end_row", 1000)

    # Headers
    for j, col in enumerate(corr_cols):
        ws.cell(row=4, column=j + 2, value=col).font = FONT_HEADER
        ws.cell(row=4, column=j + 2).fill = FILL_HEADER

    for i, row_name in enumerate(corr_cols):
        ws.cell(row=5 + i, column=1, value=row_name).font = FONT_HEADER
        for j, col_name in enumerate(corr_cols):
            # Use CORREL formula if both columns exist in Tab 1
            col_i = ret_col_map.get(row_name)
            col_j = ret_col_map.get(col_name)
            if col_i and col_j:
                if row_name == col_name:
                    # Diagonal = 1
                    c = ws.cell(row=5 + i, column=j + 2, value=1.0)
                else:
                    rng_i = sheet_range(tab1_name, col_i, dr_start, dr_end)
                    rng_j = sheet_range(tab1_name, col_j, dr_start, dr_end)
                    c = ws.cell(row=5 + i, column=j + 2,
                                value=f_correl(rng_i, rng_j))
            else:
                val = corr_mat.loc[row_name, col_name] if row_name in corr_mat.index and col_name in corr_mat.columns else np.nan
                if pd.notna(val):
                    c = ws.cell(row=5 + i, column=j + 2, value=round(float(val), 3))
            c.number_format = FMT_NUM3

    # Color scale
    add_correlation_coloring(ws, 5, 4 + n_cols, 2, 1 + n_cols)

    results["corr_matrix"] = corr_mat

    # ── Section B: Full-Period Covariance Matrix ─────────────────────────
    cov_start = 5 + n_cols + 3
    ws.cell(row=cov_start, column=1, value="SECTION B — FULL-PERIOD COVARIANCE MATRIX (ANNUALIZED)").font = FONT_SUBTITLE
    cov_start += 1

    cov_mat = ret_df.cov() * 252
    for j, col in enumerate(corr_cols):
        ws.cell(row=cov_start, column=j + 2, value=col).font = FONT_HEADER
        ws.cell(row=cov_start, column=j + 2).fill = FILL_HEADER

    for i, row_name in enumerate(corr_cols):
        ws.cell(row=cov_start + 1 + i, column=1, value=row_name).font = FONT_HEADER
        for j, col_name in enumerate(corr_cols):
            col_i = ret_col_map.get(row_name)
            col_j = ret_col_map.get(col_name)
            if col_i and col_j:
                rng_i = sheet_range(tab1_name, col_i, dr_start, dr_end)
                rng_j = sheet_range(tab1_name, col_j, dr_start, dr_end)
                c = ws.cell(row=cov_start + 1 + i, column=j + 2,
                            value=f_covariance(rng_i, rng_j, annualize=True))
            else:
                val = cov_mat.loc[row_name, col_name] if row_name in cov_mat.index and col_name in cov_mat.columns else np.nan
                if pd.notna(val):
                    c = ws.cell(row=cov_start + 1 + i, column=j + 2, value=float(val))
            c.number_format = '0.000000'

    results["cov_matrix"] = cov_mat

    # NEW: Store additional metadata for downstream tabs
    results["tab5_name"] = TAB_NAMES[5]
    results["tab5_cov_start_row"] = cov_start + 1  # first data row of covariance matrix
    results["tab5_cov_start_col"] = 2               # column B (first data column)

    # ── Section C: Regime-Conditional Correlation Matrices ───────────────
    rc_start = cov_start + 1 + n_cols + 3
    ws.cell(row=rc_start, column=1, value="SECTION C — REGIME-CONDITIONAL CORRELATIONS").font = FONT_SUBTITLE
    rc_start += 1

    # Keep regime-conditional correlations as Python (array formulas with IF are complex)
    regime_corrs = {}
    for rid, rname in REGIME_NAMES.items():
        mask = (regime == rid).reindex(ret_df.index, fill_value=False)
        if mask.sum() < 10:
            continue
        regime_ret = ret_df[mask].dropna(how="all")
        if len(regime_ret) < 5:
            continue

        ws.cell(row=rc_start, column=1, value=f"Regime {rid}: {rname} (N={mask.sum()})").font = FONT_SUBTITLE
        rc_start += 1

        rcorr = regime_ret.corr()
        regime_corrs[rid] = rcorr

        for j, col in enumerate(corr_cols):
            ws.cell(row=rc_start, column=j + 2, value=col).font = FONT_HEADER
        rc_start += 1

        for i, row_name in enumerate(corr_cols):
            ws.cell(row=rc_start + i, column=1, value=row_name).font = FONT_HEADER
            for j, col_name in enumerate(corr_cols):
                if row_name in rcorr.index and col_name in rcorr.columns:
                    val = rcorr.loc[row_name, col_name]
                    if pd.notna(val):
                        ws.cell(row=rc_start + i, column=j + 2, value=round(float(val), 3)).number_format = FMT_NUM3

        rc_start += n_cols + 2

    results["regime_corrs"] = regime_corrs

    # ── Section F: Cross-Segment Correlation Summary ─────────────────────
    ws.cell(row=rc_start, column=1, value="SECTION F — CROSS-SEGMENT CORRELATION SUMMARY").font = FONT_SUBTITLE
    rc_start += 1

    pair_list = [
        ("XOM", "COP", "Integrated vs E&P"),
        ("LNG", "VG", "Contracted vs Spot LNG"),
        ("FRO", "STNG", "Crude vs Product Tankers"),
        ("ET", "BIL", "Midstream vs Cash"),
        ("COP", "WTI", "Pure E&P vs Oil"),
        ("FRO", "WTI", "Tankers vs Oil"),
    ]
    pair_headers = ["Pair", "Full Period"]
    for rid, rname in REGIME_NAMES.items():
        pair_headers.append(rname)
    for j, h in enumerate(pair_headers):
        ws.cell(row=rc_start, column=j + 1, value=h).font = FONT_HEADER
        ws.cell(row=rc_start, column=j + 1).fill = FILL_HEADER
    rc_start += 1

    for a, b, label in pair_list:
        ws.cell(row=rc_start, column=1, value=f"{a} vs {b}: {label}")
        if a in corr_mat.index and b in corr_mat.columns:
            ws.cell(row=rc_start, column=2, value=round(float(corr_mat.loc[a, b]), 3)).number_format = FMT_NUM3
        col_off = 3
        for rid in REGIME_NAMES:
            if rid in regime_corrs:
                rc = regime_corrs[rid]
                if a in rc.index and b in rc.columns:
                    ws.cell(row=rc_start, column=col_off, value=round(float(rc.loc[a, b]), 3)).number_format = FMT_NUM3
            col_off += 1
        rc_start += 1

    # ── Section D: Rolling 60-day correlation with WTI ──────────────────
    rc_start += 2
    ws.cell(row=rc_start, column=1, value="SECTION D — ROLLING 60-DAY CORRELATION WITH WTI").font = FONT_SUBTITLE
    rc_start += 1

    equity_tickers = [t for t in ALL_TICKERS if t != "BIL" and t in log_ret.columns]
    ws.cell(row=rc_start, column=1, value="Date").font = FONT_HEADER
    for j, t in enumerate(equity_tickers):
        ws.cell(row=rc_start, column=j + 2, value=t).font = FONT_HEADER
        ws.cell(row=rc_start, column=j + 2).fill = FILL_HEADER
    ws.cell(row=rc_start, column=1).fill = FILL_HEADER
    rc_start += 1

    if "WTI" in log_ret.columns:
        # Sample every 5 days to keep file size reasonable; start from day 60
        dates_to_write = log_ret.index[59::5]
        for dt in dates_to_write:
            ws.cell(row=rc_start, column=1, value=dt.date()).number_format = FMT_DATE
            window = log_ret.loc[:dt].tail(60)
            for j, t in enumerate(equity_tickers):
                if t in window.columns:
                    pair_data = window[[t, "WTI"]].dropna()
                    if len(pair_data) >= 20:
                        corr_val = pair_data[t].corr(pair_data["WTI"])
                        if pd.notna(corr_val):
                            ws.cell(row=rc_start, column=j + 2, value=round(float(corr_val), 4)).number_format = FMT_NUM4
            rc_start += 1

    # ── Section E: Correlation Heatmap Delta (Crisis - Growth) ──────────
    rc_start += 2
    ws.cell(row=rc_start, column=1, value="SECTION E — CORRELATION DELTA (CRISIS - GROWTH)").font = FONT_SUBTITLE
    rc_start += 1

    crisis_mask = (regime == 3).reindex(ret_df.index, fill_value=False)
    growth_mask = (regime == 1).reindex(ret_df.index, fill_value=False)
    crisis_rets = ret_df[crisis_mask]
    growth_rets = ret_df[growth_mask]

    if len(crisis_rets) >= 10 and len(growth_rets) >= 10:
        corr_crisis = crisis_rets.corr()
        corr_growth = growth_rets.corr()
        delta = corr_crisis - corr_growth

        # Write headers
        ws.cell(row=rc_start, column=1, value="").fill = FILL_HEADER
        for j, col_name in enumerate(corr_cols):
            ws.cell(row=rc_start, column=j + 2, value=col_name).font = FONT_HEADER
            ws.cell(row=rc_start, column=j + 2).fill = FILL_HEADER
        rc_start += 1

        for i, ri in enumerate(corr_cols):
            ws.cell(row=rc_start, column=1, value=ri).font = FONT_HEADER
            for j, rj in enumerate(corr_cols):
                if ri in delta.index and rj in delta.columns:
                    val = delta.loc[ri, rj]
                    if pd.notna(val):
                        ws.cell(row=rc_start, column=j + 2, value=round(float(val), 3)).number_format = FMT_NUM3
            rc_start += 1
    else:
        ws.cell(row=rc_start, column=1, value="Insufficient data for crisis or growth regime to compute delta.").font = FONT_NORMAL

    auto_width(ws)
    return results
