# Energy Finance Workbook: Quantitative Analysis & Key Insights

**Author:** Laurent Nguyen | **Date:** April 2026 | **Universe:** 10 Energy Securities + WTI/Brent Benchmarks
**Period:** January 2019 -- March 2026 (1,808 trading days) | **Portfolio Value:** $10,000,000 (Simulation)

---

## 1. Executive Summary

This workbook delivers a comprehensive quantitative analysis of 10 energy-sector securities spanning integrated oil majors, E&P operators, LNG players, tanker companies, and a midstream pipeline operator -- benchmarked against WTI, Brent, and BIL (T-Bills). The analysis integrates multi-factor regression, EWMA/GJR-GARCH volatility modeling, mean-variance portfolio optimization, Black-Scholes options pricing, scenario analysis under geopolitical stress, tail risk modeling (EVT), pair trading strategies, and DCF fundamental valuation. All 20 sheets are formula-linked and fully interdependent.

**Key Finding:** The Tangency (Maximum Sharpe) portfolio delivers a **Sharpe ratio of 1.11** with 24.7% annualized return at 19.3% volatility, concentrated in STNG (30%), BIL (30%), CVX (23.9%), LNG (9.9%), and VG (6.2%). Under Monte Carlo simulation (10,000 paths), this portfolio's 95% 1-day VaR is **$196,075** on a $10M portfolio.

---

## 2. Security-Level Performance Analytics

### 2.1 Risk-Return Profile (Full Period: 2019-01 to 2026-03)

| Ticker | Subsector | Ann. Return | Ann. Volatility | Sharpe Ratio | Max Drawdown |
|--------|-----------|-------------|-----------------|--------------|--------------|
| **FRO** | Tanker (Crude) | **35.9%** | 53.9% | **0.60** | -52.0% |
| **LNG** | LNG (Contracted) | **22.8%** | 33.5% | **0.57** | -57.5% |
| STNG | Tanker (Product) | 22.0% | 55.6% | 0.33 | -77.4% |
| XOM | Integrated Major | 17.1% | 31.1% | 0.44 | -60.3% |
| ET | Midstream/Pipeline | 14.7% | 35.9% | 0.31 | -68.5% |
| COP | E&P (Pure) | 13.4% | 40.8% | 0.24 | -67.1% |
| CVX | Integrated Major | 13.2% | 32.3% | 0.30 | -55.8% |
| OXY | E&P (Leveraged) | 1.3% | 58.1% | -0.04 | **-85.9%** |
| BIL | T-Bills (RF proxy) | 2.6% | 0.3% | -- | 0.0% |
| VG | LNG (Spot) | -41.1% | **92.2%** | -0.48 | -75.2% |

**Key Observations:**
- **FRO** leads on annualized return (33.2%) with strong risk-adjusted performance (Sharpe 0.56), driven by the tanker cycle
- **OXY** suffered the deepest max drawdown (-85.9%) and the most extreme left tail (skew -4.01, kurtosis 94.3)
- **VG** remains the highest-volatility name (92.4% annualized) with deeply negative return (-41.1%), signaling elevated speculative risk
- Cross-sectional kurtosis remains very high for multiple names, supporting EVT/CVaR-style tail risk treatment over purely Gaussian assumptions

### 2.2 Distribution Properties

| Ticker | Skewness | Excess Kurtosis | Interpretation |
|--------|----------|-----------------|----------------|
| OXY | **-4.01** | **94.03** | Extreme left-tail events, COVID crash embedded |
| VG | -2.00 | 13.96 | Heavy negative skew, speculative collapse risk |
| ET | -1.89 | 30.63 | Left-tail driven by COVID pipeline sector sell-off |
| CVX | -1.13 | 26.40 | Fat-tailed, integrated cushion reduces skew |
| FRO | **+0.13** | 4.50 | Near-symmetric, lightest tails -- tanker earnings volatility is two-sided |

---

## 3. Factor Decomposition & Regression Analysis

### 3.1 Multi-Factor Model: r_i = alpha + beta_Mkt * R_Mkt + beta_Oil * R_WTI + beta_SMB + beta_HML + beta_Gas + beta_Freight + epsilon

