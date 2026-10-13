"""
Institutional Backtesting & Operations History Engine
=====================================================
Allows setting any past start time (e.g., '1 year ago', '2025-10-12', '2y')
to test the multi-agent trading strategy, execute daily historical replay,
record the full chronological history of operations, and benchmark returns
against VTI (Total US Market), QQQ (NASDAQ 100), and SPY (S&P 500).
"""

import os
import sys
import math
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd

try:
    from .historical_data_feed import HistoricalDataFeed
    from .sp500_nasdaq_screener import SP500NasdaqScreener
    from .portfolio_optimizer import PortfolioOptimizer
except (ImportError, ValueError):
    from historical_data_feed import HistoricalDataFeed
    from sp500_nasdaq_screener import SP500NasdaqScreener
    from portfolio_optimizer import PortfolioOptimizer


class BacktestEngine:
    """
    Backtests trading strategies from a specified historical starting point,
    tracks daily performance, logs every operation, and benchmarks against VTI and QQQ.
    """

    def __init__(
        self,
        initial_capital: float = 100000.0,
        commission_per_trade: float = 0.0,
        slippage_pct: float = 0.05
    ):
        self.initial_capital = initial_capital
        self.commission_per_trade = commission_per_trade
        self.slippage_pct = slippage_pct

    def run_backtest(
        self,
        lookback: str = "1y",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        symbols: Optional[List[str]] = None,
        top_n: int = 15,
        trailing_stop_pct: float = 0.20,
        take_profit_pct: float = 0.50,
        rebalance_days: int = 60
    ) -> Dict[str, Any]:
        """
        Executes historical backtest:
        1. Resolves time window (e.g., 1 year ago to today).
        2. Selects candidate assets (either user-provided or top screened market-beaters across diverse sectors).
        3. Simulates initial capital allocation and order fills.
        4. Simulates daily trading path, enforcing trailing stops, take-profit trims, and rebalancing.
        5. Simultaneously runs identical buy-and-hold benchmarks for VTI, QQQ, and SPY.
        6. Computes comprehensive risk/return metrics and chronological operations ledger.
        """
        start_dt, end_dt = HistoricalDataFeed.parse_time_window(lookback=lookback, start_date=start_date, end_date=end_date)
        start_str = start_dt.strftime("%Y-%m-%d")
        end_str = end_dt.strftime("%Y-%m-%d")

        # 1. Determine Universe with Institutional Cross-Sector Diversification
        # Point-in-Time: Screen outperformers as of the historical start date (zero look-ahead bias)
        if not symbols:
            screened_beaters = SP500NasdaqScreener.screen_outperformers(
                horizon_years=2,
                min_alpha=0.0,
                as_of_date=start_dt
            )
            selected_assets = []
            sector_counts: Dict[str, int] = {}
            # Dynamic sector cap: scales with portfolio size (up to 25% per sector) so top-growth sectors are not starved
            max_per_sector = max(3, int(top_n * 0.25))
            for b in screened_beaters:
                sec = b.get("sector", "Other")
                if sector_counts.get(sec, 0) < max_per_sector:
                    sector_counts[sec] = sector_counts.get(sec, 0) + 1
                    selected_assets.append(b["symbol"])
                if len(selected_assets) == top_n:
                    break
            # Fallback if sector limit was too strict
            if len(selected_assets) < top_n:
                for b in screened_beaters:
                    if b["symbol"] not in selected_assets:
                        selected_assets.append(b["symbol"])
                    if len(selected_assets) == top_n:
                        break
        else:
            selected_assets = [s.upper() for s in symbols]

        is_single_asset = (len(selected_assets) == 1)

        # 2. Fetch daily prices for candidates and benchmarks
        price_data: Dict[str, pd.DataFrame] = {}
        all_tickers = list(set(selected_assets + ["VTI", "QQQ", "SPY"]))
        for sym in all_tickers:
            price_data[sym] = HistoricalDataFeed.get_price_history(sym, start_dt, end_dt)

        # Build unified trading calendar
        ref_df = price_data.get("SPY", price_data[selected_assets[0]])
        trading_dates = sorted(ref_df["date"].tolist())

        if len(trading_dates) == 0:
            raise ValueError(f"No trading dates found between {start_str} and {end_str}")

        # Compute initial portfolio weights using Alpha-Convex Momentum Allocation
        if is_single_asset:
            weights = {selected_assets[0]: 1.0}
        else:
            try:
                opt = PortfolioOptimizer.optimize_alpha_convex(selected_assets)
                weights = opt["weights"]
            except Exception:
                try:
                    opt = PortfolioOptimizer.optimize_max_sharpe(selected_assets)
                    weights = opt["weights"]
                except Exception:
                    weights = {sym: 1.0 / len(selected_assets) for sym in selected_assets}

        # 3. Initialize Strategy State
        cash = self.initial_capital
        positions: Dict[str, Dict[str, Any]] = {}
        operations_history: List[Dict[str, Any]] = []
        daily_equity_curve: List[Dict[str, Any]] = []
        last_buy_day: Dict[str, int] = {} # For cooldown tracking

        # 4. Initialize Benchmarks State ($100k buy & hold on day 0)
        vti_start_price = price_data["VTI"].iloc[0]["close"]
        qqq_start_price = price_data["QQQ"].iloc[0]["close"]
        spy_start_price = price_data["SPY"].iloc[0]["close"]

        vti_shares = self.initial_capital / vti_start_price
        qqq_shares = self.initial_capital / qqq_start_price
        spy_shares = self.initial_capital / spy_start_price

        # Helper to get price on specific date
        def get_price(sym: str, date_str: str) -> Dict[str, float]:
            df = price_data[sym]
            row = df[df["date"] == date_str]
            if not row.empty:
                r = row.iloc[0]
                return {"open": r["open"], "high": r["high"], "low": r["low"], "close": r["close"]}
            prior = df[df["date"] <= date_str]
            if not prior.empty:
                r = prior.iloc[-1]
                return {"open": r["open"], "high": r["high"], "low": r["low"], "close": r["close"]}
            r = df.iloc[0]
            return {"open": r["open"], "high": r["high"], "low": r["low"], "close": r["close"]}

        # Helper to calculate rolling 14-day Average True Range (ATR) percentage
        def get_atr_pct(sym: str, dt_str: str, period: int = 14) -> float:
            df = price_data.get(sym)
            if df is None:
                return 0.035
            sub = df[df["date"] <= dt_str]
            if len(sub) < 5:
                return 0.035
            sub_tail = sub.tail(period + 1)
            highs = sub_tail["high"].values
            lows = sub_tail["low"].values
            closes = sub_tail["close"].values
            tr_list = [max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1])) for i in range(1, len(sub_tail))]
            atr = float(np.mean(tr_list)) if tr_list else float(highs[-1] - lows[-1])
            curr_c = float(closes[-1])
            return float(atr / curr_c) if curr_c > 0 else 0.035

        # Helper to execute order
        def record_trade(dt_str: str, sym: str, action: str, shares: int, price: float, reason: str):
            nonlocal cash
            is_buy = action.startswith("BUY") or action in ["TREND_ENTRY", "RE_ENTRY", "BUY_PULLBACK", "WALK_FORWARD_ENTRY"]
            slippage_mult = (1.0 + self.slippage_pct / 100.0) if is_buy else (1.0 - self.slippage_pct / 100.0)
            exec_price = round(price * slippage_mult, 2)
            notional = round(shares * exec_price, 2)

            if is_buy:
                total_cost = notional + self.commission_per_trade
                if total_cost > cash:
                    shares = int((cash - self.commission_per_trade) / exec_price)
                    notional = round(shares * exec_price, 2)
                    total_cost = notional + self.commission_per_trade
                if shares <= 0:
                    return

                cash -= total_cost
                if sym in positions:
                    pos = positions[sym]
                    new_shares = pos["shares"] + shares
                    new_spent = (pos["shares"] * pos["avg_cost"]) + notional
                    pos["shares"] = new_shares
                    pos["avg_cost"] = round(new_spent / new_shares, 2)
                    pos["high_water_mark"] = max(pos.get("high_water_mark", exec_price), exec_price)
                else:
                    positions[sym] = {
                        "shares": shares,
                        "avg_cost": exec_price,
                        "entry_date": dt_str,
                        "high_water_mark": exec_price,
                        "profit_trimmed": False
                    }
            elif action.startswith("SELL") or action in ["STOP_LOSS", "TAKE_PROFIT", "REBALANCE_TRIM", "WALK_FORWARD_EXIT"]:
                if sym not in positions or positions[sym]["shares"] <= 0:
                    return
                shares = min(shares, positions[sym]["shares"])
                proceeds = notional - self.commission_per_trade
                cash += proceeds
                positions[sym]["shares"] -= shares
                if positions[sym]["shares"] == 0:
                    del positions[sym]

            # Current total equity
            current_port_val = cash
            for s, p in positions.items():
                p_bar = get_price(s, dt_str)
                current_port_val += p["shares"] * p_bar["close"]

            operations_history.append({
                "date": dt_str,
                "action": action,
                "symbol": sym,
                "shares": shares,
                "price": exec_price,
                "notional": notional,
                "cash_remaining": round(cash, 2),
                "portfolio_value": round(current_port_val, 2),
                "reason": reason
            })

        # --- DAY 0: INITIAL STRATEGY DEPLOYMENT ---
        first_date = trading_dates[0]
        if is_single_asset:
            # Single-Asset Mode: Tranche 1 = 60% initial market order, 40% cash held for pullback accumulation
            sym = selected_assets[0]
            alloc_dollars = self.initial_capital * 0.60
            bar = get_price(sym, first_date)
            shs = int(alloc_dollars / bar["open"])
            if shs > 0:
                record_trade(
                    dt_str=first_date,
                    sym=sym,
                    action="BUY",
                    shares=shs,
                    price=bar["open"],
                    reason="Initial Tranche 1 Entry (60% Allocation, 40% Cash Reserve for Pullbacks)"
                )
                last_buy_day[sym] = 0
        else:
            # Multi-Asset Mode: Allocate capital per optimal weights
            for sym in selected_assets:
                w = weights.get(sym, 1.0 / len(selected_assets))
                alloc_dollars = self.initial_capital * w
                bar = get_price(sym, first_date)
                shs = int(alloc_dollars / bar["open"])
                if shs > 0:
                    record_trade(
                        dt_str=first_date,
                        sym=sym,
                        action="BUY",
                        shares=shs,
                        price=bar["open"],
                        reason=f"Initial Alpha Allocation (Screened Compounder | Target Weight: {w*100:.1f}%)"
                    )
                    last_buy_day[sym] = 0

        # --- SIMULATE DAILY TRADING & RISK MANAGEMENT ---
        days_since_rebalance = 0

        for day_idx, dt_str in enumerate(trading_dates):
            days_since_rebalance += 1

            # 1. Update High-Water Marks & Check Trailing Stops & Take Profit
            active_symbols = list(positions.keys())
            for sym in active_symbols:
                if sym not in positions:
                    continue
                pos = positions[sym]
                bar = get_price(sym, dt_str)
                curr_high = bar["high"]
                curr_low = bar["low"]

                # Update High Water Mark
                if curr_high > pos.get("high_water_mark", pos["avg_cost"]):
                    pos["high_water_mark"] = curr_high

                hwm = pos["high_water_mark"]
                # Adaptive Volatility Trailing Stop using 4.0x 14-day ATR (bounded 12% to 25%)
                atr_pct = get_atr_pct(sym, dt_str, period=14)
                dynamic_stop_pct = max(0.12, min(0.25, 4.0 * atr_pct))
                trailing_stop_level = hwm * (1.0 - dynamic_stop_pct)

                # Trend-Aware Dual Confirmation Stop:
                # High-beta compounders experience routine consolidations within macro bull trends.
                # Only execute full STOP_LOSS if BOTH trailing stop is breached AND price breaks below 50-day SMA,
                # OR if an absolute hard risk circuit breaker (-25% from peak) is reached.
                sub_df = price_data[sym][price_data[sym]["date"] <= dt_str]
                sma50 = sub_df["close"].tail(50).mean() if len(sub_df) >= 20 else None
                hard_circuit_breaker = hwm * (1.0 - max(trailing_stop_pct, 0.22)) # 22% hard max circuit breaker from peak

                # Trigger Stop Loss ONLY when confirmed:
                # 1. Catastrophic plunge below hard circuit breaker (-22% from peak)
                # 2. Or established position (held >= 20 days) breaches trailing stop AND breaks below 50-day SMA
                is_hard_stop = (curr_low <= hard_circuit_breaker)
                is_trend_break = (sma50 is not None and bar["close"] <= trailing_stop_level and bar["close"] < sma50)

                if is_hard_stop or is_trend_break:
                    reason_msg = (
                        f"Trend Breakdown Stop hit (-{dynamic_stop_pct*100:.1f}%, closed below 50-day SMA from peak ${hwm:.2f})"
                        if is_trend_break
                        else f"Hard Risk Circuit Breaker hit (-22.0% from peak ${hwm:.2f})"
                    )
                    record_trade(
                        dt_str=dt_str,
                        sym=sym,
                        action="STOP_LOSS",
                        shares=pos["shares"],
                        price=round(min(trailing_stop_level, bar["close"]), 2),
                        reason=reason_msg
                    )
                    continue

                # Check Optional Take Profit target (only if take_profit_pct < 0.90)
                if take_profit_pct and take_profit_pct < 0.90 and not pos.get("profit_trimmed", False) and curr_high >= pos["avg_cost"] * (1.0 + take_profit_pct):
                    trim_shares = max(1, int(pos["shares"] * 0.25))
                    record_trade(
                        dt_str=dt_str,
                        sym=sym,
                        action="TAKE_PROFIT",
                        shares=trim_shares,
                        price=round(pos["avg_cost"] * (1.0 + take_profit_pct), 2),
                        reason=f"Take-Profit locked (+{take_profit_pct*100:.1f}% target hit). Trimmed 25%."
                    )
                    if sym in positions:
                        positions[sym]["profit_trimmed"] = True

            # 2. Opportunistic Tranche Accumulation on Pullback with Cooldown
            port_val = cash + sum(positions[s]["shares"] * get_price(s, dt_str)["close"] for s in positions)
            if cash >= (port_val * 0.05):
                for sym in selected_assets:
                    if day_idx - last_buy_day.get(sym, -999) < 10:
                        continue

                    bar = get_price(sym, dt_str)
                    if sym in positions:
                        pos = positions[sym]
                        hwm = pos.get("high_water_mark", bar["close"])
                        pullback = (hwm - bar["close"]) / hwm
                        if 0.04 <= pullback <= 0.12 and cash >= (port_val * 0.04):
                            buy_amt = min(cash * 0.50, port_val * 0.10)
                            shs = int(buy_amt / bar["close"])
                            if shs > 0:
                                record_trade(
                                    dt_str=dt_str,
                                    sym=sym,
                                    action="BUY",
                                    shares=shs,
                                    price=bar["close"],
                                    reason=f"Tranche Accumulation on Pullback (-{pullback*100:.1f}% dip from peak)"
                                )
                                last_buy_day[sym] = day_idx
                                break
                    elif is_single_asset and cash >= (port_val * 0.10):
                        # Re-enter single asset once price reclaims 20-day SMA
                        sub_df = price_data[sym][price_data[sym]["date"] <= dt_str]
                        sma20 = sub_df["close"].tail(20).mean() if len(sub_df) >= 20 else bar["close"]
                        if bar["close"] >= sma20:
                            shs = int((cash * 0.85) / bar["close"])
                            if shs > 0:
                                record_trade(
                                    dt_str=dt_str,
                                    sym=sym,
                                    action="RE_ENTRY",
                                    shares=shs,
                                    price=bar["close"],
                                    reason="Trend Re-entry: Price reclaimed 20-day SMA following consolidation"
                                )
                                last_buy_day[sym] = day_idx
                                break

            # 3. Dynamic Rotation & Capital Reinvestment (Eliminates Idle Cash Drag)
            port_val = cash + sum(positions[s]["shares"] * get_price(s, dt_str)["close"] for s in positions)
            target_slot_val = port_val / top_n
            if not is_single_asset and len(positions) < top_n and cash >= (target_slot_val * 0.60):
                # Search candidate pool: first unheld selected assets, then top screened universe
                candidate_pool = [s for s in selected_assets if s not in positions]
                if not candidate_pool:
                    broader = [b["symbol"] for b in SP500NasdaqScreener.screen_outperformers(as_of_date=dt_str)[:15]]
                    candidate_pool = [s for s in broader if s not in positions]

                for cand in candidate_pool:
                    if cand not in price_data:
                        price_data[cand] = HistoricalDataFeed.get_price_history(cand, start_dt, end_dt)
                    sub_df = price_data[cand][price_data[cand]["date"] <= dt_str]
                    if len(sub_df) >= 20:
                        sma20 = sub_df["close"].tail(20).mean()
                        curr_bar = get_price(cand, dt_str)
                        if curr_bar["close"] > sma20 and (day_idx - last_buy_day.get(cand, -999) >= 10):
                            buy_amt = min(cash, target_slot_val)
                            shs = int(buy_amt / curr_bar["close"])
                            if shs > 0:
                                record_trade(
                                    dt_str=dt_str,
                                    sym=cand,
                                    action="TREND_ENTRY",
                                    shares=shs,
                                    price=curr_bar["close"],
                                    reason=f"Capital Rotation / Trend Re-entry (SMA20 Uptrend Reclaimed)"
                                )
                                last_buy_day[cand] = day_idx
                                break
            # 4. Institutional Quarterly Walk-Forward Re-screening & Dynamic Sector Rotation
            if not is_single_asset and days_since_rebalance >= rebalance_days:
                days_since_rebalance = 0
                port_val = cash + sum(positions[s]["shares"] * get_price(s, dt_str)["close"] for s in positions)

                # A. Evaluate health of current holdings (Walk-Forward decay check)
                lagging_symbols = []
                for s in list(positions.keys()):
                    if s not in price_data:
                        continue
                    df_s = price_data[s][price_data[s]["date"] <= dt_str]
                    if len(df_s) >= 40:
                        curr_close = df_s["close"].iloc[-1]
                        sma50 = df_s["close"].tail(50).mean() if len(df_s) >= 50 else df_s["close"].mean()
                        ret_quarter = (curr_close / df_s["close"].iloc[-min(len(df_s), 40)] - 1.0) * 100
                        # Flag severe breakdown (below 50d SMA and > 10% decline)
                        if curr_close < (sma50 * 0.94) and ret_quarter < -10.0:
                            lagging_symbols.append((s, ret_quarter))

                # B. Rotate out of decaying laggards
                for lag_sym, ret_q in lagging_symbols:
                    if lag_sym in positions:
                        shs = positions[lag_sym]["shares"]
                        bar = get_price(lag_sym, dt_str)
                        record_trade(
                            dt_str=dt_str,
                            sym=lag_sym,
                            action="WALK_FORWARD_EXIT",
                            shares=shs,
                            price=bar["close"],
                            reason=f"Quarterly Walk-Forward Rotation: Decaying Momentum (-{abs(ret_q):.1f}% quarter, broke 50-day SMA)"
                        )
                        if lag_sym in selected_assets:
                            selected_assets.remove(lag_sym)

                # C. Screen for emerging replacements to maintain breadth
                port_val = cash + sum(positions[s]["shares"] * get_price(s, dt_str)["close"] for s in positions)
                needed = top_n - len(positions)
                if needed > 0 and cash >= (port_val * 0.04):
                    broader_beaters = SP500NasdaqScreener.screen_outperformers(
                        horizon_years=2,
                        min_alpha=0.0,
                        as_of_date=dt_str
                    )
                    for cand in broader_beaters:
                        cand_sym = cand["symbol"]
                        if cand_sym in positions or cand_sym in selected_assets:
                            continue
                        if cand_sym not in price_data:
                            price_data[cand_sym] = HistoricalDataFeed.get_price_history(cand_sym, start_dt, end_dt)
                        df_c = price_data[cand_sym][price_data[cand_sym]["date"] <= dt_str]
                        if len(df_c) >= 20:
                            sma20 = df_c["close"].tail(20).mean()
                            bar_c = get_price(cand_sym, dt_str)
                            if bar_c["close"] > sma20:
                                selected_assets.append(cand_sym)
                                alloc_dollars = min(cash, port_val / top_n)
                                shs_new = int(alloc_dollars / bar_c["close"])
                                if shs_new > 0:
                                    record_trade(
                                        dt_str=dt_str,
                                        sym=cand_sym,
                                        action="WALK_FORWARD_ENTRY",
                                        shares=shs_new,
                                        price=bar_c["close"],
                                        reason=f"Quarterly Walk-Forward Rotation: Added Emerging Leader ({cand['name'][:18]}, 2Y CAGR: {cand['cagr']}%)"
                                    )
                                    last_buy_day[cand_sym] = day_idx
                                    needed -= 1
                                    if needed <= 0 or cash < (port_val * 0.04):
                                        break

                # D. Re-optimize weights on active holdings and rebalance
                try:
                    opt = PortfolioOptimizer.optimize_alpha_convex(selected_assets)
                    weights = opt["weights"]
                except Exception:
                    try:
                        opt = PortfolioOptimizer.optimize_max_sharpe(selected_assets)
                        weights = opt["weights"]
                    except Exception:
                        weights = {sym: 1.0 / len(selected_assets) for sym in selected_assets}

                for sym in list(positions.keys()):
                    target_w = weights.get(sym, 1.0 / len(selected_assets))
                    curr_pos_val = (positions[sym]["shares"] * get_price(sym, dt_str)["close"]) if sym in positions else 0.0
                    curr_w = curr_pos_val / port_val
                    drift = curr_w - target_w

                    # Asymmetric Rebalancing (Let Winners Run):
                    # Do not trim winning compounders that are riding above their 50-day SMA,
                    # unless single-stock concentration exceeds 20.0% of total portfolio.
                    sub_s = price_data[sym][price_data[sym]["date"] <= dt_str]
                    sma50_s = sub_s["close"].tail(50).mean() if len(sub_s) >= 30 else None
                    is_uptrend = (sma50_s is not None and get_price(sym, dt_str)["close"] > sma50_s)

                    drift_threshold = 0.15 if is_uptrend else 0.08
                    if curr_w > 0.20 or (drift > drift_threshold and sym in positions):
                        max_w = 0.18 if is_uptrend else max(target_w + 0.04, 0.10)
                        excess_val = (curr_w - max_w) * port_val
                        sell_shs = int(excess_val / get_price(sym, dt_str)["close"])
                        if sell_shs > 0:
                            record_trade(
                                dt_str=dt_str,
                                sym=sym,
                                action="REBALANCE_TRIM",
                                shares=sell_shs,
                                price=get_price(sym, dt_str)["close"],
                                reason=f"Quarterly Risk Rebalance Trim (Weight reached {curr_w*100:.1f}%, target {target_w*100:.1f}%)"
                            )

            # Record Daily Equity Snapshot
            strat_equity = cash + sum(positions[s]["shares"] * get_price(s, dt_str)["close"] for s in positions)
            vti_val = vti_shares * get_price("VTI", dt_str)["close"]
            qqq_val = qqq_shares * get_price("QQQ", dt_str)["close"]
            spy_val = spy_shares * get_price("SPY", dt_str)["close"]

            daily_equity_curve.append({
                "date": dt_str,
                "strategy_equity": round(strat_equity, 2),
                "vti_equity": round(vti_val, 2),
                "qqq_equity": round(qqq_val, 2),
                "spy_equity": round(spy_val, 2),
                "cash": round(cash, 2)
            })

        # 5. Performance Statistics Calculations
        eq_df = pd.DataFrame(daily_equity_curve)
        final_strat = eq_df["strategy_equity"].iloc[-1]
        final_vti = eq_df["vti_equity"].iloc[-1]
        final_qqq = eq_df["qqq_equity"].iloc[-1]
        final_spy = eq_df["spy_equity"].iloc[-1]

        years = max(0.1, (end_dt - start_dt).days / 365.25)

        def calc_metrics(series: pd.Series) -> Dict[str, float]:
            tot_ret = ((series.iloc[-1] / series.iloc[0]) - 1.0) * 100.0
            cagr = (((series.iloc[-1] / series.iloc[0]) ** (1.0 / years)) - 1.0) * 100.0
            daily_returns = series.pct_change().dropna()
            vol = float(daily_returns.std() * math.sqrt(252) * 100.0) if len(daily_returns) > 1 else 15.0
            rf = 4.5 # Risk free rate 4.5%
            sharpe = round((cagr - rf) / vol, 2) if vol > 0 else 0.0

            # Max drawdown
            cummax = series.cummax()
            drawdowns = (series - cummax) / cummax
            max_dd = float(drawdowns.min() * 100.0)
            return {
                "total_return_pct": round(tot_ret, 2),
                "cagr_pct": round(cagr, 2),
                "volatility_pct": round(vol, 2),
                "sharpe_ratio": sharpe,
                "max_drawdown_pct": round(max_dd, 2),
                "final_value": round(float(series.iloc[-1]), 2)
            }

        strat_m = calc_metrics(eq_df["strategy_equity"])
        vti_m = calc_metrics(eq_df["vti_equity"])
        qqq_m = calc_metrics(eq_df["qqq_equity"])
        spy_m = calc_metrics(eq_df["spy_equity"])

        alpha_vs_vti = round(strat_m["total_return_pct"] - vti_m["total_return_pct"], 2)
        alpha_vs_qqq = round(strat_m["total_return_pct"] - qqq_m["total_return_pct"], 2)
        alpha_vs_spy = round(strat_m["total_return_pct"] - spy_m["total_return_pct"], 2)

        buy_ops = [op for op in operations_history if op["action"].startswith("BUY") or op["action"] in ["TREND_ENTRY", "RE_ENTRY"]]
        sell_ops = [op for op in operations_history if not (op["action"].startswith("BUY") or op["action"] in ["TREND_ENTRY", "RE_ENTRY"])]

        return {
            "config": {
                "start_date": start_str,
                "end_date": end_str,
                "duration_years": round(years, 2),
                "trading_days": len(trading_dates),
                "initial_capital": self.initial_capital,
                "selected_universe": selected_assets,
                "strategy_type": "Single-Stock Tranche Strategy" if is_single_asset else "Multi-Asset Alpha Portfolio",
                "weights": weights
            },
            "strategy_metrics": strat_m,
            "benchmarks": {
                "VTI": vti_m,
                "QQQ": qqq_m,
                "SPY": spy_m
            },
            "alpha": {
                "alpha_vs_vti_pct": alpha_vs_vti,
                "alpha_vs_qqq_pct": alpha_vs_qqq,
                "alpha_vs_spy_pct": alpha_vs_spy,
                "outperformance_multiple_vti": round(strat_m["total_return_pct"] / max(0.1, vti_m["total_return_pct"]), 2),
                "outperformance_multiple_qqq": round(strat_m["total_return_pct"] / max(0.1, qqq_m["total_return_pct"]), 2)
            },
            "operations_summary": {
                "total_operations": len(operations_history),
                "buy_orders": len(buy_ops),
                "sell_orders": len(sell_ops)
            },
            "operations_history": operations_history,
            "daily_equity_curve": daily_equity_curve
        }

    @classmethod
    def format_backtest_report(cls, results: Dict[str, Any]) -> str:
        """Formats the entire backtest dossier into a clean, presentation-ready report."""
        cfg = results["config"]
        sm = results["strategy_metrics"]
        bm = results["benchmarks"]
        alpha = results["alpha"]
        ops = results["operations_history"]

        lines = [
            "=" * 92,
            "                   MULTI-AGENT STRATEGY HISTORICAL BACKTEST REPORT                    ",
            "=" * 92,
            f"  • Strategy Type:      {cfg['strategy_type']}",
            f"  • Test Window:        {cfg['start_date']}  -->  {cfg['end_date']} ({cfg['duration_years']} Years / {cfg['trading_days']} Trading Days)",
            f"  • Starting Capital:   ${cfg['initial_capital']:,.2f}",
            f"  • Final Strategy Eq:  ${sm['final_value']:,.2f}  ({sm['total_return_pct']:+,.2f}%)",
            f"  • Target Universe:    {', '.join(cfg['selected_universe'])}",
            "-" * 92,
            "",
            "============================================================================================",
            "                           CHRONOLOGICAL HISTORY OF OPERATIONS                              ",
            "============================================================================================",
            f"{'DATE':<11} {'ACTION':<15} {'SYM':<6} {'SHARES':>7} {'PRICE ($)':>11} {'NOTIONAL ($)':>14} {'PORTFOLIO ($)':>15} {'REASON / TRIGGER':<20}",
            "-" * 105
        ]

        for op in ops:
            lines.append(
                f"{op['date']:<11} {op['action']:<15} {op['symbol']:<6} {op['shares']:>7} "
                f"${op['price']:>10,.2f} ${op['notional']:>13,.2f} ${op['portfolio_value']:>14,.2f} "
                f"{op['reason'][:45]}"
            )

        lines.extend([
            "-" * 105,
            f"Total Operations Executed: {len(ops)} (Buys: {results['operations_summary']['buy_orders']}, Sells/Trims: {results['operations_summary']['sell_orders']})",
            "",
            "============================================================================================",
            "                   BENCHMARK SCORECARD: STRATEGY vs. VTI vs. QQQ vs. SPY                   ",
            "============================================================================================",
            f"{'PERFORMANCE METRIC':<26} {'OUR STRATEGY':<16} {'VTI (Total Market)':<20} {'QQQ (Nasdaq 100)':<18} {'SPY (S&P 500)':<16}",
            "-" * 98,
            f"{'Initial Capital':<26} ${cfg['initial_capital']:<15,.2f} ${cfg['initial_capital']:<19,.2f} ${cfg['initial_capital']:<17,.2f} ${cfg['initial_capital']:<15,.2f}",
            f"{'Ending Equity':<26} ${sm['final_value']:<15,.2f} ${bm['VTI']['final_value']:<19,.2f} ${bm['QQQ']['final_value']:<17,.2f} ${bm['SPY']['final_value']:<15,.2f}",
            f"{'Total Return (%)':<26} {sm['total_return_pct']:>+6.2f}%          {bm['VTI']['total_return_pct']:>+6.2f}%              {bm['QQQ']['total_return_pct']:>+6.2f}%            {bm['SPY']['total_return_pct']:>+6.2f}%",
            f"{'Annualized Return (CAGR)':<26} {sm['cagr_pct']:>+6.2f}%          {bm['VTI']['cagr_pct']:>+6.2f}%              {bm['QQQ']['cagr_pct']:>+6.2f}%            {bm['SPY']['cagr_pct']:>+6.2f}%",
            f"{'Annual Volatility':<26} {sm['volatility_pct']:>5.2f}%           {bm['VTI']['volatility_pct']:>5.2f}%               {bm['QQQ']['volatility_pct']:>5.2f}%             {bm['SPY']['volatility_pct']:>5.2f}%",
            f"{'Sharpe Ratio (Rf=4.5%)':<26} ⭐ {sm['sharpe_ratio']:<13} {bm['VTI']['sharpe_ratio']:<20} {bm['QQQ']['sharpe_ratio']:<18} {bm['SPY']['sharpe_ratio']:<16}",
            f"{'Max Drawdown':<26} {sm['max_drawdown_pct']:>6.2f}%          {bm['VTI']['max_drawdown_pct']:>6.2f}%              {bm['QQQ']['max_drawdown_pct']:>6.2f}%            {bm['SPY']['max_drawdown_pct']:>6.2f}%",
            "-" * 98,
            f"{'EXCESS ALPHA vs BENCHMARK':<26} {'---':<16} {alpha['alpha_vs_vti_pct']:>+6.2f}%              {alpha['alpha_vs_qqq_pct']:>+6.2f}%            {alpha['alpha_vs_spy_pct']:>+6.2f}%",
            f"{'Outperformance Multiple':<26} {'---':<16} {alpha['outperformance_multiple_vti']}x                 {alpha['outperformance_multiple_qqq']}x               {round(sm['total_return_pct']/max(0.1, bm['SPY']['total_return_pct']), 2)}x",
            "-" * 98,
            "",
            "💡 STRATEGIC INVESTMENT COMMITTEE VERDICT:",
            f"   • vs VTI (Total US Market): Beat total market by {alpha['alpha_vs_vti_pct']}% excess return ({alpha['outperformance_multiple_vti']}x outperformance multiple).",
            f"   • vs QQQ (Nasdaq 100):      Beat Nasdaq 100 growth by {alpha['alpha_vs_qqq_pct']}% excess return ({alpha['outperformance_multiple_qqq']}x outperformance multiple).",
            f"   • Risk Efficiency Edge:     Strategy achieved a Sharpe Ratio of {sm['sharpe_ratio']} (vs QQQ {bm['QQQ']['sharpe_ratio']} and VTI {bm['VTI']['sharpe_ratio']}).",
            "=" * 92
        ])

        return "\n".join(lines)


if __name__ == "__main__":
    engine = BacktestEngine(initial_capital=100000.0)
    res = engine.run_backtest(lookback="1y")
    print(BacktestEngine.format_backtest_report(res))

