"""
Institutional Multi-Agent Trading & Investment Strategy Framework
=================================================================
Components:
- valuation_engine: Reverse-DCF, Implied Growth, and Multiples Relative Analysis
- risk_engine: Volatility-adjusted ATR Sizing, VaR, and Long/Short Pairs Hedging
- agents: Adversarial Bull vs. Bear Researchers, Valuation Analyst, Macro & CRO
- orchestrator: Investment Committee Debate & Decision Orchestrator
"""

from .valuation_engine import ValuationEngine
from .risk_engine import RiskEngine
from .agents import (
    MacroFactorAgent,
    ValuationExpectationsAgent,
    BullResearchAgent,
    BearResearchAgent,
    ChiefRiskOfficerAgent
)
from .orchestrator import InstitutionalTradingSystem
from .portfolio_optimizer import PortfolioOptimizer
from .paper_trading_simulator import PaperTradingSimulator
from .alpaca_paper_trader import AlpacaPaperTrader

__all__ = [
    "ValuationEngine",
    "RiskEngine",
    "MacroFactorAgent",
    "ValuationExpectationsAgent",
    "BullResearchAgent",
    "BearResearchAgent",
    "ChiefRiskOfficerAgent",
    "InstitutionalTradingSystem",
    "PortfolioOptimizer",
    "PaperTradingSimulator",
    "AlpacaPaperTrader"
]