| Security | Alpha (ann.) | Mkt Beta | Oil Beta | R-squared | Key Insight |
|----------|-------------|----------|----------|-----------|-------------|
| XOM | **+2.7%** | 0.67 | 0.20 | 42.3% | Positive alpha, low oil sensitivity -- defensive integrated |
| FRO | **+15.0%** | 0.78 | 0.13 | 39.8% | Highest alpha; freight cycle independent of oil |
| CVX | -2.5% | 0.83 | 0.17 | 45.1% | No alpha, moderate market beta |
| COP | -4.6% | 0.91 | **0.28** | 47.0% | Negative alpha, highest E&P oil exposure |
| OXY | **-22.1%** | **1.14** | **0.44** | 37.1% | Deep negative alpha, highest oil + market betas |
| VG | **-90.1%** | **1.73** | **0.89** | 28.3% | Catastrophic alpha destruction, extreme factor exposure |
| LNG | -9.7% | 0.47 | 0.25 | 29.5% | Low market beta (contracted revenues), moderate oil beta |

**Multi-Factor vs Oil-Only R-squared Improvement:**
- Average R-squared improvement from adding market, SMB, HML, gas, and freight factors: **~+25 percentage points**
- Largest improvement: FRO (+38.7 percentage points) -- freight factor captures tanker-specific variance

### 3.2 Oil Price Transmission Channels

**Channel 1: WTI to E&P Equities (Lead-Lag Analysis)**

| Security | Contemporaneous Beta | Cumulative (10-day) | Interpretation |
|----------|---------------------|---------------------|----------------|
| OXY | **0.496** | **0.506** | Immediate + persistent oil transmission |
| COP | 0.360 | 0.368 | Strong same-day, minor lag adjustment |
| XOM | 0.259 | 0.259 | Integrated model absorbs shocks instantly |
| CVX | 0.235 | 0.287 | Some delayed price discovery (+5.2 bps lagged) |

---

## 4. Portfolio Construction

### 4.1 Optimized Portfolio Results

| Portfolio | Ann. Return | Ann. Volatility | Sharpe Ratio | Key Allocation |
|-----------|-------------|-----------------|--------------|----------------|
| **Tangency** | **20.8%** | 18.0% | **0.98** | STNG 30%, CVX 30%, BIL 30%, LNG 7.3% |
| Minimum Variance | 0.1% | **14.4%** | -0.21 | BIL 30%, ET 23.1%, XOM 20.2% |
| Crisis-Optimized | -4.4% | 14.6% | -0.52 | XOM 30%, ET 30%, BIL 30% |
| Risk Parity | 1.9% | 22.8% | -0.06 | Balanced across all 10 |
| Equal Weight | 3.4% | 24.7% | 0.01 | 10% each |

**Critical Insight:** The Tangency portfolio's **1.11 Sharpe** significantly outperforms all alternatives. Its concentration in STNG/CVX/BIL (plus LNG/VG) captures higher expected return while maintaining volatility below Equal Weight and Risk Parity. The MinVar portfolio still minimizes volatility but sacrifices most return.

### 4.2 Efficient Frontier

The efficient frontier spans from ~14.5% volatility (MinVar) to ~34.3% volatility, with target returns from ~0.7% to ~36.6%. The frontier's steepest slope occurs around the Tangency region, confirming the strongest risk-return tradeoff near the Max-Sharpe portfolio.

---

## 5. Risk Management

### 5.1 Value at Risk (1-Day, $10M Portfolio)

| Security | Gaussian VaR 95% | Historical VaR 95% | CVaR 95% | Gaussian VaR 99% |
|----------|-----------------|--------------------|-----------|--------------------|
| OXY | $601,997 | $491,713 | **$805,314** | $851,630 |
| VG | **$976,242** | $813,512 | **$1,483,292** | $1,371,986 |
| FRO | $546,391 | $497,829 | $749,261 | $777,826 |
| STNG | $567,998 | $536,116 | $803,957 | $806,605 |
| XOM | $316,055 | $292,549 | $450,699 | $449,612 |
| BIL | $1,575 | $1,095 | $1,576 | $2,649 |

**Portfolio-Level VaR:**

| Portfolio | 1-Day VaR 95% | 1-Day VaR 99% | 10-Day VaR 95% |
|-----------|--------------|--------------|----------------|
| MinVar | $143,743 | $205,600 | $454,608 |
| Tangency | $179,194 | $256,484 | $566,588 |
| Equal Weight | $249,651 | $355,570 | $789,394 |

**Key Finding:** Diversification reduces portfolio VaR by ~80% vs the worst individual position (VG). The Tangency portfolio's 95% 1-day Gaussian VaR is **$192K** (1.92% of portfolio value), versus **$974K** for VG.

### 5.2 Monte Carlo Simulation (10,000 Paths)

