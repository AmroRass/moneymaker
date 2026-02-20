"""
logger.py - Logs every signal and trade decision to CSV for analysis
"""

import csv
import os
from datetime import datetime


LOG_FILE = "trade_log.csv"

HEADERS = [
    "timestamp",
    "price",
    "tech_direction",
    "tech_strength",
    "tech_confirmed",
    "sentiment_direction",
    "sentiment_source",
    "finnhub_score",
    "claude_sentiment",
    "claude_confidence",
    "signals_agree",
    "action",
    "signal_type",
    "take_profit",
    "stop_loss",
    "reason",
    "execution_status",
]


def init_log():
    """Create log file with headers if it doesn't exist."""
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=HEADERS)
            writer.writeheader()
        print(f"[LOG] Created {LOG_FILE}")


def log_decision(trend: dict, sentiment: dict, signal: dict, execution: dict):
    """Log a full decision cycle to CSV."""
    claude = sentiment.get("claude_result") or {}
    signals_agree = trend.get("direction") == sentiment.get("direction")

    row = {
        "timestamp":            datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "price":                trend.get("close", ""),
        "tech_direction":       trend.get("direction", ""),
        "tech_strength":        trend.get("strength", ""),
        "tech_confirmed":       trend.get("confirmed", ""),
        "sentiment_direction":  sentiment.get("direction", ""),
        "sentiment_source":     sentiment.get("source", ""),
        "finnhub_score":        sentiment.get("finnhub_score", ""),
        "claude_sentiment":     claude.get("sentiment", ""),
        "claude_confidence":    claude.get("confidence", ""),
        "signals_agree":        signals_agree,
        "action":               signal.get("action", ""),
        "signal_type":          signal.get("signal_type", ""),
        "take_profit":          signal.get("take_profit", ""),
        "stop_loss":            signal.get("stop_loss", ""),
        "reason":               signal.get("reason", ""),
        "execution_status":     execution.get("status", ""),
    }

    with open(LOG_FILE, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=HEADERS)
        writer.writerow(row)


def print_decision(trend: dict, sentiment: dict, signal: dict, execution: dict):
    """Pretty print the current decision cycle to console."""
    print("\n" + "="*60)
    print(f"[{datetime.utcnow().strftime('%H:%M:%S')}] Gold @ {trend.get('close', '?')}")
    print(f"  TECH:      {trend.get('direction','?').upper()} | ADX={trend.get('strength','?')} | confirmed={trend.get('confirmed','?')}")
    print(f"  SENTIMENT: {sentiment.get('direction','?').upper()} | source={sentiment.get('source','?')} | score={sentiment.get('finnhub_score','?')}")
    if sentiment.get("claude_result"):
        c = sentiment["claude_result"]
        print(f"  CLAUDE:    {c.get('sentiment','?').upper()} | confidence={c.get('confidence','?')} | {c.get('reasoning','')}")
    print(f"  SIGNAL:    {signal.get('action','NO TRADE').upper()} ({signal.get('signal_type','')}) → {signal.get('reason','')}")
    if signal.get("trade"):
        print(f"  TP={signal.get('take_profit')} | SL={signal.get('stop_loss')}")
    print(f"  EXECUTION: {execution.get('status','')}")
    print("="*60)
