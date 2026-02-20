"""
main.py - The main bot loop
Orchestrates: data → technicals → sentiment → signal → execution → log

Usage:
    python main.py
"""

import time
import traceback
from datetime import datetime

from config import ASSET_CONFIG, TRADE_CONFIG, validate_keys
from data import get_candles, get_news
from technicals import get_trend_signal
from ai_layer import get_combined_sentiment
from signalgen import generate_signal
from execution import submit_order
from logger import init_log, log_decision, print_decision


def run_cycle():
    """Run one full decision cycle."""

    symbol    = ASSET_CONFIG["oanda_instrument"]
    keywords  = ASSET_CONFIG["news_keywords"]
    timeframe = TRADE_CONFIG["timeframe"]

    # 1. Fetch 15min price data from OANDA
    df_15m = get_candles(symbol, timeframe, lookback_bars=100)
    if df_15m.empty:
        print("[WARN] No 15min price data, skipping cycle")
        return

    # 2. Fetch 1H price data for HTF confirmation
    df_1h = get_candles(symbol, "60", lookback_bars=100)
    if df_1h.empty:
        print("[WARN] No 1H price data — HTF confirmation disabled this cycle")
        df_1h = None

    # 3. Technical analysis (15min signal + 1H confirmation)
    trend = get_trend_signal(df_15m, df_1h)

    # 4. Fetch news + Claude sentiment
    articles  = get_news(keywords, lookback_hours=TRADE_CONFIG["news_lookback_hours"])
    sentiment = get_combined_sentiment(articles)

    # 5. Generate signal
    signal = generate_signal(trend, sentiment)

    # 6. Execute on OANDA demo
    execution = submit_order(signal)

    # 7. Log everything
    log_decision(trend, sentiment, signal, execution)
    print_decision(trend, sentiment, signal, execution)


def main():
    validate_keys()

    print("\n🏅 Gold AI Trading Bot — Demo Mode")
    print(f"   Asset:     {ASSET_CONFIG['name']} ({ASSET_CONFIG['oanda_instrument']})")
    print(f"   Timeframe: {TRADE_CONFIG['timeframe']}min + 1H HTF confirmation")
    print(f"   ADX min:   {TRADE_CONFIG['adx_threshold']}")
    print(f"   EMA:       {TRADE_CONFIG['ema_fast']}/{TRADE_CONFIG['ema_slow']}")
    print(f"   TP/SL:     {TRADE_CONFIG['take_profit_pct']*100}% / {TRADE_CONFIG['stop_loss_pct']*100}%")
    print(f"   Session:   07:00-17:00 UTC only")
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
