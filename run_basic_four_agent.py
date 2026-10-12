"""
Multi-Agent Financial Intelligence System Runner
================================================
Runs the 4-agent workflow (Macro Analyst, Alpha Screener, News Analyst, and Investment Strategist).
Supports both standalone data-driven mode and AutoGen LLM GroupChat mode.

Usage:
  python run_four_agent_group.py                      # Runs 10-year horizon analysis
  python run_four_agent_group.py --years 20           # Runs 20-year horizon analysis
  python run_four_agent_group.py --symbol MSFT        # Focuses news & strategy on MSFT
  python run_four_agent_group.py --autogen            # Runs via AutoGen LLM GroupChat (requires OpenAI key)
"""

import os
import sys
import argparse

# Ensure current and parent directories are in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
for p in [current_dir, parent_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from tradingStrategy.basic_multi_agent_system import MultiAgentStockSystem, build_autogen_group_config
except ImportError:
    from basic_multi_agent_system import MultiAgentStockSystem, build_autogen_group_config


def run_standalone(years: int, symbol: str = None):
    """Executes the pipeline directly using deterministic financial tools."""
    system = MultiAgentStockSystem()
    report = system.run_full_pipeline(horizon_years=years, target_symbol=symbol)
    print("\n" + report)


def run_autogen_groupchat(years: int, symbol: str = None):
    """Runs the 4 agents inside an AutoGen GroupChat environment."""
    try:
        import autogen
    except ImportError:
        print("\n[!] 'autogen' / 'pyautogen' is not installed in the current environment.")
        print("    Running standalone pipeline instead...\n")
        run_standalone(years, symbol)
        return

    # Check for OAI_CONFIG_LIST or OPENAI_API_KEY
    config_list = []
    if os.path.exists("OAI_CONFIG_LIST"):
        try:
            config_list = autogen.config_list_from_json("OAI_CONFIG_LIST")
        except Exception:
            pass

    if not config_list and "OPENAI_API_KEY" in os.environ:
        config_list = [{"model": "gpt-4o-mini", "api_key": os.environ["OPENAI_API_KEY"]}]

    if not config_list or config_list[0].get("api_key") == "<your OpenAI API key here>":
        print("\n[!] Valid OpenAI API Key not found in OAI_CONFIG_LIST or environment variables.")
        print("    Defaulting to standalone multi-agent execution pipeline...\n")
        run_standalone(years, symbol)
        return

    llm_config = {
        "config_list": config_list,
        "temperature": 0.2,
        "cache_seed": 42
    }

    config_data = build_autogen_group_config(llm_config)
    agents = []

    for agent_spec in config_data["agents"]:
        agent = autogen.AssistantAgent(
            name=agent_spec["name"],
            system_message=agent_spec["profile"],
            llm_config=llm_config
        )
        agents.append(agent)

    user_proxy = autogen.UserProxyAgent(
        name="User_Proxy",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=10,
        is_termination_msg=lambda x: "TERMINATE" in x.get("content", ""),
        code_execution_config=False
    )

    groupchat = autogen.GroupChat(
        agents=[user_proxy] + agents,
        messages=[],
        max_round=12,
        speaker_selection_method="round_robin"
    )

    manager = autogen.GroupChatManager(
        groupchat=groupchat,
        llm_config=llm_config
    )

    prompt = (
        f"Team, please conduct a complete investment analysis:\n"
        f"1. Macro_Economic_Analyst: Assess current inflation, GDP growth, interest rates, and macro regime.\n"
        f"2. Alpha_Stock_Screener: Identify top S&P 500 / NASDAQ companies beating S&P 500 over {years} years.\n"
        f"3. Company_News_Analyst: Review recent news and sentiment for the top candidate company.\n"
        f"4. Investment_Strategist: Deliver final stock operation recommendation (action, sizing, stop-loss). "
        f"Conclude with TERMINATE."
    )

    user_proxy.initiate_chat(manager, message=prompt)


def main():
    parser = argparse.ArgumentParser(description="Multi-Agent Stock Investment System")
    parser.add_argument("--years", type=int, default=10, choices=[10, 20], help="Historical comparison horizon (10 or 20 years)")
    parser.add_argument("--symbol", type=str, default=None, help="Target stock ticker (e.g., NVDA, MSFT, AAPL)")
    parser.add_argument("--autogen", action="store_true", help="Run via AutoGen GroupChat with LLM")

    args = parser.parse_args()

    if args.autogen:
        run_autogen_groupchat(years=args.years, symbol=args.symbol)
    else:
        run_standalone(years=args.years, symbol=args.symbol)


if __name__ == "__main__":
    main()

