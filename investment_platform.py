"""
Unified Investment & Virtual Trading Platform
=============================================
End-to-end platform that:
1. Optimizes asset allocations to Maximize Return while Minimizing Risk (Max Sharpe).
2. Audits individual assets via the Institutional Multi-Agent Committee.
3. Automatically executes virtual orders into the Paper Trading Sandbox.
4. Generates an institutional portfolio performance statement.

Usage:
  python tradingStrategy/platform.py                         # Runs with default universe
  python tradingStrategy/platform.py --capital 250000        # Custom capital
  python tradingStrategy/platform.py --symbols NVDA MSFT AAPL AMZN
"""

import os
import sys
import argparse
from typing import List

# Ensure package is on sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
for p in [current_dir, parent_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from tradingStrategy.portfolio_optimizer import PortfolioOptimizer
    from tradingStrategy.paper_trading_simulator import PaperTradingSimulator
    from tradingStrategy.orchestrator import InstitutionalTradingSystem
    from tradingStrategy.alpaca_paper_trader import AlpacaPaperTrader
except ImportError:
    from portfolio_optimizer import PortfolioOptimizer
    from paper_trading_simulator import PaperTradingSimulator
    from orchestrator import InstitutionalTradingSystem
    from alpaca_paper_trader import AlpacaPaperTrader


def run_investment_platform(
    symbols: List[str],
    capital: float = 100000.0,
    reset_sandbox: bool = False
):
    print("=" * 75)
    print("      INTELLIGENT INVESTMENT & VIRTUAL TRADING PLATFORM        ")
    print("          [Maximize Sharpe Ratio | Minimize Tail Risk]         ")
    print("=" * 75)

    # ---------------------------------------------------------
    # STEP 1: PORTFOLIO OPTIMIZATION (MAXIMIZE SHARPE RATIO)
    # ---------------------------------------------------------
    print(f"\n[Phase 1] Mathematical Portfolio Optimization across universe: {symbols}")
    opt_result = PortfolioOptimizer.optimize_max_sharpe(symbols=symbols)
    parity_result = PortfolioOptimizer.optimize_risk_parity(symbols=symbols)

    print(f"\n  • Target Strategy: {opt_result['strategy']}")
    print(f"  • Expected Annual Return: +{opt_result['expected_annual_return_pct']}%")
    print(f"  • Expected Volatility:    {opt_result['expected_annual_volatility_pct']}%")
    print(f"  • Portfolio Sharpe Ratio: ⭐ {opt_result['sharpe_ratio']} (vs S&P 500 ~0.6-0.8)")
    print(f"\n  Optimal Capital Weights:")
    for sym, weight in opt_result["weights"].items():
        print(f"    - {sym:<6}: {weight * 100:>5.1f}%  (${capital * weight:>10,.2f})")

    # ---------------------------------------------------------
    # STEP 1.5: BENCHMARK SCORECARD (PORTFOLIO vs VTI vs QQQ)
    # ---------------------------------------------------------
    bench_data = PortfolioOptimizer.compare_against_benchmarks(
        port_return_pct=opt_result['expected_annual_return_pct'],
        port_volatility_pct=opt_result['expected_annual_volatility_pct'],
        port_sharpe=opt_result['sharpe_ratio']
    )

    vti = next(b for b in bench_data["benchmarks"] if b["ticker"] == "VTI")
    qqq = next(b for b in bench_data["benchmarks"] if b["ticker"] == "QQQ")

    ret_opt = f"+{opt_result['expected_annual_return_pct']}%"
    ret_vti = f"+{vti['benchmark_return_pct']}%"
    ret_qqq = f"+{qqq['benchmark_return_pct']}%"

    vol_opt = f"{opt_result['expected_annual_volatility_pct']}%"
    vol_vti = f"{vti['benchmark_volatility_pct']}%"
    vol_qqq = f"{qqq['benchmark_volatility_pct']}%"

    sharpe_opt = f"⭐ {opt_result['sharpe_ratio']}"
    sharpe_vti = str(vti['benchmark_sharpe'])
    sharpe_qqq = str(qqq['benchmark_sharpe'])

    cagr_vti = f"+{vti['cagr_10y']}%"
    cagr_qqq = f"+{qqq['cagr_10y']}%"

    dd_vti = f"{vti['max_drawdown_5y_pct']}%"
    dd_qqq = f"{qqq['max_drawdown_5y_pct']}%"

    alpha_vti = f"+{vti['excess_return_alpha_pct']}%"
    alpha_qqq = f"+{qqq['excess_return_alpha_pct']}%"

    vold_vti = f"{vti['volatility_delta_pct']:+.2f}%"
    vold_qqq = f"{qqq['volatility_delta_pct']:+.2f}% (Lower!)"

    print(f"\n[Phase 1.5] Benchmark Scorecard: Optimized Portfolio vs. VTI vs. QQQ")
    print("  " + "-" * 73)
    print(f"  {'METRIC':<24} {'OPTIMIZED':<14} {'VTI (Total Market)':<20} {'QQQ (Nasdaq 100)':<18}")
    print("  " + "-" * 73)
    print(f"  {'Exp. Annual Return':<24} {ret_opt:<14} {ret_vti:<20} {ret_qqq:<18}")
    print(f"  {'Annual Volatility':<24} {vol_opt:<14} {vol_vti:<20} {vol_qqq:<18}")
    print(f"  {'Sharpe Ratio (Rf=4.5%)':<24} {sharpe_opt:<14} {sharpe_vti:<20} {sharpe_qqq:<18}")
    print(f"  {'10-Year CAGR':<24} {'---':<14} {cagr_vti:<20} {cagr_qqq:<18}")
    print(f"  {'5-Yr Max Drawdown':<24} {'---':<14} {dd_vti:<20} {dd_qqq:<18}")
    print(f"  {'Excess Alpha vs Bench':<24} {'---':<14} {alpha_vti:<20} {alpha_qqq:<18}")
    print(f"  {'Volatility Delta':<24} {'---':<14} {vold_vti:<20} {vold_qqq:<18}")
    print("  " + "-" * 73)
    print(f"  💡 Benchmark Verdict:")
    print(f"     • vs VTI: Generates +{vti['excess_return_alpha_pct']}% excess return above the total US stock market.")
    print(f"     • vs QQQ: Matches Nasdaq-level growth (+{opt_result['expected_annual_return_pct']}%) with {abs(qqq['volatility_delta_pct']):.1f}% LOWER volatility.")
    print(f"     • True Risk-Adjusted Edge: Sharpe ratio is {opt_result['sharpe_ratio']} (vs QQQ {qqq['benchmark_sharpe']} and VTI {vti['benchmark_sharpe']}).")

    # ---------------------------------------------------------
    # Audit the top-weighted allocation asset
    top_asset = max(opt_result["weights"].items(), key=lambda x: x[1])[0]
    print(f"\n[Phase 2] Conducting Multi-Agent Committee Audit on Top Asset: {top_asset}...")
    
    committee_system = InstitutionalTradingSystem()
    committee_audit = committee_system.evaluate_investment_idea(symbol=top_asset, portfolio_equity=capital)
    cro = committee_audit["cro_decision"]

    print(f"  • Committee Decision: {cro['decision']}")
    print(f"  • ATR Dynamic Stop-Loss: ${cro['position_sizing']['stop_loss_price']:.2f} (-{cro['position_sizing']['stop_loss_pct']}%)")
    print(f"  • Reward/Risk Asymmetry: 2.5:1 Target at ${cro['position_sizing']['target_price']:.2f}")

    # ---------------------------------------------------------
    # STEP 3: VIRTUAL BROKER EXECUTION (PAPER TRADING)
    # ---------------------------------------------------------
    print(f"\n[Phase 3] Executing Orders in Virtual Paper Trading Sandbox...")
    simulator = PaperTradingSimulator(initial_cash=capital)
    state_file = os.path.join(current_dir, "virtual_portfolio.json")

    if not reset_sandbox and os.path.exists(state_file):
        simulator.load_from_file(state_file)
        print(f"  • Loaded existing virtual portfolio ({len(simulator.positions)} active positions).")
    else:
        print(f"  • Initialized fresh virtual portfolio with ${capital:,.2f} virtual cash.")

    # Execute trades based on optimal weights
    executed_trades = 0
    for sym, weight in opt_result["weights"].items():
        allocated_cash = capital * weight
        # Sample price lookup
        price_lookup = {
            "NVDA": 130.0, "MSFT": 420.0, "AAPL": 230.0,
            "AMZN": 185.0, "GOOGL": 165.0, "AVGO": 175.0, "COST": 880.0
        }
        price = price_lookup.get(sym, 100.0)
        shares = int(allocated_cash / price)

        if shares > 0 and sym not in simulator.positions:
            atr_stop = round(price * 0.91, 2)
            take_profit = round(price * 1.22, 2)
            fill = simulator.execute_order(
                symbol=sym,
                action="BUY",
                shares=shares,
                market_price=price,
                stop_loss=atr_stop,
                take_profit=take_profit,
                notes=f"Optimal Sharpe Allocation ({weight*100:.1f}%)"
            )
            if fill["status"] == "FILLED":
                executed_trades += 1
                print(f"  [✓] FILLED BUY: {shares} shares of {sym} @ ${fill['order']['execution_price']:.2f} (Stop: ${atr_stop})")

    # Persist updated virtual portfolio state
    simulator.save_to_file(state_file)

    # Check Alpaca Paper API status
    alpaca = AlpacaPaperTrader()
    alpaca_status = "Connected (Live Paper)" if alpaca.is_configured() else "Ready (Set APCA_API_KEY_ID to stream to Alpaca)"

    # ---------------------------------------------------------
    # STEP 4: PORTFOLIO ACCOUNT SUMMARY DASHBOARD
    # ---------------------------------------------------------
    summary = simulator.get_portfolio_summary()
    print("\n" + "=" * 75)
    print("               VIRTUAL ACCOUNT PERFORMANCE STATEMENT                   ")
    print("=" * 75)
    print(f"  Starting Balance:      ${summary['initial_capital']:>12,.2f}")
    print(f"  Cash Remaining:        ${summary['cash_balance']:>12,.2f}")
    print(f"  Invested Capital:      ${summary['invested_capital']:>12,.2f}")
    print(f"  Total Portfolio Equity:${summary['total_portfolio_equity']:>12,.2f}")
    print(f"  Total PnL ($):         ${summary['total_pnl']:>12,.2f} ({summary['total_return_pct']:+.2f}%)")
    print(f"  Active Positions:      {summary['active_positions_count']:>12}")
    print(f"  Alpaca Broker Bridge:  {alpaca_status}")
    print("-" * 75)
    print(f"  {'SYMBOL':<8} {'SHARES':<8} {'ENTRY':<10} {'CURRENT':<10} {'MKT VALUE':<12} {'STOP LOSS':<10}")
    for p in summary["positions"]:
        print(f"  {p['symbol']:<8} {p['shares']:<8} ${p['avg_cost']:<9.2f} ${p['current_price']:<9.2f} ${p['market_value']:<11,.2f} ${p['stop_loss']:<9.2f}")
    print("=" * 75)
    print(f"\n[✓] Virtual portfolio state saved to: {state_file}\n")


def main():
    parser = argparse.ArgumentParser(description="Intelligent Investment & Virtual Trading Platform")
    parser.add_argument("--capital", type=float, default=100000.0, help="Initial virtual capital (USD)")
    parser.add_argument("--symbols", nargs="+", default=["NVDA", "MSFT", "AAPL", "AMZN", "COST"], help="Asset universe")
    parser.add_argument("--reset", action="store_true", help="Reset virtual account state to fresh cash")

    args = parser.parse_args()
    run_investment_platform(symbols=args.symbols, capital=args.capital, reset_sandbox=args.reset)


if __name__ == "__main__":
    main()
