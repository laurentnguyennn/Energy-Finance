"""
Configuration constants for the Energy Finance Workbook.
All tickers, date ranges, parameters, and fundamental data.
"""
from datetime import date

# ── Date Range ──────────────────────────────────────────────────────────────
START_DATE = "2019-01-01"
END_DATE = date.today().isoformat()

# ── Securities Universe ─────────────────────────────────────────────────────
EQUITY_TICKERS = ["XOM", "CVX", "COP", "OXY", "LNG", "VG", "FRO", "STNG", "ET"]
SAFE_HAVEN_TICKER = "BIL"
ALL_TICKERS = EQUITY_TICKERS + [SAFE_HAVEN_TICKER]
MARKET_TICKER = "SPY"

VG_IPO_DATE = "2025-01-24"

# ── Commodity / Macro Tickers (Yahoo Finance) ───────────────────────────────
COMMODITY_YAHOO = {
    "TTF": "TTF=F",
    "Gold": "GC=F",
    "MOVE": "^MOVE",
}

# ── FRED Series ─────────────────────────────────────────────────────────────
FRED_SERIES = {
    "WTI": "DCOILWTICO",
    "Brent": "DCOILBRENTEU",
    "HenryHub": "DHHNGSP",
    "VIX": "VIXCLS",
    "OVX": "OVXCLS",
    "FedFunds": "DFF",
    "DGS2": "DGS2",
    "DGS10": "DGS10",
    "T10YIE": "T10YIE",
    "DXY": "DTWEXBGS",
    "CPI": "CPIAUCSL",
    "CPI_Energy": "CPIENGSL",
    "IndProd": "INDPRO",
    "UMich": "UMCSENT",
    "Claims": "ICSA",
}

# ── FRED API Key ────────────────────────────────────────────────────────────
# Get a free key at https://fred.stlouisfed.org/docs/api/api_key.html
# Set environment variable FRED_API_KEY or replace this default
FRED_API_KEY = "b70ecbb7d8a4ca619e8a885e5807f9cc"

# ── Event Windows ───────────────────────────────────────────────────────────
EVENT_WINDOWS = {
    1: ("Pre-COVID",       "2019-01-01", "2020-02-19"),
    2: ("COVID",           "2020-02-20", "2020-06-30"),
    3: ("Recovery",        "2020-07-01", "2022-02-23"),
    4: ("Russia-Ukraine",  "2022-02-24", "2022-12-31"),
    5: ("Normalization",   "2023-01-01", "2025-05-31"),
    6: ("12-Day War",      "2025-06-01", "2025-06-30"),
    7: ("Iran Conflict",   "2026-02-28", END_DATE),
}

# ── Regime Parameters ───────────────────────────────────────────────────────
REGIME_NAMES = {
    0: "Transition",
    1: "Risk-On Growth",
    2: "Inflation Shock",
    3: "Geopolitical Crisis",
    4: "Recession / Risk-Off",
}

# ── Portfolio Parameters ────────────────────────────────────────────────────
RF_RATE = 0.0319  # BIL yield ~3.19% annualized
PORTFOLIO_VALUE = 10_000_000
MAX_WEIGHT = 0.30
MIN_BIL_WEIGHT = 0.05
EQUITY_RISK_PREMIUM = 0.055
TERMINAL_GROWTH = 0.02

# ── Monte Carlo ─────────────────────────────────────────────────────────────
MC_SIMULATIONS = 10_000
MC_SEED = 42

# ── EWMA Parameter ──────────────────────────────────────────────────────────
EWMA_LAMBDA = 0.94

# ── Scenario Probabilities ──────────────────────────────────────────────────
SCENARIO_PROBS = [0.50, 0.35, 0.15]
SCENARIO_NAMES = ["Short Conflict", "Prolonged Conflict", "Escalation"]
# Approximate horizon in trading days for each scenario (for intercept scaling)
SCENARIO_HORIZON_DAYS = {"Short Conflict": 15, "Prolonged Conflict": 85, "Escalation": 126}

