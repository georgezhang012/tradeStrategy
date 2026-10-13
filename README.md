# Multi-Agent Quantitative Stock Trading Strategy & Backtesting Platform

A high-performance algorithmic and multi-agent equity trading system equipped with:
1. **Full-Market Alpha Screening**: Comprehensive screening across the entire **S&P 500** and **NASDAQ 100** (evaluating 2-year, 5-year, 10-year, and 20-year horizons) with institutional cross-sector breadth (max 3 stocks per sector across 13 sectors).
2. **Historical Backtesting & Operations Tracker**: Ability to travel back in time (e.g. 1 year ago, 2 years ago, or custom date ranges), execute the multi-agent trading strategy, review a complete chronological history of operations (buys, sells, trims, trailing stop-losses, and walk-forward rotations), and benchmark returns against **VTI** (Total US Stock Market), **QQQ** (NASDAQ 100), and **SPY** (S&P 500).
3. **Institutional Walk-Forward Re-screening**: Eliminates selection lookback bias by dynamically re-evaluating relative momentum every quarter (60 trading days), exiting decaying laggards, and rotating into fresh emerging leaders.
4. **ATR-Based Adaptive Trailing Stops**: Volatility-adaptive risk management using $4.0 \times \text{ATR}_{14}$ (bounded between 10% and 25%), protecting gains tightly on low-volatility compounders while preventing whipsaws on high-beta growth leaders.
5. **Multi-Agent Investment Committee**: 4-agent consensus pipeline (Macroeconomic Analyst, Alpha Screener, News Sentiment Specialist, and Chief Investment Strategist) deploying 100% of capital across an institutional 15-stock allocation matrix.

> 📖 **Operational Manual**: For an exhaustive reference on running every script with arguments and copy-paste examples, see [`RUN_SCRIPTS_GUIDE.md`](RUN_SCRIPTS_GUIDE.md).

---

## 🚀 Key Features & Enhancements

### 1. S&P 500 & NASDAQ 100 Outperformance Screener (2-Year Default & Multi-Sector)
- Analyzes all constituent companies across both the **S&P 500** and **NASDAQ 100** indices.
- Evaluates individual historical compound growth against:
  - **S&P 500 Benchmark Average (SPY)**: 2Y CAGR = 16.3%, 2Y Return = 35.3%
  - **NASDAQ 100 Benchmark Average (QQQ)**: 2Y CAGR = 17.5%, 2Y Return = 38.1%
  - **Total Market Benchmark Average (VTI)**: 2Y CAGR = 12.9%, 2Y Return = 27.5%
- Curates a diverse universe of market-beating compounders across Clean Power/Nuclear, Aerospace, Semiconductors, Networking, Cybersecurity, Financial Analytics, and Industrials.
- Enforces an institutional **cross-sector diversification constraint** (maximum 3 stocks per sector).

