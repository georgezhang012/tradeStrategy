"""
E*TRADE Automated Institutional Portfolio Trader
=================================================
Automates portfolio rebalancing and execution for an E*TRADE brokerage account.
Designed for accounts starting at $10,000 (or customized capital).

Key Features:
1. Multi-Agent Allocation Sync: Reads optimal weights from the institutional multi-agent system.
2. Whole-Share Sizing & Cash Buffering: Computes integer share lots and retains a risk buffer.
3. Pre-Trade Validation & Dry-Run Mode: Simulates every order ticket before live transmission.
4. OAuth 1.0a Session Manager: Handles PIN authentication and persistent token caching.
5. Dual Environment Support: Sandbox (paper simulation) and Live Production modes.
"""

import os
import sys
import json
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# Load environment variables if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from sp500_nasdaq_screener import SP500NasdaqScreener
from portfolio_optimizer import PortfolioOptimizer
from historical_data_feed import HistoricalDataFeed


TOKEN_CACHE_FILE = Path.home() / ".etrade_tokens.json"


class ETradePortfolioTrader:
    """
    Automated execution engine connecting Multi-Agent portfolio targets
    to an E*TRADE trading account.
    """

    def __init__(
        self,
        balance: float = 10000.0,
        sandbox: bool = True,
        consumer_key: Optional[str] = None,
        consumer_secret: Optional[str] = None,
        dry_run: bool = True
    ):
        self.balance = float(balance)
        self.sandbox = sandbox
        self.dry_run = dry_run
        self.consumer_key = consumer_key or os.getenv("ETRADE_CONSUMER_KEY", "")
        self.consumer_secret = consumer_secret or os.getenv("ETRADE_CONSUMER_SECRET", "")
        self.account_id_key = os.getenv("ETRADE_ACCOUNT_ID_KEY", "")

        self.tokens: Dict[str, str] = self._load_cached_tokens()
        self.accounts_api = None
        self.order_api = None
        self.market_api = None

    def _load_cached_tokens(self) -> Dict[str, str]:
        if TOKEN_CACHE_FILE.exists():
            try:
                with open(TOKEN_CACHE_FILE, "r") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_cached_tokens(self, tokens: Dict[str, str]):
        try:
            with open(TOKEN_CACHE_FILE, "w") as f:
                json.dump(tokens, f, indent=2)
        except Exception as e:
            print(f"[-] Warning: Failed to save tokens to {TOKEN_CACHE_FILE}: {e}")

    def authenticate_interactive(self) -> bool:
        """Guides user through E*TRADE OAuth 1.0a interactive authorization."""
        if not self.consumer_key or not self.consumer_secret:
            print("[-] Error: ETRADE_CONSUMER_KEY and ETRADE_CONSUMER_SECRET must be set in .env or environment.")
            return False

        try:
            import pyetrade
            oauth = pyetrade.ETradeOAuth(self.consumer_key, self.consumer_secret)
            auth_url = oauth.get_request_token()
            print("\n" + "=" * 80)
            print("                 E*TRADE OAUTH 1.0a AUTHORIZATION REQUEST")
            print("=" * 80)
            print("1. Please open the following URL in your web browser:")
            print(f"   \033[94m{auth_url}\033[0m")
            print("2. Log into your E*TRADE account and grant authorization.")
            print("3. E*TRADE will display a verification code (PIN).")
            print("-" * 80)
            verifier_code = input("Enter the E*TRADE verification PIN code: ").strip()

            tokens = oauth.get_access_token(verifier_code)
            self.tokens = {
                "oauth_token": tokens.get("oauth_token", ""),
                "oauth_token_secret": tokens.get("oauth_token_secret", ""),
                "saved_at": datetime.now().isoformat()
            }
            self._save_cached_tokens(self.tokens)
            print(f"[+] Successfully authenticated! Tokens saved to {TOKEN_CACHE_FILE}\n")
            return True
        except Exception as e:
            print(f"[-] Authorization error: {e}")
            return False

    def init_client_apis(self) -> bool:
        """Initializes pyetrade API wrappers if access tokens exist."""
        if self.dry_run:
            return True

        if not self.tokens.get("oauth_token") or not self.tokens.get("oauth_token_secret"):
            print("[-] No valid access tokens found. Please run with `--auth` to link your E*TRADE account.")
            return False

        try:
            import pyetrade
            tok = self.tokens["oauth_token"]
            secret = self.tokens["oauth_token_secret"]
            self.accounts_api = pyetrade.ETradeAccounts(
                self.consumer_key, self.consumer_secret, tok, secret, dev=self.sandbox
            )
            self.order_api = pyetrade.ETradeOrder(
                self.consumer_key, self.consumer_secret, tok, secret, dev=self.sandbox
            )
            self.market_api = pyetrade.ETradeMarket(
                self.consumer_key, self.consumer_secret, tok, secret, dev=self.sandbox
            )
            return True
        except Exception as e:
            print(f"[-] Failed to initialize E*TRADE client APIs: {e}")
            return False

    def fetch_live_cash_balance(self) -> float:
        """Retrieves actual settled cash balance from E*TRADE account."""
        if self.dry_run or not self.accounts_api:
            return self.balance

        try:
            account_list = self.accounts_api.list_accounts()
            accounts = account_list.get("AccountListResponse", {}).get("Accounts", {}).get("Account", [])
            if not accounts:
                print("[-] No accounts found for this E*TRADE user. Using local balance.")
                return self.balance

            target_acc = accounts[0]
            if self.account_id_key:
                for a in accounts:
                    if a.get("accountIdKey") == self.account_id_key:
                        target_acc = a
                        break
            self.account_id_key = target_acc.get("accountIdKey", "")

            balance_resp = self.accounts_api.get_account_balance(self.account_id_key)
            cash_avail = float(balance_resp.get("BalanceResponse", {}).get("Computed", {}).get("cashAvailableForInvestment", self.balance))
            print(f"[+] Live E*TRADE Account ID: {target_acc.get('accountId', 'N/A')} | Cash Available: ${cash_avail:,.2f}")
            return cash_avail
        except Exception as e:
            print(f"[-] Warning: Failed to query live balance from E*TRADE ({e}). Using default ${self.balance:,.2f}")
            return self.balance

    def get_current_stock_price(self, symbol: str) -> float:
        """Fetches current stock price from E*TRADE market quote or high-fidelity feed."""
        if not self.dry_run and self.market_api:
            try:
                quote_resp = self.market_api.get_quote([symbol])
                quote_data = quote_resp.get("QuoteResponse", {}).get("QuoteData", [])
                if quote_data:
                    p = float(quote_data[0].get("All", {}).get("lastTrade", 0.0))
                    if p > 0:
                        return p
            except Exception:
                pass

        # Reference price feed
        now_dt = datetime(2026, 10, 12)
        return HistoricalDataFeed.get_target_price_at_date(symbol, now_dt)

    def generate_portfolio_allocation(self, top_n: int = 15) -> List[Dict[str, Any]]:
        """
        Calculates exact target dollar allocations, integer share sizing,
        and cash buffering for the top institutional compounders.
        """
        # 1. Screen top cross-sector compounders
        screened = SP500NasdaqScreener.screen_outperformers(horizon_years=2, min_alpha=0.0)
        selected = []
        sector_counts: Dict[str, int] = {}
        for b in screened:
            sec = b.get("sector", "Other")
            if sector_counts.get(sec, 0) < 3:
                sector_counts[sec] = sector_counts.get(sec, 0) + 1
                selected.append(b)
            if len(selected) == top_n:
                break

        # Fallback if sector limit was too strict
        if len(selected) < top_n:
            for b in screened:
                if b["symbol"] not in [s["symbol"] for s in selected]:
                    selected.append(b)
                if len(selected) == top_n:
                    break

        symbols = [s["symbol"] for s in selected]

        # 2. Compute optimal weights
        try:
            opt = PortfolioOptimizer.optimize_max_sharpe(symbols)
            weights = opt["weights"]
        except Exception:
            weights = {sym: 1.0 / len(symbols) for sym in symbols}

        # 3. Calculate whole-share integer order quantities
        # Reserve 2.0% cash buffer to accommodate price slippage and commissions
        investable_cash = self.balance * 0.98

        allocation_plan = []
        allocated_items = []

        for item in selected:
            sym = item["symbol"]
            w = weights.get(sym, 1.0 / len(symbols))
            target_dollars = investable_cash * w
            price = self.get_current_stock_price(sym)
            shares = int(target_dollars / price) if price > 0 else 0
            cost = round(shares * price, 2)

            allocated_items.append({
                "item": item,
                "symbol": sym,
                "price": price,
                "target_weight": w,
                "target_dollars": target_dollars,
                "shares": shares,
                "cost": cost
            })

        # Greedy whole-share cash optimizer: reallocate remaining cash to holdings most underweight
        spent = sum(x["cost"] for x in allocated_items)
        residual = investable_cash - spent

        # Iteratively allocate whole shares while residual cash permits
        while residual > 50.0:
            candidates = [x for x in allocated_items if 0 < x["price"] <= residual]
            if not candidates:
                break
            # Pick candidate whose current allocated weight is most below its target
            candidates.sort(key=lambda x: (x["cost"] / investable_cash) - x["target_weight"])
            best = candidates[0]
            best["shares"] += 1
            best["cost"] = round(best["shares"] * best["price"], 2)
            residual -= best["price"]

        for x in allocated_items:
            item = x["item"]
            sym = x["symbol"]
            allocation_plan.append({
                "symbol": sym,
                "name": item["name"],
                "sector": item["sector"],
                "cagr_2y": item.get("cagr_2y", item.get("cagr", 0.0)),
                "alpha_vs_spy": item.get("alpha_over_sp500", 0.0),
                "target_weight_pct": round(x["target_weight"] * 100.0, 1),
                "target_dollars": round(x["target_dollars"], 2),
                "current_price": round(x["price"], 2),
                "shares_to_buy": x["shares"],
                "estimated_cost": x["cost"]
            })

        # Sort by target dollar descending
        allocation_plan.sort(key=lambda x: x["target_dollars"], reverse=True)
        return allocation_plan

    def print_execution_tickets(self, plan: List[Dict[str, Any]]):
        """Prints a comprehensive, institutional order dossier."""
        total_cost = sum(p["estimated_cost"] for p in plan)
        cash_left = self.balance - total_cost

        print("\n" + "=" * 115)
        print(f"         E*TRADE INSTITUTIONAL PORTFOLIO EXECUTION DOSSIER (INITIAL BALANCE: ${self.balance:,.2f})")
        print("=" * 115)
        print(f"  • Execution Mode:    {'DRY-RUN SIMULATION (Safe Mode)' if self.dry_run else 'LIVE ORDER SUBMISSION'}")
        print(f"  • Environment:       {'E*TRADE Sandbox (Dev)' if self.sandbox else 'E*TRADE Production (Live)'}")
        print(f"  • Holdings Breadth:  {len(plan)} Institutional Compounders across Diverse Sectors")
        print(f"  • Target Deployment: ${total_cost:,.2f} ({(total_cost/self.balance)*100:.1f}%) | Cash Buffer: ${cash_left:,.2f} ({(cash_left/self.balance)*100:.1f}%)")
        print("-" * 115)
        print(f"{'SYM':<6} {'COMPANY NAME':<23} {'GICS SECTOR':<20} {'2Y CAGR':>8} {'WT (%)':>7} {'PRICE':>9} {'SHARES':>7} {'NOTIONAL':>11} {'STATUS':<15}")
        print("-" * 115)

        for p in plan:
            status = "SIMULATED BUY" if self.dry_run else "READY TO SEND"
            if p["shares_to_buy"] == 0:
                status = "SKIPPED (0 SHS)"
            print(
                f"{p['symbol']:<6} {p['name'][:22]:<23} {p['sector'][:19]:<20} "
                f"{p['cagr_2y']:>7.1f}% {p['target_weight_pct']:>6.1f}% "
                f"${p['current_price']:>8.2f} {p['shares_to_buy']:>7} "
                f"${p['estimated_cost']:>10.2f} {status:<15}"
            )

        print("-" * 115)
        print(f"{'TOTAL ALLOCATED':<61} {sum(p['target_weight_pct'] for p in plan):>6.1f}% {'':>9} {sum(p['shares_to_buy'] for p in plan):>7} ${total_cost:>10.2f}")
        print(f"UNALLOCATED CASH BUFFER: ${cash_left:,.2f}\n")

    def execute_live_orders(self, plan: List[Dict[str, Any]]):
        """Sends orders to E*TRADE brokerage account."""
        if self.dry_run:
            print("[i] Dry-run enabled. No orders were sent to E*TRADE.")
            return

        if not self.order_api or not self.account_id_key:
            print("[-] Cannot submit live orders: API client or Account ID Key not configured.")
            return

        print("\n[!] CAUTION: About to submit real orders to your E*TRADE account!")
        confirm = input("Type 'CONFIRM' to submit all orders: ").strip()
        if confirm != "CONFIRM":
            print("[-] Execution cancelled by user.")
            return

        for p in plan:
            shs = p["shares_to_buy"]
            sym = p["symbol"]
            if shs <= 0:
                continue

            try:
                print(f"[*] Placing market BUY order for {shs} shares of {sym}...")
                # pyetrade equity order payload structure
                order_spec = {
                    "orderType": "EQ",
                    "clientOrderId": f"AGY_{sym}_{int(datetime.now().timestamp())}",
                    "Order": [{
                        "allOrNone": "false",
                        "priceType": "MARKET",
                        "orderTerm": "GOOD_FOR_DAY",
                        "marketSession": "REGULAR",
                        "Instrument": [{
                            "Product": {"securityType": "EQ", "symbol": sym},
                            "orderAction": "BUY",
                            "quantityType": "QUANTITY",
                            "quantity": shs
                        }]
                    }]
                }
                # Preview order first
                preview_resp = self.order_api.preview_equity_order(self.account_id_key, order_spec)
                preview_id = preview_resp.get("PreviewOrderResponse", {}).get("orderId", "")
                
                # Place order
                place_resp = self.order_api.place_equity_order(self.account_id_key, order_spec, preview_id)
                order_num = place_resp.get("PlaceOrderResponse", {}).get("OrderIds", [{}])[0].get("orderId", "SUBMITTED")
                print(f"    [+] SUCCESS: Order #{order_num} executed for {shs} shares of {sym}")
            except Exception as e:
                print(f"    [-] FAILED to execute order for {sym}: {e}")