# ── Fundamental Data (approximate anchor values) ────────────────────────────
FUNDAMENTALS = {
    "XOM":  {"name": "Exxon Mobil",       "subsector": "Integrated Major",
             "mkt_cap": 460e9, "ev": 490e9, "revenue": 340e9, "ebitda": 55e9,
             "net_income": 33e9, "eps": 8.00, "pe": 14, "ev_ebitda": 9,
             "div_yield": 0.035, "net_debt_ebitda": 0.5, "fcf_yield": 0.08,
             "production": "3.7M boe/d", "coupon": 0.0425, "bond_maturity": 2030,
             "bond_rating": "AA-", "bond_price": 98.5, "wacc_rd": 0.04},
    "CVX":  {"name": "Chevron",           "subsector": "Integrated Major",
             "mkt_cap": 270e9, "ev": 290e9, "revenue": 195e9, "ebitda": 45e9,
             "net_income": 18e9, "eps": 9.50, "pe": 15, "ev_ebitda": 6.5,
             "div_yield": 0.043, "net_debt_ebitda": 0.8, "fcf_yield": 0.07,
             "production": "3.7M boe/d", "coupon": 0.035, "bond_maturity": 2029,
             "bond_rating": "AA-", "bond_price": 97.0, "wacc_rd": 0.038},
    "COP":  {"name": "ConocoPhillips",    "subsector": "Pure E&P",
             "mkt_cap": 120e9, "ev": 130e9, "revenue": 55e9, "ebitda": 25e9,
             "net_income": 10e9, "eps": 7.50, "pe": 12, "ev_ebitda": 5,
             "div_yield": 0.030, "net_debt_ebitda": 0.4, "fcf_yield": 0.09,
             "production": "1.9M boe/d", "coupon": 0.05, "bond_maturity": 2031,
             "bond_rating": "A", "bond_price": 99.0, "wacc_rd": 0.045},
    "OXY":  {"name": "Occidental Petroleum", "subsector": "E&P + Chemicals",
             "mkt_cap": 35e9, "ev": 50e9, "revenue": 26e9, "ebitda": 12e9,
             "net_income": 2.5e9, "eps": 2.50, "pe": 14, "ev_ebitda": 4,
             "div_yield": 0.020, "net_debt_ebitda": 1.3, "fcf_yield": 0.06,
             "production": "1.48M boe/d", "coupon": 0.06125, "bond_maturity": 2028,
             "bond_rating": "BBB-", "bond_price": 101.0, "wacc_rd": 0.055},
    "LNG":  {"name": "Cheniere Energy",   "subsector": "LNG Export",
             "mkt_cap": 50e9, "ev": 70e9, "revenue": 20e9, "ebitda": 7e9,
             "net_income": 5e9, "eps": 20.0, "pe": 10, "ev_ebitda": 10,
             "div_yield": 0.010, "net_debt_ebitda": 3.0, "fcf_yield": 0.07,
             "production": "9 trains", "coupon": None, "bond_maturity": None,
             "bond_rating": None, "bond_price": None, "wacc_rd": 0.05},
    "VG":   {"name": "Venture Global",    "subsector": "LNG Export (Growth)",
             "mkt_cap": 21e9, "ev": 50e9, "revenue": 13.8e9, "ebitda": 6e9,
             "net_income": 2e9, "eps": 0.54, "pe": 39, "ev_ebitda": 8,
             "div_yield": 0.0, "net_debt_ebitda": 7.0, "fcf_yield": 0.02,
             "production": "128 cargos Q4", "coupon": 0.08375, "bond_maturity": 2031,
             "bond_rating": "BB-", "bond_price": 95.0, "wacc_rd": 0.075},
    "FRO":  {"name": "Frontline",         "subsector": "Crude Tankers",
             "mkt_cap": 3e9, "ev": 5e9, "revenue": 1.5e9, "ebitda": 0.8e9,
             "net_income": 0.4e9, "eps": 2.00, "pe": 7, "ev_ebitda": 6,
             "div_yield": 0.10, "net_debt_ebitda": 2.5, "fcf_yield": 0.15,
             "production": "41 VLCCs", "coupon": None, "bond_maturity": None,
             "bond_rating": None, "bond_price": None, "wacc_rd": 0.06},
    "STNG": {"name": "Scorpio Tankers",   "subsector": "Product Tankers",
             "mkt_cap": 3e9, "ev": 4e9, "revenue": 1.2e9, "ebitda": 0.5e9,
             "net_income": 0.3e9, "eps": 6.00, "pe": 9, "ev_ebitda": 8,
             "div_yield": 0.035, "net_debt_ebitda": 1.5, "fcf_yield": 0.10,
             "production": "99 tankers", "coupon": None, "bond_maturity": None,
             "bond_rating": None, "bond_price": None, "wacc_rd": 0.055},
    "ET":   {"name": "Energy Transfer",   "subsector": "Midstream Pipelines",
             "mkt_cap": 65e9, "ev": 110e9, "revenue": 80e9, "ebitda": 15.5e9,
             "net_income": 6e9, "eps": 1.80, "pe": 11, "ev_ebitda": 7,
             "div_yield": 0.070, "net_debt_ebitda": 3.0, "fcf_yield": 0.12,
             "production": "130K+ miles", "coupon": 0.055, "bond_maturity": 2032,
             "bond_rating": "BBB-", "bond_price": 100.5, "wacc_rd": 0.05},
    "BIL":  {"name": "SPDR 1-3M T-Bill ETF", "subsector": "Ultrashort Treasury",
             "mkt_cap": 43.3e9, "ev": None, "revenue": None, "ebitda": None,
             "net_income": None, "eps": None, "pe": None, "ev_ebitda": None,
             "div_yield": 0.0319, "net_debt_ebitda": None, "fcf_yield": None,
             "production": "N/A", "coupon": None, "bond_maturity": None,
             "bond_rating": None, "bond_price": None, "wacc_rd": None},
}