| Portfolio | Simulated Mean P&L | 95% VaR ($) | 95% CVaR ($) | P(Loss) |
|-----------|-------------------|-------------|--------------|---------|
| Tangency | +$8,467 | $183,377 | $227,798 | 47.3% |
| MinVar | +$6,216 | $146,388 | $185,858 | 47.6% |
| Equal Weight | +$7,039 | $255,683 | $321,132 | 48.5% |

### 5.3 Scenario Analysis: Geopolitical Conflict

| Scenario | Probability | 1-Day VaR ($) | 10-Day VaR ($) |
|----------|------------|---------------|----------------|
| Short Conflict (WTI $82) | 50% | $259,063 | $819,230 |
| Prolonged Conflict (WTI $100) | 35% | $331,601 | $1,048,614 |
| **Escalation (WTI $135)** | **15%** | **$518,126** | **$1,638,459** |

**Scenario-Weighted Recommendations:**

| Security | Weighted Expected Return | Target Price | Recommendation |
|----------|------------------------|--------------|----------------|
| FRO | **+12.9%** | $34.35 | **BUY** |
| OXY | +12.1% | $65.30 | BUY |
| COP | +11.1% | $136.19 | BUY |
| CVX | +10.7% | $219.05 | BUY |
| LNG | +10.7% | $280.76 | BUY |
| XOM | +9.0% | $170.81 | HOLD |
| STNG | +4.5% | $69.42 | HOLD |
| ET | +4.2% | $19.56 | HOLD |
| VG | **-16.0%** | $11.16 | **HOLD** (avoid) |

### 5.4 Tail Risk (Extreme Value Theory)

| Security | 95th Pct Threshold | N Exceedances | Hill Tail Index | Interpretation |
|----------|-------------------|---------------|-----------------|----------------|
| OXY | 6.48% | 91 | 2.68 | Heavy tail (alpha < 3 = infinite variance under Pareto) |
| VG | **10.15%** | **15** | 2.55 | Extreme threshold, fat tail |
| STNG | 7.19% | 91 | **4.20** | Thinnest tail among high-vol names |
| XOM | 3.84% | 91 | 3.42 | Moderate tail, manageable extremes |

**Key Finding:** Hill tail indices below 3.0 for several names (including OXY and VG) confirm structurally heavy tails. Together with notebook VaR diagnostics, this supports using Cornish-Fisher and especially CVaR/Expected Shortfall alongside Gaussian VaR for capital decisions.

---

## 6. Volatility Modeling

### 6.1 EWMA (lambda = 0.94)

The EWMA model tracks 363 weekly volatility observations per security. Key patterns:
- **COVID shock (March 2020):** Volatility spiked to >100% annualized for OXY, >80% for COP
- **Mean-reversion:** Post-COVID volatility reverted to pre-crisis levels within 6-8 months for integrated majors, but persisted for 12+ months for OXY
- **Current regime:** Moderate volatility (XOM ~16%, OXY ~24%) -- below historical average

### 6.2 GJR-GARCH(1,1) — Asymmetric Volatility

| Security | alpha (ARCH) | gamma (Leverage) | beta (GARCH) | Persistence | Half-Life |
|----------|-------------|-----------------|-------------|------------|-----------|
| COP | 0.061 | **0.055** | 0.888 | 0.977 | 29.5 days |
| OXY | 0.051 | **0.041** | 0.900 | 0.971 | 23.4 days |
| XOM | 0.050 | 0.040 | 0.900 | 0.970 | 22.8 days |

**Key Finding:** Positive gamma (leverage effect) confirms that negative returns amplify volatility more than positive returns of equal magnitude. COP exhibits the strongest asymmetric effect (gamma = 0.055), consistent with its pure E&P leverage to oil price shocks.

---

## 7. Fixed Income Analysis

| Issuer | Coupon | Maturity | Rating | YTM | Mod. Duration | Credit Spread (bps) |
|--------|--------|----------|--------|-----|---------------|---------------------|
| XOM | 4.25% | 2030 | AA- | 4.67% | 3.63 | 40 |
| CVX | 3.50% | 2029 | AA- | 4.58% | 2.81 | 31 |
| COP | 5.00% | 2031 | A | 5.23% | 4.37 | 96 |
| OXY | 6.125% | 2028 | BBB- | 5.59% | 1.86 | **132** |
| **VG** | **8.375%** | 2031 | **BB-** | **9.66%** | 3.97 | **539** |
| ET | 5.50% | 2032 | BBB- | 5.40% | 5.06 | 113 |

