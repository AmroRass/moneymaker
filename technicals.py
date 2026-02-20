"""
technicals.py - Computes trend signals from price data
"""

import pandas as pd
import numpy as np
from config import TRADE_CONFIG


def compute_ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def compute_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Compute ADX (trend strength indicator)."""
    high = df["high"]
    low  = df["low"]
    close = df["close"]

    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low  - close.shift()).abs()
    ], axis=1).max(axis=1)

    dm_plus  = ((high - high.shift()) > (low.shift() - low)).astype(float) * (high - high.shift()).clip(lower=0)
    dm_minus = ((low.shift() - low) > (high - high.shift())).astype(float) * (low.shift() - low).clip(lower=0)

    atr     = tr.ewm(span=period, adjust=False).mean()
    di_plus  = 100 * dm_plus.ewm(span=period,  adjust=False).mean() / atr
    di_minus = 100 * dm_minus.ewm(span=period, adjust=False).mean() / atr

    dx = (100 * (di_plus - di_minus).abs() / (di_plus + di_minus).replace(0, np.nan)).fillna(0)
    adx = dx.ewm(span=period, adjust=False).mean()
    return adx


def get_trend_signal(df: pd.DataFrame) -> dict:
    """
    Returns trend direction and strength based on EMA crossover + ADX.

    Returns:
        direction: "bullish" | "bearish" | "neutral"
        strength:  ADX value (>20 = trend exists, >40 = strong trend)
        ema_fast:  latest fast EMA value
        ema_slow:  latest slow EMA value
        confirmed: bool - trend is strong enough to trade
    """
    if df.empty or len(df) < TRADE_CONFIG["ema_slow"] + 5:
        return {"direction": "neutral", "strength": 0, "confirmed": False}

    ema_fast = compute_ema(df["close"], TRADE_CONFIG["ema_fast"])
    ema_slow = compute_ema(df["close"], TRADE_CONFIG["ema_slow"])
    adx      = compute_adx(df, TRADE_CONFIG["adx_period"])

    latest_fast = ema_fast.iloc[-1]
    latest_slow = ema_slow.iloc[-1]
    latest_adx  = adx.iloc[-1]

    if latest_fast > latest_slow:
        direction = "bullish"
    elif latest_fast < latest_slow:
        direction = "bearish"
    else:
        direction = "neutral"

    confirmed = latest_adx >= TRADE_CONFIG["adx_threshold"] and direction != "neutral"

    return {
        "direction":  direction,
        "strength":   round(latest_adx, 2),
        "ema_fast":   round(latest_fast, 4),
        "ema_slow":   round(latest_slow, 4),
        "confirmed":  confirmed,
        "close":      round(df["close"].iloc[-1], 4),
    }
