#!/usr/bin/env bash
# ==============================================================================
# Automated Cron Scheduler Setup for Investment Strategy Platform
# ==============================================================================
# Schedule:
# 1. DAILY (Mon-Fri at 4:15 PM ET): Runs Risk & Stop-Loss Monitor
# 2. MONTHLY (1st of month at 9:00 AM): Runs Core Portfolio Rebalance
# ==============================================================================

WORKSPACE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_EXEC="$(which python3)"

DAILY_CMD="cd $WORKSPACE_DIR && $PYTHON_EXEC tradingStrategy/monitor_and_alert.py --save-log >> tradingStrategy/cron_daily.log 2>&1"
MONTHLY_CMD="cd $WORKSPACE_DIR && $PYTHON_EXEC tradingStrategy/investment_platform.py >> tradingStrategy/cron_monthly.log 2>&1"

# Crontab entries:
# 15 16 * * 1-5 = 4:15 PM Monday through Friday
# 0 9 1 * * = 9:00 AM on 1st day of every month
CRON_DAILY="15 16 * * 1-5 $DAILY_CMD"
CRON_MONTHLY="0 9 1 * * $MONTHLY_CMD"

echo "=========================================================="
echo " Setting up Automated Cron Schedule for macOS / Linux    "
echo "=========================================================="
echo ""
echo "Daily Risk Monitor:     $CRON_DAILY"
echo "Monthly Rebalancer:     $CRON_MONTHLY"
echo ""

# Write to current user crontab safely
(crontab -l 2>/dev/null | grep -v "tradingStrategy"; echo "$CRON_DAILY"; echo "$CRON_MONTHLY") | crontab -

echo "[✓] Automated schedule successfully installed in crontab!"
echo ""
echo "To verify active crontab, run:"
echo "  crontab -l"
echo ""
echo "To check alert logs at any time:"
echo "  cat tradingStrategy/alerts.log"
echo "=========================================================="

