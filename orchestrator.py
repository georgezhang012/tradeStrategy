"""
Institutional Trading System Orchestrator
=========================================
Orchestrates the Investment Committee debate:
Macro -> Valuation (Reverse DCF) -> Bull Pitch -> Bear Red Team -> CRO Adjudication.
"""

from typing import Dict, Any, Optional
try:
    from .agents import (
        MacroFactorAgent,
        ValuationExpectationsAgent,
        BullResearchAgent,
        BearResearchAgent,
        ChiefRiskOfficerAgent
    )
except (ImportError, ValueError):
    from agents import (
        MacroFactorAgent,
        ValuationExpectationsAgent,
        BullResearchAgent,
        BearResearchAgent,
        ChiefRiskOfficerAgent
    )


class InstitutionalTradingSystem:
    """Coordinates the institutional multi-agent investment committee."""

    def __init__(self):
        self.macro_agent = MacroFactorAgent()
        self.valuation_agent = ValuationExpectationsAgent()
        self.bull_agent = BullResearchAgent()
        self.bear_agent = BearResearchAgent()
        self.cro_agent = ChiefRiskOfficerAgent()

    def evaluate_investment_idea(
        self,
        symbol: str,
        portfolio_equity: float = 100000.0
    ) -> Dict[str, Any]:
        """
        Executes the full institutional review for a given ticker:
        1. Macro & Factor Allocation Check
        2. Expectations & Reverse-DCF Valuation Audit
        3. Bullish Catalyst Pitch
        4. Red Team Forensic Risk Counter-Attack
        5. Chief Risk Officer Sizing, Pairs-Hedge, and Binding Verdict
        """
        sym = symbol.upper()
        print(f"\n=======================================================")
        print(f"   INSTITUTIONAL INVESTMENT COMMITTEE AUDIT: {sym}     ")
        print(f"=======================================================\n")

        # Step 1: Macro & Factor Regime
        print(f"[*] Step 1: Invoking {self.macro_agent.NAME} ({self.macro_agent.TITLE})...")
        macro_report = self.macro_agent.analyze()

        # Step 2: Expectations & Reverse-DCF Valuation
        print(f"[*] Step 2: Invoking {self.valuation_agent.NAME} ({self.valuation_agent.TITLE})...")
        val_report = self.valuation_agent.analyze(sym)

        # Step 3: Bull Pitch
        print(f"[*] Step 3: Invoking {self.bull_agent.NAME} ({self.bull_agent.TITLE})...")
        bull_pitch = self.bull_agent.generate_pitch(sym)

        # Step 4: Red Team Counter-Attack
        print(f"[*] Step 4: Invoking {self.bear_agent.NAME} ({self.bear_agent.TITLE})...")
        bear_audit = self.bear_agent.generate_counter_thesis(sym)

        # Step 5: CRO Adjudication & Quant Sizing
        print(f"[*] Step 5: Invoking {self.cro_agent.NAME} ({self.cro_agent.TITLE})...")
        cro_decision = self.cro_agent.adjudicate_and_size(
            symbol=sym,
            macro_report=macro_report,
            val_report=val_report,
            bull_pitch=bull_pitch,
            bear_audit=bear_audit,
            portfolio_equity=portfolio_equity
        )

        return {
            "symbol": sym,
            "macro_report": macro_report,
            "valuation_report": val_report,
            "bull_pitch": bull_pitch,
            "bear_audit": bear_audit,
            "cro_decision": cro_decision,
            "committee_memo": cro_decision["committee_memo"]
        }

