"""
data.py - Fetches price data and news from Finnhub
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
import time
from config import FINNHUB_API_KEY, ASSET_CONFIG, TRADE_CONFIG, SENTIMENT_CONFIG


BASE_URL = "https://finnhub.io/api/v1"


def get_candles(symbol: str, resolution: str, lookback_bars: int = 100) -> pd.DataFrame:
    """
    Fetch OHLCV candles from Finnhub.
    resolution: "1", "5", "15", "30", "60", "D"
    """
    to_ts = int(time.time())
    from_ts = to_ts - (lookback_bars * int(resolution) * 60)

    url = f"{BASE_URL}/forex/candle"
    params = {
        "symbol": symbol,
        "resolution": resolution,
        "from": from_ts,
        "to": to_ts,
        "token": FINNHUB_API_KEY
    }

    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    if data.get("s") != "ok" or not data.get("c"):
        print(f"[DATA] No candle data returned for {symbol}")
        return pd.DataFrame()

    df = pd.DataFrame({
        "timestamp": pd.to_datetime(data["t"], unit="s"),
        "open":  data["o"],
        "high":  data["h"],
        "low":   data["l"],
        "close": data["c"],
        "volume": data["v"],
    })
    df.set_index("timestamp", inplace=True)
    return df


def get_news(keywords: list, lookback_hours: int = 2) -> list:
    """
    Fetch recent general market news and filter by keywords.
    Returns list of dicts with title, summary, sentiment, datetime.
    """
    url = f"{BASE_URL}/news"
    params = {
        "category": "general",
        "token": FINNHUB_API_KEY
    }

    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    articles = resp.json()

    cutoff = datetime.utcnow() - timedelta(hours=lookback_hours)
    filtered = []

    for article in articles:
        pub_time = datetime.utcfromtimestamp(article.get("datetime", 0))
        if pub_time < cutoff:
            continue

        text = (article.get("headline", "") + " " + article.get("summary", "")).lower()
        if any(kw.lower() in text for kw in keywords):
            filtered.append({
                "headline": article.get("headline", ""),
                "summary":  article.get("summary", ""),
                "url":      article.get("url", ""),
                "datetime": pub_time,
                "source":   article.get("source", ""),
            })

    return filtered


def get_forex_sentiment(symbol: str = "XAUUSD") -> dict:
    """
    Fetch Finnhub's built-in sentiment for a symbol.
    Returns buzz and sentiment scores.
    """
    url = f"{BASE_URL}/news-sentiment"
    params = {
        "symbol": symbol,
        "token": FINNHUB_API_KEY
    }

    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    sentiment_score = data.get("sentiment", {}).get("bullishPercent", 0.5) - 0.5
    buzz_score = data.get("buzz", {}).get("buzz", 0)

    return {
        "sentiment_score": round(sentiment_score, 3),
        "buzz": buzz_score,
        "articles_in_week": data.get("buzz", {}).get("weeklyAverage", 0),
    }