def main():
    parser = argparse.ArgumentParser(description="E*TRADE Automated Institutional Portfolio Trader")
    parser.add_argument("--balance", type=float, default=10000.0, help="Initial investment capital (default: $10,000)")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Simulate execution without sending orders (default: True)")
    parser.add_argument("--live", action="store_true", help="Enable live E*TRADE order execution (disables dry-run)")
    parser.add_argument("--auth", action="store_true", help="Launch interactive OAuth 1.0a authorization flow")
    parser.add_argument("--sandbox", action="store_true", default=True, help="Use E*TRADE Sandbox environment")
    parser.add_argument("--production", action="store_true", help="Use E*TRADE Production environment (disables sandbox)")
    parser.add_argument("--top-n", type=int, default=15, help="Number of diversified compounders (default: 15)")

    args = parser.parse_args()

    is_dry_run = not args.live
    is_sandbox = not args.production

    trader = ETradePortfolioTrader(
        balance=args.balance,
        sandbox=is_sandbox,
        dry_run=is_dry_run
    )

    if args.auth:
        trader.authenticate_interactive()
        return

    # Check live balance if client credentials configured and not purely dry-run
    if not is_dry_run:
        trader.init_client_apis()
        trader.fetch_live_cash_balance()

    plan = trader.generate_portfolio_allocation(top_n=args.top_n)
    trader.print_execution_tickets(plan)

    if not is_dry_run:
        trader.execute_live_orders(plan)
    else:
        print("💡 Next Steps to Execute on E*TRADE:")
        print("  1. Copy `.env.example` to `.env` and fill in your E*TRADE Consumer Key and Secret.")
        print("  2. Run `python3 etrade_trader.py --auth` to obtain your access PIN and save your session.")
        print("  3. Run `python3 etrade_trader.py --balance 10000 --live` to review and submit live orders.\n")


if __name__ == "__main__":
    main()