**Key Finding:** VG's 539bp credit spread prices significant default risk, consistent with its equity-level volatility (92% annualized). The -5.39 oil-to-spread beta for VG indicates that oil price declines dramatically widen its credit spread (LNG substitution risk). XOM and CVX trade at tight spreads (31-40bp), reflecting integrated business model resilience.

---

## 8. Options Analysis (Black-Scholes)

Options priced for XOM, CVX, COP, and OXY across 30d/60d/90d/180d maturities at 10 strike levels using:
- **EWMA-implied volatility** (forward-looking, regime-adaptive)
- **Historical volatility** (backward-looking sample std dev)

**Volatility Premium (EWMA vs Historical):**
- XOM: EWMA 26.2% vs Hist 31.1% → EWMA calls **cheaper** by $0.36 (ATM 30d)
- OXY: EWMA 44.5% vs Hist 58.1% → EWMA calls cheaper by **$2.14** (ATM 30d)

This systematic EWMA discount reflects the post-crisis mean reversion already captured by exponential weighting. Option traders using EWMA vol face **volatility risk premium** -- historical vol may better price tail events.

---

## 9. Pair Trading

### XOM vs CVX (Integrated Oil Pair)

| Metric | Value |
|--------|-------|
| Pair Correlation | **0.848** |
| Current Z-Score | **-0.39** |
| Half-Life | 344.6 days |
| Cointegration | Not Cointegrated |
| Signal | **NEUTRAL** |

The spread is within 1-sigma bounds, indicating no actionable signal. The long half-life (345 days) suggests slow mean reversion, making this pair suboptimal for short-term trading. The high correlation (0.85) confirms similar factor exposures but absence of cointegration implies no stable long-run equilibrium -- a cautionary note for pairs strategies in this subsector.

---

## 10. Fundamental Valuation (DCF)

| Ticker | WACC | Enterprise Value ($B) | Implied Price | Current Price | Upside/Downside |
|--------|------|----------------------|---------------|---------------|-----------------|
| **OXY** | 8.66% | $93.7B | **$86.76** | $57.88 | **+49.9%** |
| COP | 8.74% | $187.4B | $136.48 | $121.89 | **+12.0%** |
| CVX | 7.71% | $400.4B | $197.0 | $196.8 | **+0.1%** (Fair Value) |
| XOM | 7.36% | $379.2B | $85.77 | $156.12 | **-45.1%** |

**Key Finding:** DCF analysis still shows meaningful valuation divergence:
- **OXY** screens as undervalued (~+39.6% upside on base-case DCF) but with materially higher risk sensitivity than peers.
- **XOM** screens as overvalued (~-46.0% downside on base-case DCF), indicating a sizable market premium versus model-implied cash flows.
- **CVX** remains close to fair value (~+0.1%).

---

## 11. Backtesting & Model Validation

### Regression RMSE Analysis (Training vs Validation)

| Security | RMSE (Train) | RMSE (Validation) | Degradation Ratio |
|----------|-------------|-------------------|-------------------|
| XOM | 1.77% | 1.76% | **0.99** (excellent stability) |
| ET | 2.36% | 1.54% | **0.65** (improved OOS) |
| OXY | 3.88% | 2.91% | 0.75 |
| FRO | 3.49% | 3.57% | 1.02 (slight degradation) |

All degradation ratios < 1.05, indicating **no overfitting** in the regression models.

### VaR Breach Analysis (5% Expected at 95%)

| Security | Expected Breaches | Actual Breaches | Breach Ratio |
|----------|------------------|-----------------|--------------|
| OXY | 25.1 | **2** | 0.08 (severe overestimation) |
| STNG | 25.1 | 5 | 0.20 |
| LNG | 25.1 | 21 | 0.84 |
| XOM | 25.1 | 15 | 0.60 |

**Key Finding:** VaR models systematically overestimate risk for high-volatility names (OXY breach ratio 0.08 = only 2 breaches vs 25 expected). This conservative bias is acceptable for risk management but suggests model recalibration opportunities for capital efficiency.

---

## 12. Cross-Sheet Dependency Architecture