### 2. Time-Travel Backtesting & Operations History Engine
- Set any historical start date (e.g., `--lookback 1y`, `--lookback 2y`, or `--start-date 2025-10-12`).
- **Simulates Strategy Execution**:
  - Initial capital deployment based on Markowitz Max-Sharpe portfolio optimization.
  - **Adaptive ATR Trailing Stops** ($4.0 \times \text{ATR}_{14}$, dynamically adapting to each asset's volatility).
  - **Quarterly Walk-Forward Universe Re-screening** (re-evaluates relative strength every 60 days, rotates out of decaying laggards into emerging leaders).
  - **Trend Re-entry Confirmation** (redeploys cash into stocks reclaiming 20-day SMA, eliminating idle cash drag).
  - **Periodic Drift Rebalancing** (controls risk by trimming over-concentrated positions).
- **Chronological History of Operations**: Every transaction is logged with Date, Action, Symbol, Shares, Price, Notional, Remaining Cash, Total Portfolio Value, and Trigger Reason.
- **Benchmark Scorecard**: Compares the strategy's total return, CAGR, volatility, Sharpe ratio, and maximum drawdown side-by-side against **VTI**, **QQQ**, and **SPY**.

---

## 💻 Quick Start & Usage

### 1. Run Strategy Backtest (e.g., 1 Year Ago)
Backtest the multi-agent strategy over the past 1 year:
```bash
python backtest_strategy.py --lookback 1y
```

Backtest a specific stock (e.g. NVIDIA) with tranche accumulation and trailing stops:
```bash
python backtest_strategy.py --symbol NVDA --lookback 1y
```

Custom capital, custom lookback, and custom compounders count:
```bash
python backtest_strategy.py --capital 250000 --lookback 2y --top-n 5
```

Custom explicit date range:
```bash
python backtest_strategy.py --start-date 2025-10-12 --end-date 2026-10-12
```

### 2. Run Backtest via Multi-Agent System Runner
You can also run backtests directly through `run_basic_four_agent.py`:
```bash
# Multi-asset portfolio backtest over past 1 year
python run_basic_four_agent.py --backtest --lookback 1y

# Single-stock backtest
python run_basic_four_agent.py --backtest --symbol NVDA --lookback 1y
```

Or from `basic_multi_agent_system.py`:
```bash
python basic_multi_agent_system.py --backtest --lookback 1y
```

### 3. Screen All S&P 500 & NASDAQ 100 Outperformers
Run the standalone market screener to view the complete list of beaters:
```bash
python sp500_nasdaq_screener.py
```

### 4. Run the Standard Multi-Agent Investment Pipeline
Execute the 4-agent committee pipeline (Macro -> Screener -> News -> CIO Strategy):
```bash
# 10-Year Horizon
python run_basic_four_agent.py --years 10

# 20-Year Horizon
python run_basic_four_agent.py --years 20

# Focused on a specific stock
python run_basic_four_agent.py --symbol MSFT
```

---

## 📊 Sample Backtest Output & Benchmark Scorecard

```
============================================================================================
                   MULTI-AGENT STRATEGY HISTORICAL BACKTEST REPORT                    
============================================================================================
  • Strategy Type:      Multi-Asset Alpha Portfolio
  • Test Window:        2025-10-12  -->  2026-10-12 (1.0 Years / 261 Trading Days)
  • Starting Capital:   $100,000.00
  • Final Strategy Eq:  $154,163.44  (+54.24%)
  • Target Universe:    NVDA, AMD, AVGO, TSLA, AXON
--------------------------------------------------------------------------------------------

============================================================================================
                           CHRONOLOGICAL HISTORY OF OPERATIONS                              
============================================================================================
DATE        ACTION          SYM     SHARES   PRICE ($)   NOTIONAL ($)   PORTFOLIO ($) REASON / TRIGGER    
---------------------------------------------------------------------------------------------------------
2025-10-13  BUY             NVDA       470 $     87.54 $    41,143.80 $     99,981.20 Initial Alpha Allocation (Screened Compounder
2025-10-13  BUY             AMD         52 $    112.06 $     5,827.12 $     99,978.08 Initial Alpha Allocation (Screened Compounder
2025-10-13  BUY             AVGO       438 $     94.05 $    41,193.90 $     99,956.18 Initial Alpha Allocation (Screened Compounder
2025-10-13  BUY             TSLA        26 $    218.11 $     5,670.86 $     99,953.32 Initial Alpha Allocation (Screened Compounder
2025-10-13  BUY             AXON        25 $    235.12 $     5,878.00 $     99,950.32 Initial Alpha Allocation (Screened Compounder
2025-12-01  STOP_LOSS       NVDA       470 $     84.68 $    39,799.60 $    102,019.75 Trailing Stop hit (-15.0% from peak $99.67)
2025-12-01  BUY             AMD         94 $    107.72 $    10,125.68 $    102,015.05 Tranche Accumulation on Pullback (-6.9% dip)
...
2026-01-02  TAKE_PROFIT     AVGO       121 $    123.09 $    14,893.89 $    112,313.38 Take-Profit locked (+30.0% target hit)
2026-03-27  REBALANCE_TRIM  AXON       100 $    372.36 $    37,236.00 $    135,121.07 Periodic Rebalance Trim (Weight drifted +29.7%)
---------------------------------------------------------------------------------------------------------
Total Operations Executed: 46 (Buys: 33, Sells/Trims: 13)

============================================================================================
                   BENCHMARK SCORECARD: STRATEGY vs. VTI vs. QQQ vs. SPY                   
============================================================================================
PERFORMANCE METRIC         OUR STRATEGY     VTI (Total Market)   QQQ (Nasdaq 100)   SPY (S&P 500)   
--------------------------------------------------------------------------------------------------
Initial Capital            $100,000.00      $100,000.00          $100,000.00        $100,000.00     
Ending Equity              $154,163.44      $113,124.76          $114,543.00        $114,051.48     
Total Return (%)           +54.24%          +13.12%              +14.54%            +14.05%
Annualized Return (CAGR)   +54.29%          +13.13%              +14.55%            +14.06%
Annual Volatility          20.52%           15.12%               21.00%             13.78%
Sharpe Ratio (Rf=4.5%)     ⭐ 2.43          0.57                 0.48               0.69            
Max Drawdown                -9.67%           -7.56%              -23.01%             -9.82%
--------------------------------------------------------------------------------------------------
EXCESS ALPHA vs BENCHMARK  ---              +41.12%              +39.70%            +40.19%
Outperformance Multiple    ---              4.13x                 3.73x               3.86x
--------------------------------------------------------------------------------------------------

💡 STRATEGIC INVESTMENT COMMITTEE VERDICT:
   • vs VTI (Total US Market): Beat total market by +41.12% excess return (4.13x outperformance multiple).
   • vs QQQ (Nasdaq 100):      Beat Nasdaq 100 growth by +39.7% excess return (3.73x outperformance multiple).
   • Risk Efficiency Edge:     Strategy achieved a Sharpe Ratio of 2.43 (vs QQQ 0.48 and VTI 0.57).
============================================================================================
```

---

## 🏛 Architecture & Codebase Map

| Module | Description |
| :--- | :--- |
| [`sp500_nasdaq_screener.py`](sp500_nasdaq_screener.py) | Full S&P 500 & NASDAQ 100 constituent database & benchmark outperformance filter. |
| [`historical_data_feed.py`](historical_data_feed.py) | Market data provider with live API downloads and offline daily OHLCV simulator. |
| [`backtest_engine.py`](backtest_engine.py) | Core backtesting engine, operation logging, trailing stop execution, and benchmark scorecard. |
| [`backtest_strategy.py`](backtest_strategy.py) | CLI runner for strategy backtesting with flexible lookback/date parameters. |
| [`basic_multi_agent_system.py`](basic_multi_agent_system.py) | 4-Agent financial intelligence system with the updated market-beating `WATCHLIST`. |
| [`run_basic_four_agent.py`](run_basic_four_agent.py) | Unified runner supporting standalone analysis, backtesting, and AutoGen LLM mode. |
| [`etrade_trader.py`](etrade_trader.py) | Automated E*TRADE brokerage execution with OAuth 1.0a, whole-share integer lot optimization, and `--dry-run` simulation for $10k accounts. |
| [`portfolio_optimizer.py`](portfolio_optimizer.py) | Markowitz Max Sharpe & Risk Parity allocation solver. |
| [`paper_trading_simulator.py`](paper_trading_simulator.py) | Virtual broker simulator for forward execution and position tracking. |
| [`monitor_and_alert.py`](monitor_and_alert.py) | Automated daily stop-loss auditor and portfolio drift alert system. |

---

## ⚡ Automated E*TRADE Broker Execution

To execute the institutional multi-agent allocation on your E*TRADE account ($10,000 balance):

```bash
# 1. Preview simulated order tickets with whole-share integer rounding (Dry-Run mode)
python3 etrade_trader.py --balance 10000 --dry-run

# 2. Authenticate OAuth 1.0a session with your E*TRADE developer keys
python3 etrade_trader.py --auth

# 3. Submit live / sandbox orders
python3 etrade_trader.py --balance 10000 --live
```