# ── DCF Parameters ──────────────────────────────────────────────────────────
DCF_STOCKS = ["XOM", "CVX", "COP", "OXY"]
DCF_PARAMS = {
    "XOM": {"prod_growth": [0.00, 0.01, 0.01, 0.00, 0.00],
            "ebitda_margin": [0.16, 0.16, 0.16, 0.16, 0.16],
            "capex_pct": 0.06, "tax_rate": 0.22, "da_pct": 0.04,
            "wc_change_pct": 0.005, "shares_out": 4.1e9},
    "CVX": {"prod_growth": [0.05, 0.03, 0.02, 0.01, 0.01],
            "ebitda_margin": [0.23, 0.24, 0.24, 0.24, 0.24],
            "capex_pct": 0.07, "tax_rate": 0.22, "da_pct": 0.05,
            "wc_change_pct": 0.005, "shares_out": 1.85e9},
    "COP": {"prod_growth": [0.03, 0.02, 0.02, 0.01, 0.01],
            "ebitda_margin": [0.45, 0.44, 0.43, 0.42, 0.42],
            "capex_pct": 0.10, "tax_rate": 0.21, "da_pct": 0.08,
            "wc_change_pct": 0.005, "shares_out": 1.3e9},
    "OXY": {"prod_growth": [0.02, 0.02, 0.01, 0.01, 0.00],
            "ebitda_margin": [0.46, 0.45, 0.44, 0.43, 0.42],
            "capex_pct": 0.08, "tax_rate": 0.21, "da_pct": 0.06,
            "wc_change_pct": 0.005, "shares_out": 0.9e9},
}
OIL_PRICE_PATH = [75, 72, 70, 70, 68]  # WTI assumption per year
OIL_TERMINAL = 65

