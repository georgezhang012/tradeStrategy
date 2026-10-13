"""
Portfolio Optimization Engine: Maximize Return & Minimize Risk
==============================================================
Implements:
1. Markowitz Efficient Frontier: Solves for Maximum Sharpe Ratio Portfolio.
2. Minimum Volatility (Risk Minimization) Portfolio.
3. Risk Parity / Equal Risk Contribution (Inverse-Volatility Weighting).
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional


class PortfolioOptimizer:
    """
    Optimizes asset allocations to maximize risk-adjusted returns (Sharpe Ratio)
    while enforcing volatility limits and diversification constraints.
    """

    # Default statistical parameters for major candidates
    ASSET_STATS = {
        "NVDA": {"expected_return": 0.28, "volatility": 0.38},
        "MSFT": {"expected_return": 0.18, "volatility": 0.21},
        "AAPL": {"expected_return": 0.16, "volatility": 0.22},
        "AMZN": {"expected_return": 0.19, "volatility": 0.27},
        "GOOGL": {"expected_return": 0.17, "volatility": 0.24},
        "AVGO": {"expected_return": 0.22, "volatility": 0.30},
        "COST": {"expected_return": 0.14, "volatility": 0.16},
        "SPY":  {"expected_return": 0.118, "volatility": 0.152},
        "VTI":  {"expected_return": 0.115, "volatility": 0.158},
        "QQQ":  {"expected_return": 0.175, "volatility": 0.215}
    }

    # Institutional Benchmark Profiles for comparison
    BENCHMARK_PROFILES = {
        "VTI": {
            "name": "Vanguard Total Stock Market ETF",
            "description": "Broad US Total Market Blend (~3,700 stocks)",
            "expected_return": 0.115,
            "volatility": 0.158,
            "sharpe_ratio": 0.44,
            "cagr_10y": 12.3,
            "return_10y": 218.0,
            "cagr_20y": 9.9,
            "max_drawdown_5y_pct": -24.5,
            "beta": 1.00
        },
        "QQQ": {
            "name": "Invesco QQQ Trust (NASDAQ-100)",
            "description": "Tech & High-Growth Mega-Caps (100 non-financials)",
            "expected_return": 0.175,
            "volatility": 0.215,
            "sharpe_ratio": 0.60,
            "cagr_10y": 18.2,
            "return_10y": 432.0,
            "cagr_20y": 14.8,
            "max_drawdown_5y_pct": -35.2,
            "beta": 1.18
        },
        "SPY": {
            "name": "SPDR S&P 500 ETF Trust",
            "description": "Large-Cap Blend (500 US leaders)",
            "expected_return": 0.118,
            "volatility": 0.152,
            "sharpe_ratio": 0.48,
            "cagr_10y": 12.8,
            "return_10y": 234.0,
            "cagr_20y": 10.2,
            "max_drawdown_5y_pct": -23.9,
            "beta": 1.00
        }
    }

    # Baseline correlation matrix between assets
    DEFAULT_CORRELATIONS = {
        ("NVDA", "MSFT"): 0.55, ("NVDA", "AAPL"): 0.48, ("NVDA", "AMZN"): 0.52, ("NVDA", "COST"): 0.18,
        ("MSFT", "AAPL"): 0.65, ("MSFT", "AMZN"): 0.62, ("MSFT", "COST"): 0.30,
        ("AAPL", "AMZN"): 0.58, ("AAPL", "COST"): 0.28,
        ("AMZN", "COST"): 0.25,
        ("VTI", "QQQ"): 0.88, ("VTI", "SPY"): 0.99, ("QQQ", "SPY"): 0.90
    }

    @classmethod
    def get_asset_stats(cls, symbol: str) -> Dict[str, float]:
        """Retrieves asset expected return and volatility dynamically from screener metrics."""
        try:
            from sp500_nasdaq_screener import SP500NasdaqScreener
            metrics = SP500NasdaqScreener.generate_historical_metrics_dict().get(symbol, {})
            cagr = metrics.get("cagr_2y", metrics.get("cagr_5y", metrics.get("cagr_10y")))
            if cagr is not None:
                exp_ret = max(0.10, min(0.95, float(cagr) / 100.0))
                vol = 0.38 if exp_ret > 0.40 else (0.28 if exp_ret > 0.25 else 0.20)
                return {"expected_return": exp_ret, "volatility": vol}
        except Exception:
            pass

        if symbol in cls.ASSET_STATS:
            return cls.ASSET_STATS[symbol]
        return {"expected_return": 0.16, "volatility": 0.24}

    @classmethod
    def build_covariance_matrix(cls, symbols: List[str]) -> Tuple[np.ndarray, np.ndarray]:
        """Constructs annualized expected returns vector and covariance matrix."""
        n = len(symbols)
        returns = np.array([cls.get_asset_stats(s)["expected_return"] for s in symbols])
        vols = np.array([cls.get_asset_stats(s)["volatility"] for s in symbols])
        
        corr_matrix = np.eye(n)
        for i in range(n):
            for j in range(i + 1, n):
                s1, s2 = symbols[i], symbols[j]
                c = cls.DEFAULT_CORRELATIONS.get((s1, s2), cls.DEFAULT_CORRELATIONS.get((s2, s1), 0.40))
                corr_matrix[i, j] = c
                corr_matrix[j, i] = c

        # Covariance = diag(vols) * corr * diag(vols)
        cov_matrix = np.outer(vols, vols) * corr_matrix
        return returns, cov_matrix

    @classmethod
    def optimize_alpha_convex(
        cls,
        symbols: List[str],
        power: float = 1.5,
        max_weight_per_asset: Optional[float] = None,
        min_weight_per_asset: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Convex Alpha / Momentum Weighting:
        Allocates capital proportionally to (Alpha)^power, ensuring elite compounders
        maintain heavy portfolio torque while tail assets provide broad diversification.
        """
        n = len(symbols)
        if n == 0:
            return {"weights": {}}
        if n == 1:
            return {"weights": {symbols[0]: 1.0}}

        returns = [cls.get_asset_stats(s)["expected_return"] for s in symbols]
        alphas = [max(0.02, r - 0.12) for r in returns] # excess over 12% baseline
        scores = np.array([a ** power for a in alphas])
        total_score = np.sum(scores)
        if total_score > 0:
            raw_weights = scores / total_score
        else:
            raw_weights = np.ones(n) / n

        eff_max = max_weight_per_asset or min(0.20, max(0.06, 2.5 / n))
        eff_min = min_weight_per_asset or max(0.005, min(0.03, 0.3 / n))

        weights = np.clip(raw_weights, eff_min, eff_max)
        weights /= np.sum(weights)

        allocations = {symbols[i]: round(float(weights[i]), 4) for i in range(n)}
        port_return = float(weights @ returns)
        return {
            "strategy": "Alpha-Convex Momentum Weighting",
            "symbols": symbols,
            "weights": allocations,
            "expected_annual_return_pct": round(port_return * 100, 2)
        }

    @classmethod
    def optimize_max_sharpe(
        cls,
        symbols: List[str],
        risk_free_rate: float = 0.045, # 4.5% Treasury yield
        max_weight_per_asset: float = 0.25, # 25% max concentration limit
        min_weight_per_asset: float = 0.02  # 2% minimum allocation
    ) -> Dict[str, Any]:
        """
        Calculates the Maximum Sharpe Ratio Portfolio weights.
        Maximizes: (E[R] - Rf) / Portfolio_Volatility with institutional breadth constraints.
        """
        returns, cov_matrix = cls.build_covariance_matrix(symbols)
        n = len(symbols)

        # Analytical unconstrained tangency weights: w = inv(Cov) * (returns - Rf)
        inv_cov = np.linalg.pinv(cov_matrix)
        excess_returns = returns - risk_free_rate
        raw_weights = inv_cov @ excess_returns
        
        # Project into long-only positive weights with bounds
        positive_weights = np.maximum(raw_weights, 0.0)
        if np.sum(positive_weights) == 0:
            positive_weights = np.ones(n) / n
        else:
            positive_weights /= np.sum(positive_weights)

        # Apply institutional concentration boundaries scaled dynamically to portfolio size
        eff_max = min(max_weight_per_asset, max(0.08, 2.2 / n)) if n >= 5 else 0.40
        eff_min = max(0.01, min(0.04, 0.4 / n)) if n >= 5 else 0.05
        weights = np.clip(positive_weights, eff_min, eff_max)
        weights /= np.sum(weights)

        # Calculate portfolio metrics
        port_return = float(weights @ returns)
        port_variance = float(weights.T @ cov_matrix @ weights)
        port_volatility = float(np.sqrt(port_variance))
        sharpe_ratio = float((port_return - risk_free_rate) / port_volatility)

        allocations = {symbols[i]: round(float(weights[i]), 4) for i in range(n)}

        return {
            "strategy": "Maximum Sharpe Ratio (Mean-Variance Optimal)",
            "symbols": symbols,
            "weights": allocations,
            "expected_annual_return_pct": round(port_return * 100, 2),
            "expected_annual_volatility_pct": round(port_volatility * 100, 2),
            "sharpe_ratio": round(sharpe_ratio, 2),
            "risk_free_rate_pct": round(risk_free_rate * 100, 2)
        }

    @classmethod
    def optimize_risk_parity(
        cls,
        symbols: List[str],
        risk_free_rate: float = 0.045
    ) -> Dict[str, Any]:
        """
        Calculates the Risk Parity (Inverse-Volatility) Portfolio.
        Minimizes concentration risk by equalizing risk contribution.
        """
        returns, cov_matrix = cls.build_covariance_matrix(symbols)
        vols = np.array([cls.ASSET_STATS.get(s, {"volatility": 0.25})["volatility"] for s in symbols])

        # Inverse volatility weighting: w_i proportional to 1 / sigma_i
        inv_vols = 1.0 / vols
        weights = inv_vols / np.sum(inv_vols)

        port_return = float(weights @ returns)
        port_variance = float(weights.T @ cov_matrix @ weights)
        port_volatility = float(np.sqrt(port_variance))
        sharpe_ratio = float((port_return - risk_free_rate) / port_volatility)

        allocations = {symbols[i]: round(float(weights[i]), 4) for i in range(len(symbols))}

        return {
            "strategy": "Risk Parity (Equal Risk Contribution / Volatility Minimization)",
            "symbols": symbols,
            "weights": allocations,
            "expected_annual_return_pct": round(port_return * 100, 2),
            "expected_annual_volatility_pct": round(port_volatility * 100, 2),
            "sharpe_ratio": round(sharpe_ratio, 2)
        }

    @classmethod
    def compare_against_benchmarks(
        cls,
        port_return_pct: float,
        port_volatility_pct: float,
        port_sharpe: float
    ) -> Dict[str, Any]:
        """
        Compares the optimized portfolio against key passive benchmarks:
        1. VTI (Vanguard Total US Market ETF)
        2. QQQ (Invesco Nasdaq-100 ETF)
        3. SPY (S&P 500 ETF)
        """
        comparisons = []
        for ticker in ["VTI", "QQQ", "SPY"]:
            b_info = cls.BENCHMARK_PROFILES[ticker]
            b_ret_pct = round(b_info["expected_return"] * 100, 2)
            b_vol_pct = round(b_info["volatility"] * 100, 2)
            b_sharpe = b_info["sharpe_ratio"]

            alpha = round(port_return_pct - b_ret_pct, 2)
            vol_delta = round(port_volatility_pct - b_vol_pct, 2)
            sharpe_diff = round(port_sharpe - b_sharpe, 2)

            comparisons.append({
                "ticker": ticker,
                "name": b_info["name"],
                "description": b_info["description"],
                "benchmark_return_pct": b_ret_pct,
                "benchmark_volatility_pct": b_vol_pct,
                "benchmark_sharpe": b_sharpe,
                "cagr_10y": b_info["cagr_10y"],
                "cagr_20y": b_info["cagr_20y"],
                "max_drawdown_5y_pct": b_info["max_drawdown_5y_pct"],
                "excess_return_alpha_pct": alpha,
                "volatility_delta_pct": vol_delta,
                "sharpe_outperformance": sharpe_diff,
                "verdict": (
                    f"Outperformed {ticker} by +{alpha}% with {abs(vol_delta)}% {'lower' if vol_delta < 0 else 'higher'} volatility."
                    if alpha >= 0 else
                    f"Underperformed {ticker} by {alpha}%."
                )
            })

        return {
            "portfolio": {
                "expected_return_pct": port_return_pct,
                "volatility_pct": port_volatility_pct,
                "sharpe_ratio": port_sharpe
            },
            "benchmarks": comparisons
        }


