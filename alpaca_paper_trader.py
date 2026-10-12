"""
Alpaca Paper Trading API Bridge
===============================
Connects the Multi-Agent Strategy directly to Alpaca's Free Paper Trading Platform.
- Base URL: https://paper-api.alpaca.markets
- Simulates real-time market order fills, limit orders, bracket stop-losses.
- Free virtual $100,000 buying power account with zero financial risk.
"""

import os
import json
import requests
from typing import Dict, Any, Optional, List


class AlpacaPaperTrader:
    """Live Paper Trading Connector for Alpaca."""

    BASE_URL = "https://paper-api.alpaca.markets"

    def __init__(
        self,
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None
    ):
        self.api_key = api_key or os.environ.get("APCA_API_KEY_ID")
        self.secret_key = secret_key or os.environ.get("APCA_API_SECRET_KEY")
        self.headers = {
            "APCA-API-KEY-ID": self.api_key or "",
            "APCA-API-SECRET-KEY": self.secret_key or "",
            "Content-Type": "application/json"
        }

    def is_configured(self) -> bool:
        """Returns True if valid credentials are present."""
        return bool(self.api_key and self.secret_key)

    def get_account_summary(self) -> Dict[str, Any]:
        """Fetches live paper account balance, equity, and buying power."""
        if not self.is_configured():
            return {
                "configured": False,
                "message": (
                    "Alpaca API keys not set. Set APCA_API_KEY_ID and APCA_API_SECRET_KEY "
                    "environment variables to connect to Alpaca Paper Trading."
                )
            }

        try:
            resp = requests.get(f"{self.BASE_URL}/v2/account", headers=self.headers, timeout=10)
            if resp.status_code == 200:
                acc = resp.json()
                return {
                    "configured": True,
                    "account_number": acc.get("account_number"),
                    "status": acc.get("status"),
                    "cash": float(acc.get("cash", 0)),
                    "portfolio_value": float(acc.get("portfolio_value", 0)),
                    "buying_power": float(acc.get("buying_power", 0)),
                    "currency": acc.get("currency", "USD")
                }
            else:
                return {"configured": False, "error": resp.text}
        except Exception as e:
            return {"configured": False, "error": str(e)}

    def submit_bracket_order(
        self,
        symbol: str,
        qty: int,
        side: str = "buy",
        stop_loss_price: Optional[float] = None,
        take_profit_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Submits an institutional Bracket Order to Alpaca Paper Trading:
        Simultaneously places an Entry order + Stop-Loss + Profit Target.
        """
        if not self.is_configured():
            return {"status": "FAILED", "reason": "Alpaca API keys not configured."}

        order_payload: Dict[str, Any] = {
            "symbol": symbol.upper(),
            "qty": qty,
            "side": side.lower(),
            "type": "market",
            "time_in_force": "day"
        }

        # Bracket order parameters
        if stop_loss_price or take_profit_price:
            order_payload["order_class"] = "bracket"
            if take_profit_price:
                order_payload["take_profit"] = {"limit_price": round(take_profit_price, 2)}
            if stop_loss_price:
                order_payload["stop_loss"] = {"stop_price": round(stop_loss_price, 2)}

        try:
            resp = requests.post(
                f"{self.BASE_URL}/v2/orders",
                headers=self.headers,
                json=order_payload,
                timeout=10
            )
            if resp.status_code in [200, 201]:
                return {"status": "SUBMITTED", "order": resp.json()}
            else:
                return {"status": "FAILED", "error": resp.text}
        except Exception as e:
            return {"status": "FAILED", "error": str(e)}

