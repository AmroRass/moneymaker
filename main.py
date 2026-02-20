"""
main.py - The main bot loop
Orchestrates: data → technicals → sentiment → signal → execution → log

Usage:
    python main.py

Make sure you've filled in your API keys in config.py first.
"""

import time
import traceback
from datetime import datetime

from config import ASSET_CONFIG, TRADE_CONFIG, validate_keys
from data import get_candles, get_news, get_forex_sentiment
from technicals import get_trend_signal
from ai_layer import get_combined_sentiment
from signal import generate_signal
from execution import submit_order
from logger import init_log, log_decision, print_decision


def run_cycle():
    """Run one full decision cycle."""

    symbol    = ASSET_CONFIG["finnhub_symbol"]
    keywords  = ASSET_CONFIG["news_keywords"]
    timeframe = TRADE_CONFIG["timeframe"]

    # 1. Fetch price data
    df = get_candles(symbol, timeframe, lookback_bars=100)
    if df.empty:
        print("[WARN] No price data, skipping cycle")
        return

    # 2. Technical analysis
    trend = get_trend_signal(df)

    # 3. News + sentiment
    articles       = get_news(keywords, lookback_hours=TRADE_CONFIG["news_lookback_hours"])
    finnhub_data   = get_forex_sentiment()
    sentiment      = get_combined_sentiment(
        finnhub_score = finnhub_data["sentiment_score"],
        articles      = articles,
        buzz          = finnhub_data["buzz"],
    )

    # 4. Generate signal
    signal = generate_signal(trend, sentiment)

    # 5. Execute
    execution = submit_order(signal)

    # 6. Log everything
    log_decision(trend, sentiment, signal, execution)
    print_decision(trend, sentiment, signal, execution)


def main():
    validate_keys()
    print("\n🏅 Gold AI Trading Bot — Paper Mode")
    print(f"   Asset:     {ASSET_CONFIG['name']} ({ASSET_CONFIG['finnhub_symbol']})")
    print(f"   Timeframe: {TRADE_CONFIG['timeframe']}min")
    print(f"   Conflict:  {TRADE_CONFIG['conflict_mode']} mode")
    print(f"   Interval:  every {TRADE_CONFIG['poll_interval_seconds']}s")
    print("="*60)

    init_log()

    while True:
        try:
            run_cycle()
        except KeyboardInterrupt:
            print("\n[BOT] Stopped by user.")
            break
        except Exception as e:
            print(f"[ERROR] {e}")
            traceback.print_exc()

        print(f"\n[BOT] Sleeping {TRADE_CONFIG['poll_interval_seconds']}s...")
        time.sleep(TRADE_CONFIG["poll_interval_seconds"])


if __name__ == "__main__":
    main()