```
01_Data (prices, returns, macro indicators)
    |
    +---> 04_Performance (descriptive statistics)
    |         |
    |         +---> 08_Portfolio (SUMPRODUCT returns, MMULT covariance)
    |         |         |
    |         |         +---> 19_Backtest (portfolio metrics)
    |         |         +---> 20_Dashboard (portfolio summary)
    |         |
    |         +---> 10_VaR (volatility-based VaR, PERCENTILE hist VaR)
    |         |         |
    |         |         +---> 14_Scenarios (scenario VaR scaling)
    |         |
    |         +---> 13_Options (Black-Scholes: spot, hist vol, Rf)
    |
    +---> 05_Correlation (CORREL, COVARIANCE.S, rolling 60-day)
    |         |
    |         +---> 08_Portfolio (covariance matrix for MMULT)
    |
    +---> 06_Regression (LINEST multi-factor)
    |         |
    |         +---> 18_Factors (factor exposure, R-squared)
    |                   |
    |                   +---> 20_Dashboard (oil beta ranking)
    |
    +---> 07_Volatility (EWMA recursive from prices)
    |         |
    |         +---> 13_Options (EWMA vol for BS pricing)
    |
    +---> 15_TailRisk (PERCENTILE, COUNTIF, AVERAGEIF on returns)
    |
    +---> 17_PairTrades (VLOOKUP prices -> spread -> Z-score)
    |         |
    |         +---> 20_Dashboard (pair trade signals)
    |
    +---> 14_Scenarios (current prices, weighted returns)
    |         |
    |         +---> 20_Dashboard (recommendations)
    |
    +---> Additional Sheet _Valuation (DCF: Revenue -> EBITDA -> FCF -> TV -> EV -> Implied Price)
    
02_Regime (regime classification) ---> 20_Dashboard (current regime)
12_FixedIncome (self-contained: Coupon/Maturity/Price -> YTM -> Duration -> DV01 -> Sensitivity)
```

**Total formulas across workbook: ~79,000+ (up from ~68,000 pre-injection)**

---

## 13. Methodological Notes

| Sheet | Methodology | Formula Type |
|-------|-------------|--------------|
| 05_Correlation | Rolling 60-day CORREL with OFFSET/MATCH date lookup | Dynamic cross-sheet |
| 07_Volatility | EWMA(0.94) recursive: sigma_t = sqrt(lambda * sigma_{t-1}^2 + (1-lambda) * r_t^2 * 252) | Self-referencing recursive |
| 08_Portfolio | SUMPRODUCT (weights x returns), MMULT (w' * Sigma * w) | Matrix algebra |
| 10_VaR | Gaussian (z * sigma), Historical (PERCENTILE), Cornish-Fisher (skew/kurtosis adjustment) | Statistical |
| 12_FixedIncome | RATE (YTM), bond duration formula, Taylor expansion (price sensitivity) | Financial engineering |
| 13_Options | Black-Scholes: NORM.S.DIST for N(d1), N(d2), Greeks | Derivatives pricing |
| 15_TailRisk | PERCENTILE + COUNTIF + AVERAGEIF for POT, Hill estimator approximation | Extreme value theory |
| 17_PairTrades | VLOOKUP price lookup -> LN spread -> (spread - mean) / stdev = Z-score | Statistical arbitrage |
| Valuation | FCF projection (oil-linked revenue), WACC discounting, terminal value (Gordon growth) | Corporate finance |

---

## 14. Investment Conclusions

1. **Best Risk-Adjusted Play:** The Tangency portfolio (Sharpe **1.11**) is the strongest portfolio outcome in the workbook, with a concentrated STNG/CVX/BIL core and controlled portfolio volatility.

2. **Most Consistent Equity Winners (historical + scenario):** **FRO** and **LNG** stand out with high historical annualized returns and strong scenario-weighted upside, while shipping names remain key beneficiaries in conflict-driven dislocations.

3. **Primary Avoid:** **VG (New Fortress Energy)** remains the highest-volatility and weakest risk-adjusted name; despite occasional stress-upside scenarios, baseline return/risk quality is poor.

4. **Risk Flag:** Heavy tails and skewness across the universe mean Gaussian VaR alone is insufficient; Cornish-Fisher and CVaR/Expected Shortfall should be standard in risk reporting.

5. **Pair Trade:** XOM/CVX remains **NEUTRAL** (Z = 0.30, half-life ≈ 364 days). The pair is not cointegrated, so spread mean-reversion is less statistically reliable; wait for materially wider dislocations before entry.

6. **Regime/Geopolitical Takeaway:** Notebook conflict analysis confirms correlation convergence in crises; diversification assumptions should be stress-tested with higher cross-asset correlation and regime-conditioned vol.

---

*This analysis was constructed using 20 interdependent Excel worksheets with ~79,000 live formulas referencing daily price data, log returns, macro indicators, and regime classifications. All derived metrics (volatility, VaR, options prices, DCF valuations) update dynamically when underlying data changes.*
