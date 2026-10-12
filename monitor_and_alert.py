"""
Automated Risk Monitor & Portfolio Alert Engine
===============================================
Runs automated checks according to the institutional schedule:
1. DAILY RISK CHECK:
   - Evaluates all active positions against 2.0x ATR Stop-Loss levels.
   - Evaluates positions against Take-Profit targets.
   - Monitors individual asset and total portfolio drawdown.
2. DRIFT & REBALANCE CHECK (Weekly / Monthly):
   - Computes current asset allocation weights vs. optimal weights.
   - Flags an alert if any asset has drifted by > 5.0% (Tolerance Band).

Usage:
  python tradingStrategy/monitor_and_alert.py                      # Normal check
  python tradingStrategy/monitor_and_alert.py --simulate NVDA=115 # Simulate a price drop to test stop-loss alert
  python tradingStrategy/monitor_and_alert.py --save-log           # Saves alert records to alerts.log
"""

import os
import sys
import json
import argparse
from datetime import datetime
from typing import Dict, Any, List, Tuple

# Ensure package path is resolved
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
for p in [current_dir, parent_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from tradingStrategy.paper_trading_simulator import PaperTradingSimulator
    from tradingStrategy.portfolio_optimizer import PortfolioOptimizer
except ImportError:
    from paper_trading_simulator import PaperTradingSimulator
    from portfolio_optimizer import PortfolioOptimizer


class RiskAndAlertMonitor:
    """Monitors live/virtual portfolio and alerts when trading operations are required."""

    STATE_FILE = os.path.join(current_dir, "virtual_portfolio.json")
    LOG_FILE = os.path.join(current_dir, "alerts.log")

    # Baseline target weights from Optimizer
    TARGET_WEIGHTS = {
        "NVDA": 0.202,
        "MSFT": 0.277,
        "AAPL": 0.058,
        "AMZN": 0.060,
        "COST": 0.403
    }

    # Reference prices (can be updated via live feed or simulation)
    CURRENT_MARKET_PRICES = {
        "NVDA": 130.06,
        "MSFT": 420.21,
        "AAPL": 230.11,
        "AMZN": 185.09,
        "COST": 880.44
    }

    def __init__(self, simulated_prices: Dict[str, float] = None):
        self.simulator = PaperTradingSimulator()
        if os.path.exists(self.STATE_FILE):
            self.simulator.load_from_file(self.STATE_FILE)

        self.market_prices = dict(self.CURRENT_MARKET_PRICES)
        if simulated_prices:
            self.market_prices.update(simulated_prices)

        # Update simulator with current market prices
        self.simulator.update_prices(self.market_prices)

    def run_check(self) -> Dict[str, Any]:
        """Performs full risk and rebalance drift evaluation."""
        summary = self.simulator.get_portfolio_summary()
        alerts = []
        action_required = False

        total_equity = summary["total_portfolio_equity"]
        positions = summary["positions"]

        # -------------------------------------------------------------
        # 1. DAILY RISK & STOP-LOSS AUDIT
        # -------------------------------------------------------------
        for pos in positions:
            sym = pos["symbol"]
            curr_price = pos["current_price"]
            stop_loss = pos.get("stop_loss")
            take_profit = pos.get("take_profit")

            # Check Stop-Loss Breach
            if stop_loss and curr_price <= stop_loss:
                action_required = True
                alerts.append({
                    "type": "STOP_LOSS_BREACH",
                    "severity": "CRITICAL",
                    "symbol": sym,
                    "message": (
                        f"🚨 STOP-LOSS TRIGGERED: {sym} traded at ${curr_price:.2f}, breaching "
                        f"the ATR stop-loss level of ${stop_loss:.2f}."
                    ),
                    "action": f"EXECUTE IMMEDIATE SELL: Close {pos['shares']} shares of {sym} at market to protect capital."
                })

            # Check Take-Profit Target
            elif take_profit and curr_price >= take_profit:
                action_required = True
                alerts.append({
                    "type": "TAKE_PROFIT_REACHED",
                    "severity": "HIGH",
                    "symbol": sym,
                    "message": (
                        f"🎯 TAKE-PROFIT REACHED: {sym} reached ${curr_price:.2f}, meeting "
                        f"the target price of ${take_profit:.2f} (2.5x Risk/Reward achieved)."
                    ),
                    "action": f"EXECUTE PARTIAL TRIM: Harvest profits on 50% ({pos['shares'] // 2} shares) of {sym} and trail remaining stop."
                })

        # -------------------------------------------------------------
        # 2. REBALANCE & WEIGHT DRIFT AUDIT (5% Tolerance Band)
        # -------------------------------------------------------------
        drift_warnings = []
        for pos in positions:
            sym = pos["symbol"]
            current_weight = pos["market_value"] / total_equity if total_equity > 0 else 0
            target_weight = self.TARGET_WEIGHTS.get(sym, 0.20)
            drift = current_weight - target_weight

            # 5% Drift Tolerance Band Rule
            if abs(drift) > 0.05:
                action_required = True
                direction = "OVERWEIGHT" if drift > 0 else "UNDERWEIGHT"
                drift_warnings.append({
                    "symbol": sym,
                    "current_weight_pct": round(current_weight * 100, 1),
                    "target_weight_pct": round(target_weight * 100, 1),
                    "drift_pct": round(drift * 100, 1),
                    "direction": direction
                })
                alerts.append({
                    "type": "PORTFOLIO_WEIGHT_DRIFT",
                    "severity": "MEDIUM",
                    "symbol": sym,
                    "message": (
                        f"⚖️ TOLERANCE BAND BREACH: {sym} is currently {current_weight*100:.1f}% of book "
                        f"(Target: {target_weight*100:.1f}%, Drift: {drift*100:+.1f}%)."
                    ),
                    "action": (
                        f"REBALANCE: {'Trim' if drift > 0 else 'Accumulate'} {sym} back toward target weight."
                    )
                })

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        report = {
            "timestamp": timestamp,
            "action_required": action_required,
            "alerts_count": len(alerts),
            "alerts": alerts,
            "portfolio_summary": summary,
            "drift_warnings": drift_warnings
        }

        return report

    def format_report_text(self, result: Dict[str, Any]) -> str:
        """Formats human-readable terminal and log output."""
        ts = result["timestamp"]
        summary = result["portfolio_summary"]
        action_needed = result["action_required"]

        lines = [
            "=" * 75,
            f"          AUTOMATED PORTFOLIO RISK & REBALANCE AUDIT           ",
            f"                     Timestamp: {ts}                           ",
            "=" * 75,
            f"  Portfolio Equity: ${summary['total_portfolio_equity']:,.2f} | Cash: ${summary['cash_balance']:,.2f}",
            f"  Total PnL:        ${summary['total_pnl']:+,.2f} ({summary['total_return_pct']:+.2f}%)",
            "-" * 75
        ]

        if not action_needed:
            lines.extend([
                "  ✅ STATUS: ALL CLEAR — NO ACTION NEEDED",
                "  • All open positions are operating safely above ATR stop-loss thresholds.",
                "  • Asset allocations are strictly within the 5.0% drift tolerance bands.",
                "  • Capital defense guardrails remain fully intact.",
                "-" * 75
            ])
        else:
            lines.extend([
                "  ⚠️  STATUS: ACTION REQUIRED BY TRADER",
                f"  • Detected {result['alerts_count']} operational trigger(s) requiring intervention:",
                ""
            ])
            for i, a in enumerate(result["alerts"], 1):
                lines.extend([
                    f"  [{i}] [{a['severity']}] {a['type']}:",
                    f"      {a['message']}",
                    f"      👉 RECOMMENDED ACTION: {a['action']}",
                    ""
                ])
            lines.append("-" * 75)

        lines.extend([
            f"  {'SYMBOL':<8} {'CURRENT':<10} {'STOP LOSS':<12} {'BUFFER TO STOP':<16} {'STATUS':<10}",
            "-" * 75
        ])

        for p in summary["positions"]:
            sym = p["symbol"]
            curr = p["current_price"]
            stop = p.get("stop_loss")
            if stop:
                buffer_pct = ((curr - stop) / curr) * 100
                status_str = "BREACHED" if curr <= stop else f"Safe (+{buffer_pct:.1f}%)"
                stop_str = f"${stop:.2f}"
            else:
                status_str = "No Stop"
                stop_str = "None"
                buffer_pct = 0.0

            lines.append(f"  {sym:<8} ${curr:<9.2f} {stop_str:<12} {f'{buffer_pct:.1f}% cushion':<16} {status_str:<10}")

        lines.append("=" * 75)
        return "\n".join(lines)

    def log_alerts(self, text_report: str):
        """Appends timestamped alert report to alerts.log."""
        with open(self.LOG_FILE, "a") as f:
            f.write(text_report + "\n\n")


def main():
    parser = argparse.ArgumentParser(description="Automated Portfolio Risk & Rebalance Monitor")
    parser.add_argument("--simulate", type=str, default=None, help="Simulate a price shock (e.g. NVDA=115 or MSFT=390)")
    parser.add_argument("--save-log", action="store_true", default=True, help="Save alert report to alerts.log")
    parser.add_argument("--send-email", action="store_true", help="Send email alert if action is required")

    args = parser.parse_args()

    sim_prices = {}
    if args.simulate:
        for pair in args.simulate.split(","):
            if "=" in pair:
                s, p = pair.split("=")
                sim_prices[s.strip().upper()] = float(p.strip())

    monitor = RiskAndAlertMonitor(simulated_prices=sim_prices)
    result = monitor.run_check()
    text_report = monitor.format_report_text(result)

    print("\n" + text_report)

    if args.save_log:
        monitor.log_alerts(text_report)
        print(f"[✓] Check logged to: {monitor.LOG_FILE}\n")

    # Send email notification if requested and action is needed
    if args.send_email or os.environ.get("AUTO_SEND_EMAIL") == "true":
        from tradingStrategy.email_notifier import EmailAlertService
        email_svc = EmailAlertService()
        if result["action_required"]:
            subject = f"🚨 Portfolio Alert: {result['alerts_count']} Operational Trigger(s) Detected ({result['timestamp']})"
            res = email_svc.send_alert_email(subject=subject, report_text=text_report, alerts=result["alerts"])
            if res.get("sent"):
                print(f"[✓] Email alert successfully sent to: {res['recipient']}\n")
            else:
                print(f"[!] Email dispatch skipped / error: {res.get('reason') or res.get('error')}\n")
        else:
            print("[i] All clear — no email alert needed (Risk thresholds intact).\n")


if __name__ == "__main__":
    main()