# ── Bond Analysis ───────────────────────────────────────────────────────────
BOND_ISSUERS = ["XOM", "CVX", "COP", "OXY", "VG", "ET"]

# ── Options Analysis ────────────────────────────────────────────────────────
OPTIONS_STOCKS = ["XOM", "CVX", "COP", "OXY"]
OPTIONS_MATURITIES_DAYS = [30, 60, 90]
OPTIONS_MONEYNESS = [0.90, 0.92, 0.94, 0.96, 0.98, 1.00, 1.02, 1.04, 1.06, 1.08, 1.10]

# ── Pair Trades ─────────────────────────────────────────────────────────────
PAIRS = [
    ("XOM", "CVX",  "Integrated"),
    ("COP", "OXY",  "E&P"),
    ("LNG", "VG",   "LNG Export"),
    ("FRO", "STNG", "Shipping"),
    ("COP", "ET",   "Beta vs Defensive"),
]

# ── Scenario Assumptions ───────────────────────────────────────────────────
# Each scenario: (WTI_target, VIX_change, 2s10s_change, DXY_pct, breakeven_change, OVX_change)
SCENARIO_INPUTS = {
    "Short Conflict":     {"wti_target": 82,  "vix_delta": 5,   "spread_2s10s_delta": -0.10,
                           "dxy_pct": 0.02,   "breakeven_delta": 0.25, "ovx_delta": 8},
    "Prolonged Conflict": {"wti_target": 100,  "vix_delta": 12,  "spread_2s10s_delta": -0.40,
                           "dxy_pct": 0.01,   "breakeven_delta": 1.00, "ovx_delta": 20},
    "Escalation":         {"wti_target": 135,  "vix_delta": 30,  "spread_2s10s_delta": -0.80,
                           "dxy_pct": -0.03,  "breakeven_delta": 3.00, "ovx_delta": 45},
}

# ── Stress Scenarios (Monte Carlo overlay) ──────────────────────────────────
STRESS_SCENARIOS = {
    "Hormuz Full Closure":   {"wti_pct": 0.30, "vix_pts": 15, "spread_2s10s": -0.50,
                              "dxy_pct": 0.03, "breakeven_delta": 1.5, "ovx_delta": 25},
    "Nuclear Escalation":    {"wti_pct": 0.50, "vix_pts": 25, "spread_2s10s": -1.00,
                              "dxy_pct": -0.05, "breakeven_delta": 3.0, "ovx_delta": 45},
    "Rapid De-escalation":   {"wti_pct": -0.20, "vix_pts": -10, "spread_2s10s": 0.30,
                              "dxy_pct": -0.01, "breakeven_delta": -0.5, "ovx_delta": -15},
}

# ── Tab Names ───────────────────────────────────────────────────────────────
TAB_NAMES = {
    1:  "01_Data",
    2:  "02_Regime",
    3:  "03_Profiles",
    4:  "04_Performance",
    5:  "05_Correlation",
    6:  "06_Regression",
    7:  "07_Volatility",
    8:  "08_Portfolio",
    9:  "09_Valuation",
    10: "10_VaR",
    11: "11_MonteCarlo",
    12: "12_FixedIncome",
    13: "13_Options",
    14: "14_Scenarios",
    15: "15_TailRisk",
    16: "16_Transmission",
    17: "17_PairTrades",
    18: "18_Factors",
    19: "19_Backtest",
    20: "20_Dashboard",
}

# ── Tab Colors ──────────────────────────────────────────────────────────────
TAB_COLORS = {
    "green":  "00B050",   # data tabs (1-3)
    "blue":   "4472C4",   # analysis tabs (4-8)
    "red":    "FF0000",   # risk tabs (9-15)
    "purple": "7030A0",   # recommendation tabs (16-20)
}
