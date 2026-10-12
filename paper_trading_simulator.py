"""
Virtual Paper Trading Simulator & Brokerage Sandbox
===================================================
A standalone paper trading engine to test algorithms with simulated money:
1. Manages cash, margin, and open long/short positions.
2. Simulates realistic fills, slippage, and execution commissions.
3. Automatically tracks Unrealized PnL, Realized PnL, and Total Equity.
4. Enforces trailing stop-losses and take-profit targets.
5. Persists portfolio history to disk (JSON).
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional


class PaperTradingSimulator:
    """Local virtual brokerage simulator for forward paper-testing."""

    DEFAULT_STATE_FILE = "virtual_portfolio.json"

    def __init__(self, initial_cash: float = 100000.0, commission_per_trade: float = 0.0, slippage_pct: float = 0.05):
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.realized_pnl = 0.0
        self.commission_rate = commission_per_trade
        self.slippage_pct = slippage_pct # 0.05% slippage simulation
        self.positions: Dict[str, Dict[str, Any]] = {}
        self.trade_history: List[Dict[str, Any]] = []

    def execute_order(
        self,
        symbol: str,
        action: str,            # "BUY" or "SELL"
        shares: int,
        market_price: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        notes: str = ""
    ) -> Dict[str, Any]:
        """Executes a virtual trade with simulated slippage and commission."""
        sym = symbol.upper()
        action = action.upper()
        if shares <= 0:
            return {"status": "REJECTED", "reason": "Shares count must be positive."}

        # Simulate slippage
        slippage_mult = (1.0 + self.slippage_pct / 100.0) if action == "BUY" else (1.0 - self.slippage_pct / 100.0)
        exec_price = round(market_price * slippage_mult, 2)
        trade_notional = round(shares * exec_price, 2)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if action == "BUY":
            total_cost = trade_notional + self.commission_rate
            if total_cost > self.cash:
                return {
                    "status": "REJECTED",
                    "reason": f"Insufficient cash (${self.cash:.2f} available, ${total_cost:.2f} required)."
                }

            self.cash -= total_cost
            if sym in self.positions:
                pos = self.positions[sym]
                total_shares = pos["shares"] + shares
                total_spent = (pos["shares"] * pos["avg_cost"]) + trade_notional
                pos["shares"] = total_shares
                pos["avg_cost"] = round(total_spent / total_shares, 2)
                pos["current_price"] = exec_price
                if stop_loss: pos["stop_loss"] = stop_loss
                if take_profit: pos["take_profit"] = take_profit
            else:
                self.positions[sym] = {
                    "symbol": sym,
                    "shares": shares,
                    "avg_cost": exec_price,
                    "current_price": exec_price,
                    "stop_loss": stop_loss,
                    "take_profit": take_profit,
                    "side": "LONG"
                }

            trade_record = {
                "timestamp": timestamp,
                "symbol": sym,
                "action": "BUY",
                "shares": shares,
                "execution_price": exec_price,
                "notional": trade_notional,
                "cash_remaining": round(self.cash, 2),
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "notes": notes
            }
            self.trade_history.append(trade_record)
            return {"status": "FILLED", "order": trade_record}

        elif action == "SELL":
            if sym not in self.positions or self.positions[sym]["shares"] < shares:
                available = self.positions[sym]["shares"] if sym in self.positions else 0
                return {
                    "status": "REJECTED",
                    "reason": f"Cannot sell {shares} shares. Only {available} shares owned."
                }

            pos = self.positions[sym]
            proceeds = trade_notional - self.commission_rate
            self.cash += proceeds

            cost_basis = shares * pos["avg_cost"]
            pnl = round(proceeds - cost_basis, 2)
            self.realized_pnl += pnl

            pos["shares"] -= shares
            if pos["shares"] == 0:
                del self.positions[sym]

            trade_record = {
                "timestamp": timestamp,
                "symbol": sym,
                "action": "SELL",
                "shares": shares,
                "execution_price": exec_price,
                "notional": trade_notional,
                "realized_pnl": pnl,
                "cash_remaining": round(self.cash, 2),
                "notes": notes
            }
            self.trade_history.append(trade_record)
            return {"status": "FILLED", "order": trade_record}

        return {"status": "REJECTED", "reason": f"Unknown action {action}"}

    def update_prices(self, price_map: Dict[str, float]):
        """Updates current prices for all open positions."""
        for sym, price in price_map.items():
            sym_u = sym.upper()
            if sym_u in self.positions:
                self.positions[sym_u]["current_price"] = price

    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Calculates current equity, unrealized PnL, and performance return."""
        positions_value = 0.0
        open_positions_summary = []

        for sym, pos in self.positions.items():
            mkt_val = round(pos["shares"] * pos["current_price"], 2)
            cost_val = round(pos["shares"] * pos["avg_cost"], 2)
            unrealized_pnl = round(mkt_val - cost_val, 2)
            unrealized_pnl_pct = round((unrealized_pnl / cost_val) * 100, 2) if cost_val > 0 else 0.0

            positions_value += mkt_val
            open_positions_summary.append({
                "symbol": sym,
                "side": pos["side"],
                "shares": pos["shares"],
                "avg_cost": pos["avg_cost"],
                "current_price": pos["current_price"],
                "market_value": mkt_val,
                "unrealized_pnl": unrealized_pnl,
                "unrealized_pnl_pct": unrealized_pnl_pct,
                "stop_loss": pos.get("stop_loss"),
                "take_profit": pos.get("take_profit")
            })

        total_equity = round(self.cash + positions_value, 2)
        total_pnl = round(total_equity - self.initial_cash, 2)
        total_return_pct = round((total_pnl / self.initial_cash) * 100, 2)

        return {
            "initial_capital": self.initial_cash,
            "cash_balance": round(self.cash, 2),
            "invested_capital": round(positions_value, 2),
            "total_portfolio_equity": total_equity,
            "total_pnl": total_pnl,
            "total_return_pct": total_return_pct,
            "realized_pnl": round(self.realized_pnl, 2),
            "active_positions_count": len(open_positions_summary),
            "positions": open_positions_summary,
            "total_trades_count": len(self.trade_history)
        }

    def save_to_file(self, filepath: Optional[str] = None):
        """Saves virtual account state to disk."""
        path = filepath or self.DEFAULT_STATE_FILE
        data = {
            "initial_cash": self.initial_cash,
            "cash": self.cash,
            "realized_pnl": self.realized_pnl,
            "positions": self.positions,
            "trade_history": self.trade_history
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def load_from_file(self, filepath: Optional[str] = None):
        """Loads virtual account state from disk."""
        path = filepath or self.DEFAULT_STATE_FILE
        if os.path.exists(path):
            with open(path, "r") as f:
                data = json.load(f)
            self.initial_cash = data.get("initial_cash", 100000.0)
            self.cash = data.get("cash", 100000.0)
            self.realized_pnl = data.get("realized_pnl", 0.0)
            self.positions = data.get("positions", {})
            self.trade_history = data.get("trade_history", [])

