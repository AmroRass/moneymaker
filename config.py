"""
Asset configuration - swap this out to trade a different instrument.
Everything else in the system stays the same.
"""

ASSET_CONFIG = {
    "name": "Gold",
    "finnhub_symbol": "OANDA:XAU_USD",
    "oanda_instrument": "XAU_USD",        # OANDA instrument format
    "news_keywords": ["gold", "XAU", "fed", "inflation", "dollar", "interest rate", "central bank", "safe haven", "geopolitical"],
    "description": "Gold Spot vs USD"
}

# Trading parameters
TRADE_CONFIG = {
    "timeframe": "15",           # minutes
    "ema_fast": 9,
    "ema_slow": 21,
    "adx_period": 14,
    "adx_threshold": 20,         # min ADX to confirm trend exists
    "take_profit_pct": 0.004,    # 0.4%
    "stop_loss_pct": 0.003,      # 0.3%
    "conflict_mode": "risky",    # "risky" = trade anyway, "conservative" = skip
    "news_lookback_hours": 2,    # how far back to look for relevant news
    "poll_interval_seconds": 60, # how often to run the loop
    "oanda_units": 1,            # number of units (oz of gold) per trade — keep small for demo
}

# Sentiment thresholds
SENTIMENT_CONFIG = {
    "bullish_threshold": 0.2,    # Finnhub sentiment score above this = bullish
    "bearish_threshold": -0.2,   # below this = bearish
    "high_impact_score": 0.6,    # send to Claude for deeper analysis if above this
}

# API Keys - loaded from .env file (never hardcode keys here)
import os
from dotenv import load_dotenv
load_dotenv()

FINNHUB_API_KEY    = os.getenv("FINNHUB_API_KEY")
ANTHROPIC_API_KEY  = os.getenv("ANTHROPIC_API_KEY")
OANDA_ACCESS_TOKEN = os.getenv("OANDA_ACCESS_TOKEN")
OANDA_ACCOUNT_ID   = os.getenv("OANDA_ACCOUNT_ID")
OANDA_ENVIRONMENT  = os.getenv("OANDA_ENVIRONMENT", "practice")  # defaults to demo

def validate_keys():
    missing = [k for k, v in {
        "FINNHUB_API_KEY":    FINNHUB_API_KEY,
        "ANTHROPIC_API_KEY":  ANTHROPIC_API_KEY,
        "OANDA_ACCESS_TOKEN": OANDA_ACCESS_TOKEN,
        "OANDA_ACCOUNT_ID":   OANDA_ACCOUNT_ID,
    }.items() if not v]
    if missing:
        raise EnvironmentError(f"Missing required env vars: {', '.join(missing)}\nCopy .env.example to .env and fill in your keys.")
