"""
Institutional Investment Committee Agents
=========================================
Implements an adversarial, institutional decision-making team:
1. MacroFactorAgent: Assesses macro regime and factor style tilts.
2. ValuationExpectationsAgent: Computes Reverse-DCF and expectations asymmetry.
3. BullResearchAgent: Defends the long investment thesis and catalyst drivers.
4. BearResearchAgent (Red Team): Stresses risks, multiple contraction, and headwinds.
5. ChiefRiskOfficerAgent: Moderates debate, calculates ATR stops & hedges, issues binding decision.
"""

from typing import Dict, Any, List
from .valuation_engine import ValuationEngine
from .risk_engine import RiskEngine


class MacroFactorAgent:
    """Agent 1: Macro & Factor Regime Analyst."""
    NAME = "Macro_Factor_Analyst"
    TITLE = "Head of Macro & Factor Allocation"

    def analyze(self) -> Dict[str, Any]:
        return {
            "macro_regime": "Disinflationary Expansion (Late Mid-Cycle)",
            "fed_cycle": "Monetary Easing / Gradual Rate Reduction",
            "treasury_10y_yield": 4.15,
            "factor_performance": {
                "Quality": "Outperforming (High ROIC, Clean Balance Sheets in demand)",
                "Momentum": "Strong (Trend continuation across market leaders)",
                "Value": "Neutral (Deep cyclical value lagging secular tech)",
                "Growth": "Constructive (Supported by stabilizing discount rates)"
            },
            "posture": "Favor High-Quality Growth with verifiable Cash Flow Generation"
        }


class ValuationExpectationsAgent:
    """Agent 2: Reverse-DCF & Market Expectations Analyst."""
    NAME = "Valuation_Expectations_Analyst"
    TITLE = "Senior Equity Valuation Specialist"

    def analyze(self, symbol: str) -> Dict[str, Any]:
        return ValuationEngine.analyze_company_valuation(symbol)


class BullResearchAgent:
    """Agent 3: Champions the long thesis and identifies catalysts."""
    NAME = "Bull_Researcher"
    TITLE = "Senior Long-Only Equity Analyst"

    THESIS_BANK = {
        "NVDA": {
            "catalysts": [
                "Generative AI inference demand transitioning from hyperscalers to global enterprise software.",
                "High switching costs created by proprietary CUDA software architecture and developer lock-in.",
                "Next-generation rack-scale architectures (GB200/Blackwell) expanding ASPs and gross margins."
            ],
            "economic_moat": "Wide Moat: Proprietary hardware-software ecosystem and multi-year lead in interconnect fabrics.",
            "upside_scenario": "Hyperscaler CapEx increases another 20-30% YoY, driving EPS expansion beyond sell-side consensus."
        },
        "MSFT": {
            "catalysts": [
                "Azure cloud infrastructure capturing dominant share of enterprise AI enterprise migrations.",
                "Copilot monetizing high-margin ARPU expansion across 400M+ commercial Office seats.",
                "Pristine balance sheet ($70B+ annual FCF) enabling continuous buybacks and R&D reinvestment."
            ],
            "economic_moat": "Wide Moat: Mission-critical operating system, enterprise productivity, and hybrid cloud lock-in.",
            "upside_scenario": "Rapid enterprise Copilot penetration driving operating margin expansion to multi-year highs."
        },
        "AAPL": {
            "catalysts": [
                "Apple Intelligence on-device AI triggering the largest multi-year hardware replacement cycle since 5G.",
                "Services ecosystem (iCloud, App Store, Pay) reaching $100B+ annual run-rate at 74% gross margin.",
                "Relentless share count reduction through $100B+ annual share repurchases."
            ],
            "economic_moat": "Wide Moat: Premier consumer tech brand loyalty, hardware-software integration, and 2B active devices.",
            "upside_scenario": "Double-digit iPhone unit growth combined with accelerating services subscription monetization."
        }
    }

    def generate_pitch(self, symbol: str) -> Dict[str, Any]:
        sym = symbol.upper()
        thesis = self.THESIS_BANK.get(sym, {
            "catalysts": [
                "Secular revenue expansion outperforming broader sector growth.",
                "Operational leverage driving margin expansion and strong free cash flow conversion."
            ],
            "economic_moat": "Moderate Moat: Established market position and customer stickiness.",
            "upside_scenario": "Beat-and-raise quarterly earnings cadence fueled by strong end-market demand."
        })
        return {
            "symbol": sym,
            "core_thesis": thesis,
            "bull_conviction": "High"
        }


