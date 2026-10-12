"""
Multi-Agent Strategy Backtest CLI Runner
========================================
Runs historical backtests of the multi-agent trading strategy,
replays trading decisions from any past starting point (e.g., 1 year ago),
displays a chronological history of operations, and benchmarks returns
against VTI (Total US Stock Market) and QQQ (Nasdaq 100).

Usage:
  python backtest_strategy.py                             # Backtests multi-asset strategy 1 year ago
  python backtest_strategy.py --lookback 1y               # Explicit 1-year lookback
  python backtest_strategy.py --lookback 2y               # 2-year lookback
  python backtest_strategy.py --symbol NVDA               # Backtests single-stock strategy on NVDA
  python backtest_strategy.py --symbols NVDA MSFT COST    # Custom portfolio backtest
  python backtest_strategy.py --start-date 2025-10-12      # Specific start date
  python backtest_strategy.py --capital 250000            # Custom initial capital
"""

import os
import sys
import argparse

# Ensure current and parent directories are on sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
for p in [current_dir, parent_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from tradingStrategy.backtest_engine import BacktestEngine
except ImportError:
    from backtest_engine import BacktestEngine


def main():
    parser = argparse.ArgumentParser(description="Multi-Agent Strategy Historical Backtesting & Operations Tracker")
    parser.add_argument("--lookback", type=str, default="1y", help="Historical lookback window (e.g., '1y', '2y', '6m', '3y')")
    parser.add_argument("--start-date", type=str, default=None, help="Explicit start date (YYYY-MM-DD), e.g. 2025-10-12")
    parser.add_argument("--end-date", type=str, default=None, help="Explicit end date (YYYY-MM-DD), e.g. 2026-10-12")
    parser.add_argument("--capital", type=float, default=100000.0, help="Initial portfolio capital in USD (default: $100,000)")
    parser.add_argument("--symbol", type=str, default=None, help="Single target stock symbol (e.g., NVDA, MSFT, AAPL, COST)")
    parser.add_argument("--symbols", nargs="+", default=None, help="List of custom target stock symbols (e.g., NVDA MSFT COST LLY)")
    parser.add_argument("--top-n", type=int, default=5, help="Number of top screened compounders to hold (default: 5)")
    parser.add_argument("--stop-loss", type=float, default=0.20, help="Trailing stop loss threshold (default: 0.20 for 20%%)")
    parser.add_argument("--take-profit", type=float, default=0.50, help="Take profit target threshold (default: 0.50 for 50%%)")
    parser.add_argument("--rebalance-days", type=int, default=60, help="Portfolio rebalancing interval in trading days (default: 60)")

    args = parser.parse_args()

    # Determine symbols list
    target_symbols = None
    if args.symbol:
        target_symbols = [args.symbol.upper()]
    elif args.symbols:
        target_symbols = [s.upper() for s in args.symbols]

    engine = BacktestEngine(initial_capital=args.capital)
    results = engine.run_backtest(
        lookback=args.lookback,
        start_date=args.start_date,
        end_date=args.end_date,
        symbols=target_symbols,
        top_n=args.top_n,
        trailing_stop_pct=args.stop_loss,
        take_profit_pct=args.take_profit,
        rebalance_days=args.rebalance_days
    )

    report = BacktestEngine.format_backtest_report(results)
    print("\n" + report + "\n")


if __name__ == "__main__":
    main()
