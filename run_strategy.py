"""
Institutional Multi-Agent Trading Strategy Runner
=================================================
Executes the professional Investment Committee workflow:
- Reverse-DCF Expectations Analysis
- Adversarial Bull vs. Bear (Red Team) Debate
- ATR Volatility Position Sizing
- Beta-Neutral Pairs Hedging

Usage:
  python tradingStrategy/run_strategy.py --symbol NVDA
  python tradingStrategy/run_strategy.py --symbol MSFT --equity 250000
  python tradingStrategy/run_strategy.py --symbol AAPL
"""

import sys
import os
import argparse

# Ensure current directory is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    from tradingStrategy.orchestrator import InstitutionalTradingSystem
except ImportError:
    from orchestrator import InstitutionalTradingSystem


def main():
    parser = argparse.ArgumentParser(description="Institutional Multi-Agent Equity Strategy Runner")
    parser.add_argument("--symbol", type=str, default="NVDA", help="Target ticker symbol (e.g. NVDA, MSFT, AAPL, AMZN, INTC)")
    parser.add_argument("--equity", type=float, default=100000.0, help="Total portfolio equity in USD (default: $100,000)")
    parser.add_argument("--save-memo", action="store_true", default=True, help="Save final committee memo to disk")

    args = parser.parse_args()

    system = InstitutionalTradingSystem()
    result = system.evaluate_investment_idea(symbol=args.symbol, portfolio_equity=args.equity)

    print("\n" + result["committee_memo"])

    if args.save_memo:
        memo_path = os.path.join(current_dir, f"memo_{args.symbol.upper()}.md")
        with open(memo_path, "w") as f:
            f.write(result["committee_memo"])
        print(f"\n[✓] Investment Committee Memo saved to: {memo_path}\n")


if __name__ == "__main__":
    main()