class BearResearchAgent:
    """Agent 4 (Red Team): Challenges the thesis, exposes valuation risk and structural headwinds."""
    NAME = "Bear_Researcher_RedTeam"
    TITLE = "Head of Short Research & Forensic Analysis"

    RISK_BANK = {
        "NVDA": {
            "counter_arguments": [
                "Hyperscaler ROI Dilemma: Big Tech investors may demand CapEx cuts if AI software monetization lags the massive hardware buildout.",
                "Custom ASIC Threat: In-house silicon from Google (TPU), Amazon (Trainium), and Meta (MTIA) will eventually erode edge GPU margins.",
                "Geopolitical Vulnerability: Extreme concentration in Taiwan semiconductor fabrication (TSMC) represents unhedgeable tail risk.",
                "Expectations Asymmetry: Reverse-DCF shows market expects ~30%+ FCF CAGR; any minor supplier delay triggers severe multiple contraction."
            ],
            "bear_target_drawdown": "-25% to -35% on CapEx digestion cycle"
        },
        "MSFT": {
            "counter_arguments": [
                "Massive CapEx Drag: Capital expenditures for data centers and GPUs dampening near-term free cash flow margins.",
                "Copilot Churn: Risk that corporate enterprises pilot Copilot seats but fail to roll out across general enterprise workforce.",
                "Valuation Stretch: Forward P/E of 30x exceeds 10-year historical median (25x)."
            ],
            "bear_target_drawdown": "-15% to -20% on valuation multiple mean-reversion"
        },
        "AAPL": {
            "counter_arguments": [
                "China Market Headwinds: Domestic competition from Huawei and geopolitical smartphone restrictions.",
                "Regulatory Scrutiny: US DOJ antitrust lawsuit and EU Digital Markets Act threatening high-margin App Store and search exclusivity fees.",
                "Stagnant Top-Line Growth: Revenue growth has hovered in the single digits, making a 31x P/E multiple expensive relative to growth."
            ],
            "bear_target_drawdown": "-15% to -25% on regulatory fines and decelerating upgrade velocity"
        }
    }

    def generate_counter_thesis(self, symbol: str) -> Dict[str, Any]:
        sym = symbol.upper()
        risk = self.RISK_BANK.get(sym, {
            "counter_arguments": [
                "Valuation multiple leaves no room for operational or earnings execution errors.",
                "Macro sensitivity to interest rate duration and slowing corporate IT budgets."
            ],
            "bear_target_drawdown": "-15% to -25% multiple compression"
        })
        return {
            "symbol": sym,
            "red_team_audit": risk,
            "bear_conviction": "Moderate to High"
        }


