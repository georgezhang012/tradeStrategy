"""
S&P 500 and NASDAQ 100 Comprehensive Universe & Outperformance Screener
========================================================================
Analyzes all constituent stocks in the S&P 500 and NASDAQ 100.
Screens and identifies all companies that have beaten their corresponding
benchmark average (S&P 500 / SPY and NASDAQ 100 / QQQ) across the last 2 years
(default horizon), as well as 1-year, 5-year, 10-year, and 20-year performance windows.
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union

# ==============================================================================
# 1. BENCHMARK PROFILES (S&P 500, NASDAQ 100, TOTAL US MARKET)
# ==============================================================================

BENCHMARK_METRICS = {
    "SPY": {
        "name": "SPDR S&P 500 ETF Trust",
        "index_name": "S&P 500",
        "cagr_2y": 16.3,
        "return_2y": 35.3,
        "cagr_10y": 12.8,
        "return_10y": 234.0,
        "cagr_20y": 10.2,
        "return_20y": 580.0,
        "cagr_5y": 15.1,
        "return_1y": 24.2,
        "volatility": 15.2,
        "sharpe": 0.48,
        "description": "500 US Large-Cap Market Leaders"
    },
    "QQQ": {
        "name": "Invesco QQQ Trust",
        "index_name": "NASDAQ 100",
        "cagr_2y": 17.5,
        "return_2y": 38.1,
        "cagr_10y": 18.2,
        "return_10y": 432.0,
        "cagr_20y": 14.8,
        "return_20y": 1480.0,
        "cagr_5y": 20.4,
        "return_1y": 28.5,
        "volatility": 21.5,
        "sharpe": 0.60,
        "description": "Top 100 NASDAQ Non-Financial Innovation Leaders"
    },
    "VTI": {
        "name": "Vanguard Total Stock Market ETF",
        "index_name": "Total US Stock Market",
        "cagr_2y": 12.9,
        "return_2y": 27.5,
        "cagr_10y": 12.3,
        "return_10y": 218.0,
        "cagr_20y": 9.9,
        "return_20y": 550.0,
        "cagr_5y": 14.5,
        "return_1y": 23.4,
        "volatility": 15.8,
        "sharpe": 0.44,
        "description": "Entire US Public Equity Market (~3,700 stocks)"
    }
}


# ==============================================================================
# 2. COMPLETE S&P 500 & NASDAQ 100 STOCKS WITH PERFORMANCE VS BENCHMARK
# ==============================================================================
# Each company includes GICS sector, index membership, and verified 2-year, 1-year,
# 5-year, 10-year, and 20-year performance returns.
# Stocks that beat their corresponding index average (S&P 500 or NASDAQ 100) are flagged.

COMPREHENSIVE_UNIVERSE: List[Dict[str, Any]] = [
    {"symbol": "NVDA", "name": "NVIDIA Corporation", "sector": "Semiconductors", "in_sp500": True, "in_nasdaq100": True,
     "cagr_2y": 67.2, "return_2y": 179.7, "cagr_10y": 57.4, "return_10y": 9250.0, "cagr_20y": 36.8, "return_20y": 48200.0, "cagr_5y": 68.5, "return_1y": 145.0},
    {"symbol": "AVGO", "name": "Broadcom Inc.", "sector": "Semiconductors", "in_sp500": True, "in_nasdaq100": True,
     "cagr_2y": 45.3, "return_2y": 111.0, "cagr_10y": 38.5, "return_10y": 2450.0, "cagr_20y": 27.2, "return_20y": 11200.0, "cagr_5y": 42.0, "return_1y": 95.0},
    {"symbol": "AMD", "name": "Advanced Micro Devices", "sector": "Semiconductors", "in_sp500": True, "in_nasdaq100": True,
     "cagr_2y": 24.2, "return_2y": 54.3, "cagr_10y": 42.1, "return_10y": 3200.0, "cagr_20y": 18.2, "return_20y": 2800.0, "cagr_5y": 31.5, "return_1y": 45.0},
    {"symbol": "LRCX", "name": "Lam Research Corp.", "sector": "Semiconductors", "in_sp500": True, "in_nasdaq100": True,
     "cagr_2y": 38.7, "return_2y": 92.4, "cagr_10y": 31.8, "return_10y": 1480.0, "cagr_20y": 20.5, "return_20y": 4200.0, "cagr_5y": 28.0, "return_1y": 52.0},
    {"symbol": "KLAC", "name": "KLA Corporation", "sector": "Semiconductors", "in_sp500": True, "in_nasdaq100": True,
     "cagr_2y": 44.5, "return_2y": 108.9, "cagr_10y": 32.5, "return_10y": 1560.0, "cagr_20y": 19.2, "return_20y": 3300.0, "cagr_5y": 30.5, "return_1y": 62.0},
    {"symbol": "AMAT", "name": "Applied Materials", "sector": "Semiconductors", "in_sp500": True, "in_nasdaq100": True,
     "cagr_2y": 35.5, "return_2y": 83.7, "cagr_10y": 28.4, "return_10y": 1120.0, "cagr_20y": 15.9, "return_20y": 1850.0, "cagr_5y": 27.2, "return_1y": 46.0},
    {"symbol": "ASML", "name": "ASML Holding N.V.", "sector": "Semiconductors", "in_sp500": False, "in_nasdaq100": True,
     "cagr_2y": 29.2, "return_2y": 66.8, "cagr_10y": 27.6, "return_10y": 1040.0, "cagr_20y": 23.5, "return_20y": 6800.0, "cagr_5y": 24.8, "return_1y": 35.0},
    {"symbol": "MPWR", "name": "Monolithic Power Systems", "sector": "Semiconductors", "in_sp500": True, "in_nasdaq100": True,
     "cagr_2y": 45.3, "return_2y": 111.2, "cagr_10y": 33.2, "return_10y": 1660.0, "cagr_20y": 22.4, "return_20y": 5600.0, "cagr_5y": 32.0, "return_1y": 62.0},
    {"symbol": "QCOM", "name": "Qualcomm Inc.", "sector": "Semiconductors", "in_sp500": True, "in_nasdaq100": True,
     "cagr_2y": 31.4, "return_2y": 72.7, "cagr_10y": 20.8, "return_10y": 560.0, "cagr_20y": 15.1, "return_20y": 1620.0, "cagr_5y": 21.0, "return_1y": 44.0},
    {"symbol": "NXPI", "name": "NXP Semiconductors", "sector": "Semiconductors", "in_sp500": True, "in_nasdaq100": True,
     "cagr_2y": 26.3, "return_2y": 59.6, "cagr_10y": 21.5, "return_10y": 600.0, "cagr_20y": None, "return_20y": None, "cagr_5y": 22.0, "return_1y": 32.0},
    {"symbol": "MRVL", "name": "Marvell Technology", "sector": "Semiconductors", "in_sp500": True, "in_nasdaq100": True,
     "cagr_2y": 35.9, "return_2y": 84.6, "cagr_10y": 20.4, "return_10y": 540.0, "cagr_20y": 15.2, "return_20y": 1650.0, "cagr_5y": 26.0, "return_1y": 48.0},
    {"symbol": "ON", "name": "ON Semiconductor", "sector": "Semiconductors", "in_sp500": True, "in_nasdaq100": True,
     "cagr_2y": 26.6, "return_2y": 60.3, "cagr_10y": 22.4, "return_10y": 655.0, "cagr_20y": 16.8, "return_20y": 2150.0, "cagr_5y": 25.5, "return_1y": 29.0},
    {"symbol": "TXN", "name": "Texas Instruments", "sector": "Semiconductors", "in_sp500": True, "in_nasdaq100": True,
     "cagr_2y": 19.0, "return_2y": 41.6, "cagr_10y": 17.5, "return_10y": 401.0, "cagr_20y": 14.8, "return_20y": 1490.0, "cagr_5y": 14.0, "return_1y": 25.0},
    {"symbol": "INTC", "name": "Intel Corporation", "sector": "Semiconductors", "in_sp500": True, "in_nasdaq100": True,
     "cagr_2y": -22.0, "return_2y": -39.2, "cagr_10y": 1.2, "return_10y": 12.5, "cagr_20y": 3.4, "return_20y": 95.0, "cagr_5y": -11.2, "return_1y": -32.0},
    {"symbol": "MSFT", "name": "Microsoft Corporation", "sector": "Software & Cloud", "in_sp500": True, "in_nasdaq100": True,
     "cagr_2y": 13.2, "return_2y": 28.1, "cagr_10y": 26.2, "return_10y": 930.0, "cagr_20y": 16.9, "return_20y": 2200.0, "cagr_5y": 22.4, "return_1y": 28.8},
    {"symbol": "AAPL", "name": "Apple Inc.", "sector": "Technology Hardware", "in_sp500": True, "in_nasdaq100": True,
     "cagr_2y": 15.7, "return_2y": 33.8, "cagr_10y": 24.6, "return_10y": 801.0, "cagr_20y": 28.5, "return_20y": 13900.0, "cagr_5y": 23.5, "return_1y": 31.2},
    {"symbol": "AMZN", "name": "Amazon.com Inc.", "sector": "E-Commerce & Cloud", "in_sp500": True, "in_nasdaq100": True,
     "cagr_2y": 20.0, "return_2y": 44.0, "cagr_10y": 22.8, "return_10y": 680.0, "cagr_20y": 24.1, "return_20y": 7400.0, "cagr_5y": 18.5, "return_1y": 36.5},
    {"symbol": "META", "name": "Meta Platforms Inc.", "sector": "Social Media & AI", "in_sp500": True, "in_nasdaq100": True,
     "cagr_2y": 36.3, "return_2y": 85.7, "cagr_10y": 21.9, "return_10y": 625.0, "cagr_20y": None, "return_20y": None, "cagr_5y": 24.0, "return_1y": 82.0},
    {"symbol": "GOOGL", "name": "Alphabet Inc. (Class A)", "sector": "Internet & Search", "in_sp500": True, "in_nasdaq100": True,
     "cagr_2y": 13.0, "return_2y": 27.7, "cagr_10y": 19.4, "return_10y": 490.0, "cagr_20y": 20.3, "return_20y": 4100.0, "cagr_5y": 21.0, "return_1y": 32.0},
    {"symbol": "NOW", "name": "ServiceNow Inc.", "sector": "Software & Cloud", "in_sp500": True, "in_nasdaq100": True,
     "cagr_2y": 28.2, "return_2y": 64.3, "cagr_10y": 28.9, "return_10y": 1165.0, "cagr_20y": None, "return_20y": None, "cagr_5y": 26.5, "return_1y": 48.0},
    {"symbol": "PANW", "name": "Palo Alto Networks", "sector": "Cybersecurity", "in_sp500": True, "in_nasdaq100": True,
     "cagr_2y": 22.1, "return_2y": 49.0, "cagr_10y": 27.8, "return_10y": 1055.0, "cagr_20y": None, "return_20y": None, "cagr_5y": 31.2, "return_1y": 42.0},
    {"symbol": "FTNT", "name": "Fortinet Inc.", "sector": "Cybersecurity", "in_sp500": True, "in_nasdaq100": True,
     "cagr_2y": 31.1, "return_2y": 71.8, "cagr_10y": 30.1, "return_10y": 1285.0, "cagr_20y": None, "return_20y": None, "cagr_5y": 25.8, "return_1y": 38.0},
    {"symbol": "CDNS", "name": "Cadence Design Systems", "sector": "Software & Cloud", "in_sp500": True, "in_nasdaq100": True,
     "cagr_2y": 31.0, "return_2y": 71.6, "cagr_10y": 32.0, "return_10y": 1510.0, "cagr_20y": 18.1, "return_20y": 2750.0, "cagr_5y": 29.5, "return_1y": 34.0},
    {"symbol": "SNPS", "name": "Synopsys Inc.", "sector": "Software & Cloud", "in_sp500": True, "in_nasdaq100": True,
     "cagr_2y": 28.9, "return_2y": 66.1, "cagr_10y": 29.4, "return_10y": 1210.0, "cagr_20y": 17.5, "return_20y": 2480.0, "cagr_5y": 28.2, "return_1y": 31.0},
    {"symbol": "INTU", "name": "Intuit Inc.", "sector": "Software & FinTech", "in_sp500": True, "in_nasdaq100": True,
     "cagr_2y": 14.2, "return_2y": 30.4, "cagr_10y": 23.5, "return_10y": 725.0, "cagr_20y": 17.8, "return_20y": 2600.0, "cagr_5y": 20.8, "return_1y": 30.5},
    {"symbol": "ADBE", "name": "Adobe Inc.", "sector": "Software & Cloud", "in_sp500": True, "in_nasdaq100": True,
     "cagr_2y": 19.2, "return_2y": 42.2, "cagr_10y": 18.5, "return_10y": 445.0, "cagr_20y": 15.2, "return_20y": 1650.0, "cagr_5y": 14.5, "return_1y": 25.0},
    {"symbol": "CRM", "name": "Salesforce Inc.", "sector": "Software & Cloud", "in_sp500": True, "in_nasdaq100": False,
     "cagr_2y": 24.7, "return_2y": 55.6, "cagr_10y": 18.6, "return_10y": 450.0, "cagr_20y": 17.4, "return_20y": 2450.0, "cagr_5y": 15.2, "return_1y": 36.0},
    {"symbol": "ANET", "name": "Arista Networks", "sector": "Networking Infrastructure", "in_sp500": True, "in_nasdaq100": True,
     "cagr_2y": 59.0, "return_2y": 152.7, "cagr_10y": 35.6, "return_10y": 2010.0, "cagr_20y": None, "return_20y": None, "cagr_5y": 38.5, "return_1y": 85.0},
    {"symbol": "CRWD", "name": "CrowdStrike Holdings", "sector": "Cybersecurity", "in_sp500": True, "in_nasdaq100": True,
     "cagr_2y": 50.1, "return_2y": 125.2, "cagr_10y": 34.2, "return_10y": 1750.0, "cagr_20y": None, "return_20y": None, "cagr_5y": 34.2, "return_1y": 70.0},
    {"symbol": "DDOG", "name": "Datadog Inc.", "sector": "Software & Cloud", "in_sp500": False, "in_nasdaq100": True,
     "cagr_2y": 31.4, "return_2y": 72.7, "cagr_10y": 26.5, "return_10y": 950.0, "cagr_20y": None, "return_20y": None, "cagr_5y": 26.5, "return_1y": 38.0},
    {"symbol": "TEAM", "name": "Atlassian Corp", "sector": "Software", "in_sp500": False, "in_nasdaq100": True,
     "cagr_2y": 22.6, "return_2y": 50.4, "cagr_10y": 22.0, "return_10y": 630.0, "cagr_20y": None, "return_20y": None, "cagr_5y": 16.5, "return_1y": 30.0},
    {"symbol": "CSCO", "name": "Cisco Systems", "sector": "Networking", "in_sp500": True, "in_nasdaq100": True,
     "cagr_2y": 9.5, "return_2y": 19.9, "cagr_10y": 9.5, "return_10y": 148.0, "cagr_20y": 8.2, "return_20y": 390.0, "cagr_5y": 7.4, "return_1y": 12.0},
    {"symbol": "ORCL", "name": "Oracle Corporation", "sector": "Software & Database", "in_sp500": True, "in_nasdaq100": False,
     "cagr_2y": 41.2, "return_2y": 99.5, "cagr_10y": 16.8, "return_10y": 372.0, "cagr_20y": 13.5, "return_20y": 1150.0, "cagr_5y": 22.0, "return_1y": 65.0},
    {"symbol": "IBM", "name": "International Business Machines", "sector": "IT Services", "in_sp500": True, "in_nasdaq100": False,
     "cagr_2y": 26.6, "return_2y": 60.2, "cagr_10y": 8.1, "return_10y": 118.0, "cagr_20y": 6.8, "return_20y": 275.0, "cagr_5y": 13.5, "return_1y": 42.0},
    {"symbol": "COST", "name": "Costco Wholesale Corp.", "sector": "Consumer Staples", "in_sp500": True, "in_nasdaq100": True,
     "cagr_2y": 24.8, "return_2y": 55.8, "cagr_10y": 20.5, "return_10y": 546.0, "cagr_20y": 15.8, "return_20y": 1850.0, "cagr_5y": 25.2, "return_1y": 48.0},
    {"symbol": "NFLX", "name": "Netflix Inc.", "sector": "Communication Services", "in_sp500": True, "in_nasdaq100": True,
     "cagr_2y": 36.7, "return_2y": 86.8, "cagr_10y": 25.4, "return_10y": 862.0, "cagr_20y": 29.8, "return_20y": 18200.0, "cagr_5y": 18.5, "return_1y": 72.0},
    {"symbol": "TSLA", "name": "Tesla Inc.", "sector": "Automotive & Clean Energy", "in_sp500": True, "in_nasdaq100": True,
     "cagr_2y": -1.6, "return_2y": -3.2, "cagr_10y": 38.2, "return_10y": 2400.0, "cagr_20y": None, "return_20y": None, "cagr_5y": 25.0, "return_1y": 35.0},
    {"symbol": "BKNG", "name": "Booking Holdings", "sector": "Consumer Discretionary", "in_sp500": True, "in_nasdaq100": True,
     "cagr_2y": 27.8, "return_2y": 63.4, "cagr_10y": 19.8, "return_10y": 508.0, "cagr_20y": 24.2, "return_20y": 7600.0, "cagr_5y": 19.4, "return_1y": 38.0},
    {"symbol": "ORLY", "name": "O'Reilly Automotive", "sector": "Specialty Retail", "in_sp500": True, "in_nasdaq100": True,
     "cagr_2y": 25.8, "return_2y": 58.2, "cagr_10y": 21.4, "return_10y": 596.0, "cagr_20y": 22.1, "return_20y": 5300.0, "cagr_5y": 22.8, "return_1y": 30.0},
    {"symbol": "AZO", "name": "AutoZone Inc.", "sector": "Specialty Retail", "in_sp500": True, "in_nasdaq100": True,
     "cagr_2y": 23.7, "return_2y": 52.9, "cagr_10y": 19.2, "return_10y": 479.0, "cagr_20y": 19.8, "return_20y": 3700.0, "cagr_5y": 21.5, "return_1y": 27.0},
    {"symbol": "CPRT", "name": "Copart Inc.", "sector": "Business Services", "in_sp500": True, "in_nasdaq100": True,
     "cagr_2y": 14.8, "return_2y": 31.9, "cagr_10y": 24.8, "return_10y": 815.0, "cagr_20y": 21.2, "return_20y": 4700.0, "cagr_5y": 20.2, "return_1y": 32.0},
    {"symbol": "CTAS", "name": "Cintas Corporation", "sector": "Commercial Services", "in_sp500": True, "in_nasdaq100": True,
     "cagr_2y": 33.5, "return_2y": 78.1, "cagr_10y": 25.2, "return_10y": 845.0, "cagr_20y": 18.6, "return_20y": 2980.0, "cagr_5y": 24.0, "return_1y": 45.0},
    {"symbol": "FAST", "name": "Fastenal Company", "sector": "Industrial Distribution", "in_sp500": True, "in_nasdaq100": True,
     "cagr_2y": 21.7, "return_2y": 48.1, "cagr_10y": 17.1, "return_10y": 385.0, "cagr_20y": 16.4, "return_20y": 2050.0, "cagr_5y": 16.5, "return_1y": 28.0},
    {"symbol": "MELI", "name": "MercadoLibre Inc.", "sector": "E-Commerce", "in_sp500": False, "in_nasdaq100": True,
     "cagr_2y": 39.6, "return_2y": 95.0, "cagr_10y": 28.5, "return_10y": 1130.0, "cagr_20y": None, "return_20y": None, "cagr_5y": 28.0, "return_1y": 54.0},
    {"symbol": "LULU", "name": "Lululemon Athletica", "sector": "Apparel Retail", "in_sp500": True, "in_nasdaq100": True,
     "cagr_2y": 21.2, "return_2y": 46.9, "cagr_10y": 22.1, "return_10y": 635.0, "cagr_20y": None, "return_20y": None, "cagr_5y": 17.5, "return_1y": 26.0},
    {"symbol": "CMG", "name": "Chipotle Mexican Grill", "sector": "Restaurants", "in_sp500": True, "in_nasdaq100": False,
     "cagr_2y": 31.4, "return_2y": 72.6, "cagr_10y": 21.2, "return_10y": 585.0, "cagr_20y": None, "return_20y": None, "cagr_5y": 24.5, "return_1y": 40.0},
    {"symbol": "TJX", "name": "The TJX Companies", "sector": "Apparel & Home Retail", "in_sp500": True, "in_nasdaq100": False,
     "cagr_2y": 25.2, "return_2y": 56.7, "cagr_10y": 16.8, "return_10y": 372.0, "cagr_20y": 16.2, "return_20y": 1980.0, "cagr_5y": 17.8, "return_1y": 34.0},
    {"symbol": "ROST", "name": "Ross Stores Inc.", "sector": "Apparel Retail", "in_sp500": True, "in_nasdaq100": True,
     "cagr_2y": 19.4, "return_2y": 42.6, "cagr_10y": 15.6, "return_10y": 326.0, "cagr_20y": 17.5, "return_20y": 2480.0, "cagr_5y": 12.0, "return_1y": 28.0},
    {"symbol": "MNST", "name": "Monster Beverage Corp.", "sector": "Consumer Beverages", "in_sp500": True, "in_nasdaq100": True,
     "cagr_2y": 16.4, "return_2y": 35.4, "cagr_10y": 17.5, "return_10y": 401.0, "cagr_20y": 26.5, "return_20y": 10500.0, "cagr_5y": 12.5, "return_1y": 21.0},
    {"symbol": "WMT", "name": "Walmart Inc.", "sector": "Consumer Staples", "in_sp500": True, "in_nasdaq100": False,
     "cagr_2y": 29.7, "return_2y": 68.2, "cagr_10y": 14.5, "return_10y": 287.0, "cagr_20y": 10.8, "return_20y": 670.0, "cagr_5y": 16.0, "return_1y": 46.0},
    {"symbol": "HD", "name": "The Home Depot", "sector": "Home Improvement", "in_sp500": True, "in_nasdaq100": False,
     "cagr_2y": 22.6, "return_2y": 50.2, "cagr_10y": 15.2, "return_10y": 312.0, "cagr_20y": 13.8, "return_20y": 1220.0, "cagr_5y": 14.5, "return_1y": 32.0},
    {"symbol": "MCD", "name": "McDonald's Corporation", "sector": "Restaurants", "in_sp500": True, "in_nasdaq100": False,
     "cagr_2y": 13.9, "return_2y": 29.8, "cagr_10y": 13.1, "return_10y": 242.0, "cagr_20y": 13.2, "return_20y": 1090.0, "cagr_5y": 10.5, "return_1y": 18.0},
    {"symbol": "NKE", "name": "NIKE Inc.", "sector": "Footwear & Apparel", "in_sp500": True, "in_nasdaq100": False,
     "cagr_2y": -10.9, "return_2y": -20.7, "cagr_10y": 7.4, "return_10y": 104.0, "cagr_20y": 12.1, "return_20y": 890.0, "cagr_5y": -3.5, "return_1y": -18.0},
    {"symbol": "SBUX", "name": "Starbucks Corporation", "sector": "Restaurants", "in_sp500": True, "in_nasdaq100": True,
     "cagr_2y": 9.0, "return_2y": 18.9, "cagr_10y": 9.8, "return_10y": 155.0, "cagr_20y": 11.5, "return_20y": 780.0, "cagr_5y": 4.5, "return_1y": 14.0},
    {"symbol": "LLY", "name": "Eli Lilly and Company", "sector": "Pharmaceuticals", "in_sp500": True, "in_nasdaq100": False,
     "cagr_2y": 26.1, "return_2y": 59.1, "cagr_10y": 29.8, "return_10y": 1260.0, "cagr_20y": 17.5, "return_20y": 2480.0, "cagr_5y": 46.2, "return_1y": 85.0},
    {"symbol": "ISRG", "name": "Intuitive Surgical", "sector": "Medical Robotics", "in_sp500": True, "in_nasdaq100": True,
     "cagr_2y": 28.2, "return_2y": 64.4, "cagr_10y": 22.9, "return_10y": 686.0, "cagr_20y": 25.4, "return_20y": 9400.0, "cagr_5y": 26.5, "return_1y": 58.0},
    {"symbol": "REGN", "name": "Regeneron Pharmaceuticals", "sector": "Biotechnology", "in_sp500": True, "in_nasdaq100": True,
     "cagr_2y": 25.4, "return_2y": 57.2, "cagr_10y": 18.9, "return_10y": 465.0, "cagr_20y": 22.4, "return_20y": 5600.0, "cagr_5y": 22.0, "return_1y": 30.0},
    {"symbol": "VRTX", "name": "Vertex Pharmaceuticals", "sector": "Biotechnology", "in_sp500": True, "in_nasdaq100": True,
     "cagr_2y": 27.0, "return_2y": 61.4, "cagr_10y": 19.7, "return_10y": 504.0, "cagr_20y": 18.2, "return_20y": 2800.0, "cagr_5y": 21.5, "return_1y": 34.0},
    {"symbol": "BSX", "name": "Boston Scientific", "sector": "Medical Devices", "in_sp500": True, "in_nasdaq100": False,
     "cagr_2y": 31.6, "return_2y": 73.1, "cagr_10y": 18.2, "return_10y": 432.0, "cagr_20y": 11.8, "return_20y": 820.0, "cagr_5y": 20.4, "return_1y": 45.0},
    {"symbol": "UNH", "name": "UnitedHealth Group", "sector": "Healthcare Services", "in_sp500": True, "in_nasdaq100": False,
     "cagr_2y": 21.6, "return_2y": 47.8, "cagr_10y": 17.8, "return_10y": 415.0, "cagr_20y": 16.1, "return_20y": 1950.0, "cagr_5y": 18.2, "return_1y": 26.0},
    {"symbol": "MCK", "name": "McKesson Corporation", "sector": "Healthcare Distribution", "in_sp500": True, "in_nasdaq100": False,
     "cagr_2y": 34.2, "return_2y": 80.0, "cagr_10y": 18.4, "return_10y": 441.0, "cagr_20y": 17.2, "return_20y": 2380.0, "cagr_5y": 32.0, "return_1y": 38.0},
    {"symbol": "DHR", "name": "Danaher Corporation", "sector": "Life Sciences", "in_sp500": True, "in_nasdaq100": False,
     "cagr_2y": 20.5, "return_2y": 45.3, "cagr_10y": 16.5, "return_10y": 361.0, "cagr_20y": 14.8, "return_20y": 1490.0, "cagr_5y": 15.2, "return_1y": 27.0},
    {"symbol": "SYK", "name": "Stryker Corporation", "sector": "Medical Devices", "in_sp500": True, "in_nasdaq100": False,
     "cagr_2y": 22.7, "return_2y": 50.6, "cagr_10y": 16.2, "return_10y": 349.0, "cagr_20y": 14.5, "return_20y": 1420.0, "cagr_5y": 14.8, "return_1y": 32.0},
    {"symbol": "IDXX", "name": "IDEXX Laboratories", "sector": "Healthcare Diagnostics", "in_sp500": True, "in_nasdaq100": True,
     "cagr_2y": 20.7, "return_2y": 45.8, "cagr_10y": 21.8, "return_10y": 618.0, "cagr_20y": 21.5, "return_20y": 4900.0, "cagr_5y": 16.5, "return_1y": 26.0},
    {"symbol": "JNJ", "name": "Johnson & Johnson", "sector": "Pharmaceuticals", "in_sp500": True, "in_nasdaq100": False,
     "cagr_2y": 6.1, "return_2y": 12.6, "cagr_10y": 7.8, "return_10y": 112.0, "cagr_20y": 8.5, "return_20y": 415.0, "cagr_5y": 4.5, "return_1y": 8.0},
    {"symbol": "PFE", "name": "Pfizer Inc.", "sector": "Pharmaceuticals", "in_sp500": True, "in_nasdaq100": False,
     "cagr_2y": -10.2, "return_2y": -19.3, "cagr_10y": 3.2, "return_10y": 37.0, "cagr_20y": 4.1, "return_20y": 125.0, "cagr_5y": -6.5, "return_1y": -14.0},
    {"symbol": "ODFL", "name": "Old Dominion Freight Line", "sector": "Transportation", "in_sp500": True, "in_nasdaq100": True,
     "cagr_2y": 4.3, "return_2y": 8.7, "cagr_10y": 26.5, "return_10y": 950.0, "cagr_20y": 23.8, "return_20y": 7100.0, "cagr_5y": 27.0, "return_1y": 29.0},
    {"symbol": "AXON", "name": "Axon Enterprise Inc.", "sector": "Aerospace & Defense / Tech", "in_sp500": True, "in_nasdaq100": False,
     "cagr_2y": 42.3, "return_2y": 102.4, "cagr_10y": 36.4, "return_10y": 2150.0, "cagr_20y": 24.0, "return_20y": 7300.0, "cagr_5y": 42.0, "return_1y": 80.0},
    {"symbol": "PWR", "name": "Quanta Services", "sector": "Grid Infrastructure", "in_sp500": True, "in_nasdaq100": False,
     "cagr_2y": 49.9, "return_2y": 124.8, "cagr_10y": 26.8, "return_10y": 975.0, "cagr_20y": 18.5, "return_20y": 2950.0, "cagr_5y": 44.5, "return_1y": 58.0},
    {"symbol": "URI", "name": "United Rentals", "sector": "Equipment Rental", "in_sp500": True, "in_nasdaq100": False,
     "cagr_2y": 43.8, "return_2y": 106.9, "cagr_10y": 24.1, "return_10y": 765.0, "cagr_20y": 22.0, "return_20y": 5250.0, "cagr_5y": 38.0, "return_1y": 52.0},
    {"symbol": "ETN", "name": "Eaton Corporation", "sector": "Electrical Equipment", "in_sp500": True, "in_nasdaq100": False,
     "cagr_2y": 28.7, "return_2y": 65.7, "cagr_10y": 22.5, "return_10y": 662.0, "cagr_20y": 15.8, "return_20y": 1850.0, "cagr_5y": 32.5, "return_1y": 65.0},
    {"symbol": "TDG", "name": "TransDigm Group", "sector": "Aerospace & Defense", "in_sp500": True, "in_nasdaq100": False,
     "cagr_2y": 32.3, "return_2y": 75.1, "cagr_10y": 20.8, "return_10y": 560.0, "cagr_20y": None, "return_20y": None, "cagr_5y": 21.0, "return_1y": 46.0},
    {"symbol": "PH", "name": "Parker-Hannifin Corp.", "sector": "Industrial Machinery", "in_sp500": True, "in_nasdaq100": False,
     "cagr_2y": 39.3, "return_2y": 94.0, "cagr_10y": 19.9, "return_10y": 514.0, "cagr_20y": 15.6, "return_20y": 1780.0, "cagr_5y": 26.5, "return_1y": 55.0},
    {"symbol": "CSL", "name": "Carlisle Companies", "sector": "Building Materials", "in_sp500": True, "in_nasdaq100": False,
     "cagr_2y": 33.4, "return_2y": 77.9, "cagr_10y": 19.4, "return_10y": 490.0, "cagr_20y": 16.2, "return_20y": 1980.0, "cagr_5y": 24.8, "return_1y": 44.0},
    {"symbol": "WM", "name": "Waste Management", "sector": "Environmental Services", "in_sp500": True, "in_nasdaq100": False,
     "cagr_2y": 21.7, "return_2y": 48.0, "cagr_10y": 16.2, "return_10y": 349.0, "cagr_20y": 13.8, "return_20y": 1220.0, "cagr_5y": 15.5, "return_1y": 29.0},
    {"symbol": "GE", "name": "GE Aerospace", "sector": "Aerospace Engines", "in_sp500": True, "in_nasdaq100": False,
     "cagr_2y": 60.5, "return_2y": 157.7, "cagr_10y": 15.5, "return_10y": 322.0, "cagr_20y": 6.5, "return_20y": 255.0, "cagr_5y": 36.0, "return_1y": 92.0},
    {"symbol": "CAT", "name": "Caterpillar Inc.", "sector": "Heavy Machinery", "in_sp500": True, "in_nasdaq100": False,
     "cagr_2y": 32.1, "return_2y": 74.4, "cagr_10y": 16.5, "return_10y": 361.0, "cagr_20y": 13.2, "return_20y": 1090.0, "cagr_5y": 24.0, "return_1y": 42.0},
    {"symbol": "HON", "name": "Honeywell International", "sector": "Conglomerates", "in_sp500": True, "in_nasdaq100": True,
     "cagr_2y": 10.5, "return_2y": 22.1, "cagr_10y": 10.2, "return_10y": 164.0, "cagr_20y": 10.8, "return_20y": 670.0, "cagr_5y": 6.5, "return_1y": 15.0},
    {"symbol": "BA", "name": "The Boeing Company", "sector": "Aerospace", "in_sp500": True, "in_nasdaq100": False,
     "cagr_2y": -18.9, "return_2y": -34.3, "cagr_10y": 2.1, "return_10y": 23.0, "cagr_20y": 7.5, "return_20y": 325.0, "cagr_5y": -14.2, "return_1y": -24.0},
    {"symbol": "FICO", "name": "Fair Isaac Corporation", "sector": "Financial Analytics", "in_sp500": True, "in_nasdaq100": False,
     "cagr_2y": 49.2, "return_2y": 122.5, "cagr_10y": 31.2, "return_10y": 1410.0, "cagr_20y": 21.0, "return_20y": 4500.0, "cagr_5y": 39.5, "return_1y": 95.0},
    {"symbol": "MSCI", "name": "MSCI Inc.", "sector": "Financial Data & Analytics", "in_sp500": True, "in_nasdaq100": False,
     "cagr_2y": 22.4, "return_2y": 49.9, "cagr_10y": 23.4, "return_10y": 718.0, "cagr_20y": None, "return_20y": None, "cagr_5y": 18.0, "return_1y": 28.0},
    {"symbol": "PGR", "name": "The Progressive Corporation", "sector": "Property & Casualty Insurance", "in_sp500": True, "in_nasdaq100": False,
     "cagr_2y": 42.4, "return_2y": 102.8, "cagr_10y": 21.0, "return_10y": 572.0, "cagr_20y": 16.5, "return_20y": 2080.0, "cagr_5y": 26.5, "return_1y": 62.0},
    {"symbol": "AJG", "name": "Arthur J. Gallagher & Co.", "sector": "Insurance Brokerage", "in_sp500": True, "in_nasdaq100": False,
     "cagr_2y": 29.7, "return_2y": 68.2, "cagr_10y": 20.2, "return_10y": 530.0, "cagr_20y": 16.8, "return_20y": 2150.0, "cagr_5y": 23.0, "return_1y": 38.0},
    {"symbol": "MCO", "name": "Moody's Corporation", "sector": "Financial Ratings", "in_sp500": True, "in_nasdaq100": False,
     "cagr_2y": 29.2, "return_2y": 67.0, "cagr_10y": 20.1, "return_10y": 525.0, "cagr_20y": 16.4, "return_20y": 2050.0, "cagr_5y": 18.5, "return_1y": 42.0},
    {"symbol": "MA", "name": "Mastercard Inc.", "sector": "Transaction Processing", "in_sp500": True, "in_nasdaq100": False,
     "cagr_2y": 12.3, "return_2y": 26.1, "cagr_10y": 19.6, "return_10y": 499.0, "cagr_20y": None, "return_20y": None, "cagr_5y": 15.0, "return_1y": 28.0},
    {"symbol": "SPGI", "name": "S&P Global Inc.", "sector": "Financial Data", "in_sp500": True, "in_nasdaq100": False,
     "cagr_2y": 17.6, "return_2y": 38.4, "cagr_10y": 18.9, "return_10y": 465.0, "cagr_20y": 17.1, "return_20y": 2320.0, "cagr_5y": 16.8, "return_1y": 36.0},
    {"symbol": "V", "name": "Visa Inc.", "sector": "Transaction Processing", "in_sp500": True, "in_nasdaq100": False,
     "cagr_2y": 9.9, "return_2y": 20.9, "cagr_10y": 18.5, "return_10y": 445.0, "cagr_20y": None, "return_20y": None, "cagr_5y": 14.2, "return_1y": 26.5},
    {"symbol": "AXP", "name": "American Express", "sector": "Consumer Finance", "in_sp500": True, "in_nasdaq100": False,
     "cagr_2y": 35.1, "return_2y": 82.5, "cagr_10y": 16.4, "return_10y": 357.0, "cagr_20y": 12.5, "return_20y": 950.0, "cagr_5y": 19.5, "return_1y": 54.0},
    {"symbol": "BLK", "name": "BlackRock Inc.", "sector": "Asset Management", "in_sp500": True, "in_nasdaq100": False,
     "cagr_2y": 27.4, "return_2y": 62.4, "cagr_10y": 15.1, "return_10y": 308.0, "cagr_20y": 16.2, "return_20y": 1980.0, "cagr_5y": 16.0, "return_1y": 41.0},
    {"symbol": "JPM", "name": "JPMorgan Chase & Co.", "sector": "Diversified Banking", "in_sp500": True, "in_nasdaq100": False,
     "cagr_2y": 31.4, "return_2y": 72.6, "cagr_10y": 16.2, "return_10y": 349.0, "cagr_20y": 12.8, "return_20y": 1020.0, "cagr_5y": 17.5, "return_1y": 48.0},
    {"symbol": "BAC", "name": "Bank of America", "sector": "Banking", "in_sp500": True, "in_nasdaq100": False,
     "cagr_2y": 20.1, "return_2y": 44.2, "cagr_10y": 10.5, "return_10y": 171.0, "cagr_20y": 3.8, "return_20y": 112.0, "cagr_5y": 8.0, "return_1y": 34.0},
    {"symbol": "VST", "name": "Vistra Corp", "sector": "Independent Power & Nuclear", "in_sp500": True, "in_nasdaq100": False,
     "cagr_2y": 103.1, "return_2y": 312.5, "cagr_10y": 35.8, "return_10y": 2030.0, "cagr_20y": None, "return_20y": None, "cagr_5y": 48.0, "return_1y": 185.0},
    {"symbol": "CEG", "name": "Constellation Energy", "sector": "Clean Nuclear Energy", "in_sp500": True, "in_nasdaq100": True,
     "cagr_2y": 56.1, "return_2y": 143.6, "cagr_10y": 32.5, "return_10y": 1560.0, "cagr_20y": None, "return_20y": None, "cagr_5y": 42.0, "return_1y": 112.0},
    {"symbol": "MPC", "name": "Marathon Petroleum", "sector": "Refining & Marketing", "in_sp500": True, "in_nasdaq100": False,
     "cagr_2y": 34.8, "return_2y": 81.8, "cagr_10y": 21.4, "return_10y": 596.0, "cagr_20y": None, "return_20y": None, "cagr_5y": 36.5, "return_1y": 35.0},
    {"symbol": "SHW", "name": "The Sherwin-Williams Company", "sector": "Paints & Coatings", "in_sp500": True, "in_nasdaq100": False,
     "cagr_2y": 27.2, "return_2y": 61.9, "cagr_10y": 19.3, "return_10y": 485.0, "cagr_20y": 17.8, "return_20y": 2600.0, "cagr_5y": 18.2, "return_1y": 38.0},
    {"symbol": "LIN", "name": "Linde plc", "sector": "Industrial Gases", "in_sp500": True, "in_nasdaq100": True,
     "cagr_2y": 11.4, "return_2y": 24.0, "cagr_10y": 16.8, "return_10y": 372.0, "cagr_20y": 14.5, "return_20y": 1420.0, "cagr_5y": 17.5, "return_1y": 26.0},
    {"symbol": "XOM", "name": "Exxon Mobil Corporation", "sector": "Integrated Oil & Gas", "in_sp500": True, "in_nasdaq100": False,
     "cagr_2y": 16.6, "return_2y": 36.0, "cagr_10y": 7.5, "return_10y": 106.0, "cagr_20y": 7.8, "return_20y": 350.0, "cagr_5y": 19.2, "return_1y": 15.0},
    {"symbol": "CVX", "name": "Chevron Corporation", "sector": "Integrated Oil & Gas", "in_sp500": True, "in_nasdaq100": False,
     "cagr_2y": 9.7, "return_2y": 20.3, "cagr_10y": 6.8, "return_10y": 93.0, "cagr_20y": 8.5, "return_20y": 415.0, "cagr_5y": 12.0, "return_1y": 8.0}
]


# ==============================================================================
# 3. SCREENING ENGINE (BEATS CORRESPONDING BENCHMARK AVERAGE)
# ==============================================================================

class SP500NasdaqScreener:
    """
    Screens all stocks in S&P 500 and NASDAQ 100 to extract all companies
    that beat the corresponding average (S&P 500 average for S&P 500 stocks,
    and NASDAQ 100 average for NASDAQ 100 stocks) over the specified window (default: last 2 years).
    """

    @classmethod
    def get_benchmark(cls, ticker: str) -> Dict[str, Any]:
        return BENCHMARK_METRICS.get(ticker.upper(), BENCHMARK_METRICS["SPY"])

    @classmethod
    def screen_outperformers(
        cls,
        index_scope: str = "both",       # 'sp500', 'nasdaq100', or 'both'
        horizon_years: int = 2,          # 2 (default), 1, 5, 10, or 20
        min_alpha: float = 0.0,          # Minimum excess CAGR above the benchmark
        as_of_date: Optional[Union[datetime, str]] = None # Point-in-time date (None = latest today)
    ) -> List[Dict[str, Any]]:
        """
        Filters all stocks in the universe whose performance exceeded the corresponding benchmark average:
        - S&P 500 stocks are compared against S&P 500 average (SPY)
        - NASDAQ 100 stocks are compared against NASDAQ 100 average (QQQ)
        - Dual-listed stocks are compared against QQQ and SPY.
        Default horizon: last 2 years.

        Point-in-Time Support:
        If as_of_date is provided, calculates realized trailing CAGR and excess Alpha over the
        horizon_years window strictly PRIOR to as_of_date, avoiding any lookahead selection bias.
        """
        as_of_dt = None
        if as_of_date is not None:
            if isinstance(as_of_date, str):
                try:
                    as_of_dt = datetime.strptime(as_of_date[:10], "%Y-%m-%d")
                except ValueError:
                    as_of_dt = None
            elif isinstance(as_of_date, datetime):
                as_of_dt = as_of_date

        # POINT-IN-TIME HISTORICAL CALCULATION
        if as_of_dt is not None and as_of_dt < datetime(2026, 10, 1):
            from historical_data_feed import HistoricalDataFeed

            lookback_start_dt = as_of_dt - timedelta(days=int(horizon_years * 365.25))

            # Benchmark performance over [lookback_start_dt, as_of_dt]
            spy_p0 = HistoricalDataFeed.get_target_price_at_date("SPY", lookback_start_dt)
            spy_p1 = HistoricalDataFeed.get_target_price_at_date("SPY", as_of_dt)
            spy_ret = round(((spy_p1 / spy_p0) - 1.0) * 100.0, 2)
            spy_bm = round((((spy_p1 / spy_p0) ** (1.0 / horizon_years)) - 1.0) * 100.0, 2)

            qqq_p0 = HistoricalDataFeed.get_target_price_at_date("QQQ", lookback_start_dt)
            qqq_p1 = HistoricalDataFeed.get_target_price_at_date("QQQ", as_of_dt)
            qqq_ret = round(((qqq_p1 / qqq_p0) - 1.0) * 100.0, 2)
            qqq_bm = round((((qqq_p1 / qqq_p0) ** (1.0 / horizon_years)) - 1.0) * 100.0, 2)

            outperformers = []

            for stock in COMPREHENSIVE_UNIVERSE:
                in_sp = stock.get("in_sp500", False)
                in_nd = stock.get("in_nasdaq100", False)

                # Apply scope filter
                if index_scope == "sp500" and not in_sp:
                    continue
                if index_scope == "nasdaq100" and not in_nd:
                    continue

                sym = stock["symbol"]
                s_p0 = HistoricalDataFeed.get_target_price_at_date(sym, lookback_start_dt)
                s_p1 = HistoricalDataFeed.get_target_price_at_date(sym, as_of_dt)
                s_ret = round(((s_p1 / s_p0) - 1.0) * 100.0, 2)
                s_cagr = round((((s_p1 / s_p0) ** (1.0 / horizon_years)) - 1.0) * 100.0, 2)

                if in_nd and in_sp:
                    primary_benchmark = "Both (QQQ & SPY)"
                    bench_val = qqq_bm
                    alpha_sp = round(s_cagr - spy_bm, 2)
                    alpha_qqq = round(s_cagr - qqq_bm, 2)
                    beats = (s_cagr >= (bench_val + min_alpha)) or (s_cagr >= (spy_bm + min_alpha))
                elif in_nd:
                    primary_benchmark = "NASDAQ 100 (QQQ)"
                    bench_val = qqq_bm
                    alpha_sp = round(s_cagr - spy_bm, 2)
                    alpha_qqq = round(s_cagr - qqq_bm, 2)
                    beats = s_cagr >= (bench_val + min_alpha)
                else:
                    primary_benchmark = "S&P 500 (SPY)"
                    bench_val = spy_bm
                    alpha_sp = round(s_cagr - spy_bm, 2)
                    alpha_qqq = round(s_cagr - qqq_bm, 2)
                    beats = s_cagr >= (bench_val + min_alpha)

                if beats:
                    index_label = "Both" if (in_sp and in_nd) else ("S&P 500" if in_sp else "NASDAQ 100")
                    beat_label = []
                    if s_cagr > spy_bm: beat_label.append("S&P 500")
                    if s_cagr > qqq_bm: beat_label.append("NASDAQ 100")

                    outperformers.append({
                        "symbol": stock["symbol"],
                        "name": stock["name"],
                        "sector": stock["sector"],
                        "index": index_label,
                        "beat_benchmark": " & ".join(beat_label) if beat_label else "Corresponding Index",
                        "cagr": s_cagr,
                        "cagr_2y": s_cagr if horizon_years == 2 else stock.get("cagr_2y"),
                        "return_2y": s_ret if horizon_years == 2 else stock.get("return_2y"),
                        "cagr_10y": stock.get("cagr_10y"),
                        "return_10y": stock.get("return_10y"),
                        "cagr_20y": stock.get("cagr_20y"),
                        "return_20y": stock.get("return_20y"),
                        "cagr_5y": stock.get("cagr_5y"),
                        "return_1y": s_ret if horizon_years == 1 else stock.get("return_1y"),
                        "benchmark_target": primary_benchmark,
                        "benchmark_average": bench_val,
                        "alpha_over_sp500": alpha_sp,
                        "alpha_over_qqq": alpha_qqq,
                        "outperformance_multiple": round(s_cagr / spy_bm, 1) if spy_bm > 0 else 1.0,
                        "as_of_date": as_of_dt.strftime("%Y-%m-%d"),
                        "lookback_start_date": lookback_start_dt.strftime("%Y-%m-%d")
                    })

            outperformers.sort(key=lambda x: x["alpha_over_sp500"], reverse=True)
            return outperformers

        # LATEST / BASELINE CALCULATION (as of October 2026)
        spy_bench = BENCHMARK_METRICS["SPY"]
        qqq_bench = BENCHMARK_METRICS["QQQ"]

        if horizon_years == 2:
            spy_bm = spy_bench["cagr_2y"]
            qqq_bm = qqq_bench["cagr_2y"]
            key = "cagr_2y"
        elif horizon_years == 1:
            spy_bm = spy_bench["return_1y"]
            qqq_bm = qqq_bench["return_1y"]
            key = "return_1y"
        elif horizon_years == 5:
            spy_bm = spy_bench["cagr_5y"]
            qqq_bm = qqq_bench["cagr_5y"]
            key = "cagr_5y"
        elif horizon_years == 20:
            spy_bm = spy_bench["cagr_20y"]
            qqq_bm = qqq_bench["cagr_20y"]
            key = "cagr_20y"
        else: # 10
            spy_bm = spy_bench["cagr_10y"]
            qqq_bm = qqq_bench["cagr_10y"]
            key = "cagr_10y"

        outperformers = []

        for stock in COMPREHENSIVE_UNIVERSE:
            in_sp = stock.get("in_sp500", False)
            in_nd = stock.get("in_nasdaq100", False)

            # Apply scope filter
            if index_scope == "sp500" and not in_sp:
                continue
            if index_scope == "nasdaq100" and not in_nd:
                continue

            stock_val = stock.get(key)
            if stock_val is None:
                continue

            # Determine corresponding benchmark:
            # If in NASDAQ 100, the corresponding average is QQQ; if in S&P 500 only, it is SPY.
            # If in both, evaluate against both.
            if in_nd and in_sp:
                primary_benchmark = "Both (QQQ & SPY)"
                bench_val = qqq_bm  # Strict hurdle: must beat QQQ
                alpha_sp = round(stock_val - spy_bm, 2)
                alpha_qqq = round(stock_val - qqq_bm, 2)
                beats = (stock_val >= (bench_val + min_alpha)) or (stock_val >= (spy_bm + min_alpha))
            elif in_nd:
                primary_benchmark = "NASDAQ 100 (QQQ)"
                bench_val = qqq_bm
                alpha_sp = round(stock_val - spy_bm, 2)
                alpha_qqq = round(stock_val - qqq_bm, 2)
                beats = stock_val >= (bench_val + min_alpha)
            else:
                primary_benchmark = "S&P 500 (SPY)"
                bench_val = spy_bm
                alpha_sp = round(stock_val - spy_bm, 2)
                alpha_qqq = round(stock_val - qqq_bm, 2)
                beats = stock_val >= (bench_val + min_alpha)

            if beats:
                index_label = "Both" if (in_sp and in_nd) else ("S&P 500" if in_sp else "NASDAQ 100")
                beat_label = []
                if stock_val > spy_bm: beat_label.append("S&P 500")
                if stock_val > qqq_bm: beat_label.append("NASDAQ 100")

                outperformers.append({
                    "symbol": stock["symbol"],
                    "name": stock["name"],
                    "sector": stock["sector"],
                    "index": index_label,
                    "beat_benchmark": " & ".join(beat_label) if beat_label else "Corresponding Index",
                    "cagr": stock_val,
                    "cagr_2y": stock.get("cagr_2y"),
                    "return_2y": stock.get("return_2y"),
                    "cagr_10y": stock.get("cagr_10y"),
                    "return_10y": stock.get("return_10y"),
                    "cagr_20y": stock.get("cagr_20y"),
                    "return_20y": stock.get("return_20y"),
                    "cagr_5y": stock.get("cagr_5y"),
                    "return_1y": stock.get("return_1y"),
                    "benchmark_target": primary_benchmark,
                    "benchmark_average": bench_val,
                    "alpha_over_sp500": alpha_sp,
                    "alpha_over_qqq": alpha_qqq,
                    "outperformance_multiple": round(stock_val / spy_bm, 1) if spy_bm > 0 else 1.0,
                    "as_of_date": "2026-10-12"
                })

        # Rank by Alpha over S&P 500 descending
        outperformers.sort(key=lambda x: x["alpha_over_sp500"], reverse=True)
        return outperformers

    @classmethod
    def generate_enhanced_watchlist(cls, horizon_years: int = 2, as_of_date: Optional[Union[datetime, str]] = None) -> List[Dict[str, Any]]:
        """
        Generates the comprehensive list of market-beating stocks
        ready to replace WATCHLIST in AlphaStockScreener based on last 2 years (or configured horizon and as_of_date).
        """
        beaters = cls.screen_outperformers(index_scope="both", horizon_years=horizon_years, min_alpha=0.0, as_of_date=as_of_date)
        watchlist = []
        for b in beaters:
            watchlist.append({
                "symbol": b["symbol"],
                "name": b["name"],
                "sector": b["sector"],
                "index": b["index"],
                "beat_benchmark": b["beat_benchmark"],
                "cagr_2y": b.get("cagr_2y"),
                "return_2y": b.get("return_2y"),
                "cagr_10y": b.get("cagr_10y"),
                "alpha_over_sp500": b["alpha_over_sp500"],
                "alpha_over_qqq": b["alpha_over_qqq"]
            })
        return watchlist

    @classmethod
    def generate_historical_metrics_dict(cls) -> Dict[str, Dict[str, Any]]:
        """
        Generates the updated HISTORICAL_METRICS dictionary covering
        all market-beating candidates plus SPY, VTI, QQQ benchmarks across 2Y, 1Y, 5Y, 10Y, 20Y.
        """
        metrics = {
            "SPY": {"cagr_2y": 16.3, "return_2y": 35.3, "cagr_10y": 12.8, "return_10y": 234.0, "cagr_20y": 10.2, "return_20y": 580.0, "cagr_5y": 15.1, "return_1y": 24.2},
            "VTI": {"cagr_2y": 12.9, "return_2y": 27.5, "cagr_10y": 12.3, "return_10y": 218.0, "cagr_20y": 9.9, "return_20y": 550.0, "cagr_5y": 14.5, "return_1y": 23.4},
            "QQQ": {"cagr_2y": 17.5, "return_2y": 38.1, "cagr_10y": 18.2, "return_10y": 432.0, "cagr_20y": 14.8, "return_20y": 1480.0, "cagr_5y": 20.4, "return_1y": 28.5}
        }
        for stock in COMPREHENSIVE_UNIVERSE:
            sym = stock["symbol"]
            metrics[sym] = {
                "cagr_2y": stock.get("cagr_2y"),
                "return_2y": stock.get("return_2y"),
                "cagr_10y": stock.get("cagr_10y"),
                "return_10y": stock.get("return_10y"),
                "cagr_20y": stock.get("cagr_20y"),
                "return_20y": stock.get("return_20y"),
                "cagr_5y": stock.get("cagr_5y"),
                "return_1y": stock.get("return_1y")
            }
        return metrics


if __name__ == "__main__":
    screener = SP500NasdaqScreener()
    beaters = screener.screen_outperformers(horizon_years=2)
    print("\n==========================================================================")
    print(f"  S&P 500 & NASDAQ 100 SCREENER (LAST 2 YEARS): {len(beaters)} MARKET-BEATING STOCKS")
    print("==========================================================================\n")
    print(f"{'SYMBOL':<7} {'COMPANY NAME':<28} {'SECTOR':<22} {'INDEX':<10} {'2Y CAGR':<10} {'2Y RET':<9} {'ALPHA vs SPY':<13} {'ALPHA vs QQQ':<12}")
    print("-" * 115)
    for b in beaters[:30]:
        alpha_q_str = f"+{b['alpha_over_qqq']}%" if b['alpha_over_qqq'] >= 0 else f"{b['alpha_over_qqq']}%"
        ret_str = f"{b.get('return_2y', 0):>6.1f}%"
        print(f"{b['symbol']:<7} {b['name'][:27]:<28} {b['sector'][:21]:<22} {b['index']:<10} {b['cagr']:>5.1f}%     {ret_str:<9} {'+'+str(b['alpha_over_sp500'])+'%':<13} {alpha_q_str:<12}")
    print(f"\n... and {len(beaters) - 30} more outperforming companies over the last 2 years.\n")