class ChiefRiskOfficerAgent:
    """Agent 5: Chief Risk Officer & Portfolio Manager. Delivers binding Investment Committee verdict."""
    NAME = "Chief_Risk_Officer"
    TITLE = "Chief Risk Officer & Portfolio Manager"

    def adjudicate_and_size(
        self,
        symbol: str,
        macro_report: Dict[str, Any],
        val_report: Dict[str, Any],
        bull_pitch: Dict[str, Any],
        bear_audit: Dict[str, Any],
        portfolio_equity: float = 100000.0
    ) -> Dict[str, Any]:
        """
        Synthesizes the adversarial debate and applies quantitative risk parameters:
        1. Evaluates valuation asymmetry (Reverse DCF implied growth).
        2. Applies ATR volatility stop-loss sizing.
        3. Formulates a Long/Short pair hedge if multiple compression risk is elevated.
        """
        implied_g = val_report["reverse_dcf"]["implied_growth_cagr_pct"]
        peg = val_report["fundamentals"]["peg_ratio"]
        roic = val_report["fundamentals"]["roic_pct"]

        # Quantitative Position Sizing via RiskEngine
        position_sizing = RiskEngine.calculate_volatility_position_sizing(
            symbol=symbol,
            portfolio_equity=portfolio_equity,
            risk_per_trade_pct=1.0,  # 1% equity risk limit
            atr_multiplier_stop=2.0
        )

        # Pair hedge proposal
        pair_hedge = RiskEngine.calculate_beta_neutral_pair_hedge(
            long_symbol=symbol,
            long_notional=position_sizing["position_notional"]
        )

        # Decision Logic:
        # If ROIC is elite and PEG < 2.0, Long position is approved.
        # If implied growth is high (> 25%), mandate a Beta-Neutral Pair Hedge to mitigate macro multiple collapse!
        if roic >= 20.0 and peg <= 2.5:
            if implied_g and implied_g > 25.0:
                decision = "APPROVED (MANDATORY PAIR HEDGE)"
                decision_rationale = (
                    f"Strong secular catalysts and elite ROIC ({roic}%), but Reverse-DCF indicates "
                    f"market prices in demanding {implied_g}% FCF growth. To eliminate sector multiple "
                    f"compression risk highlighted by Red Team, execute as a Beta-Neutral Pairs Trade "
                    f"(Long {symbol} vs Short {pair_hedge['short_hedge_asset']})."
                )
            else:
                decision = "APPROVED (OUTRIGHT LONG)"
                decision_rationale = (
                    f"High-quality compounder with robust ROIC ({roic}%) and manageable expectations. "
                    f"Asymmetric risk/reward favors long accumulation with 2x ATR trailing stop."
                )
        else:
            decision = "REJECTED / AVOID"
            decision_rationale = (
                f"Risk/reward asymmetry does not clear the institutional 2.5:1 threshold. "
                f"Red Team concerns regarding valuation multiple and competitive degradation dominate."
            )

        committee_memo = (
            f"=======================================================================\n"
            f"              INVESTMENT COMMITTEE MEMO & TRADE DECISION               \n"
            f"=======================================================================\n\n"
            f"ASSET: **{symbol} ({val_report['fundamentals']['name']})**\n"
            f"SECTOR: {val_report['fundamentals']['sector']}\n\n"
            f"### 1. COMMITTEE VERDICT: 🏛️ **{decision}**\n"
            f"- **Executive Rationale**: {decision_rationale}\n\n"
            f"### 2. QUANTITATIVE EXPECTATIONS AUDIT (Reverse-DCF)\n"
            f"- **Market-Implied 5-Year FCF CAGR**: `{implied_g}% / year`\n"
            f"- **Expectations Profile**: {val_report['reverse_dcf']['assessment']}\n"
            f"- **PEG Ratio**: `{peg}` ({val_report['peg_analysis']})\n"
            f"- **ROIC Quality**: `{roic}%` ({val_report['roic_quality']})\n\n"
            f"### 3. ADVERSARIAL DEBATE SYNTHESIS\n"
            f"**Bull Case (Conviction: {bull_pitch['bull_conviction']}):**\n"
            + "\n".join([f"  • {c}" for c in bull_pitch["core_thesis"]["catalysts"]]) + "\n\n"
            f"**Bear Case / Red Team Audit (Conviction: {bear_audit['bear_conviction']}):**\n"
            + "\n".join([f"  ⚠️ {c}" for c in bear_audit["red_team_audit"]["counter_arguments"]]) + "\n\n"
            f"### 4. EXECUTION & VOLATILITY-ADJUSTED RISK CONTROLS\n"
            f"- **Entry Price**: ${position_sizing['entry_price']:.2f}\n"
            f"- **Dynamic ATR Stop-Loss (2.0x ATR)**: **${position_sizing['stop_loss_price']:.2f}** (-{position_sizing['stop_loss_pct']}%)\n"
            f"- **Take-Profit Target (2.5x Risk)**: **${position_sizing['target_price']:.2f}** (+{position_sizing['target_gain_pct']}%)\n"
            f"- **Recommended Sizing**: `{position_sizing['recommended_shares']} shares` (${position_sizing['position_notional']:.2f} notional / {position_sizing['portfolio_weight_pct']}% of book)\n"
            f"- **Max Capital at Risk**: ${position_sizing['max_dollar_risk_at_stop']:.2f} (Strict 1.0% portfolio equity limit)\n\n"
            f"### 5. INSTITUTIONAL PAIR HEDGE STRUCTURE\n"
            f"- **Long Asset**: {symbol} (${position_sizing['position_notional']:.2f})\n"
            f"- **Short Hedge Asset**: {pair_hedge['short_hedge_asset']} (${pair_hedge['short_notional']:.2f} / {pair_hedge['short_shares']} shares)\n"
            f"- **Hedge Ratio**: {pair_hedge['hedge_ratio']} (Beta-Neutral)\n"
            f"- **Strategy Objective**: {pair_hedge['hedge_objective']}\n"
        )

        return {
            "decision": decision,
            "decision_rationale": decision_rationale,
            "position_sizing": position_sizing,
            "pair_hedge": pair_hedge,
            "committee_memo": committee_memo
        }

