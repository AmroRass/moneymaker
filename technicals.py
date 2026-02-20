"""
technicals.py - Computes trend signals from price data.
Now includes HTF (1H) confirmation filter.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timezone
from config import TRADE_CONFIG


def compute_ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def compute_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Compute ADX (trend strength indicator)."""
    high  = df["high"]
    low   = df["low"]
    close = df["close"]

    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low  - close.shift()).abs()
    ], axis=1).max(axis=1)

    dm_plus  = ((high - high.shift()) > (low.shift() - low)).astype(float) * (high - high.shift()).clip(lower=0)
    dm_minus = ((low.shift() - low) > (high - high.shift())).astype(float) * (low.shift() - low).clip(lower=0)

    atr      = tr.ewm(span=period, adjust=False).mean()
    di_plus  = 100 * dm_plus.ewm(span=period,  adjust=False).mean() / atr
    di_minus = 100 * dm_minus.ewm(span=period, adjust=False).mean() / atr

    dx  = (100 * (di_plus - di_minus).abs() / (di_plus + di_minus).replace(0, np.nan)).fillna(0)
    adx = dx.ewm(span=period, adjust=False).mean()
    return adx


def get_htf_direction(df_1h: pd.DataFrame) -> str:
    """
    Checks 1H chart trend direction using EMA50.
    Returns 'bullish', 'bearish', or 'unknown'.
    """
    if df_1h is None or df_1h.empty or len(df_1h) < 55:
        return "unknown"

    ema50 = compute_ema(df_1h["close"], 50)
    latest_close = df_1h["close"].iloc[-1]
    latest_ema   = ema50.iloc[-1]

    if latest_close > latest_ema:
        return "bullish"
    elif latest_close < latest_ema:
        return "bearish"
    return "unknown"


def is_trading_session() -> bool:
    """Returns True if current UTC time is within London/NY session (7am-5pm UTC)."""
    from config import SESSION_CONFIG
    if not SESSION_CONFIG["enabled"]:
        return True
    hour = datetime.now(timezone.utc).hour
    return SESSION_CONFIG["start_hour_utc"] <= hour < SESSION_CONFIG["end_hour_utc"]


def get_trend_signal(df: pd.DataFrame, df_1h: pd.DataFrame = None) -> dict:
    """
    Returns trend direction and strength based on EMA crossover + ADX.
    If HTF confirmation is enabled, also checks 1H EMA50 alignment.

    Returns:
        direction:    "bullish" | "bearish" | "neutral"
        strength:     ADX value
        confirmed:    bool - trend strong enough AND session active AND HTF agrees
        htf_direction: direction of 1H chart
        htf_agrees:   bool - whether 1H agrees with 15min signal
        in_session:   bool - whether we're in trading hours
    """
    if df.empty or len(df) < TRADE_CONFIG["ema_slow"] + 5:
        return {
            "direction": "neutral", "strength": 0, "confirmed": False,
            "htf_direction": "unknown", "htf_agrees": False, "in_session": False
        }

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

    # Session filter
    in_session = is_trading_session()

    # HTF confirmation
    htf_direction = get_htf_direction(df_1h)
    if TRADE_CONFIG.get("htf_confirmation", False) and htf_direction != "unknown":
        htf_agrees = htf_direction == direction
    else:
        htf_agrees = True  # If HTF disabled or unknown, don't block

    # All conditions must pass
    adx_ok    = latest_adx >= TRADE_CONFIG["adx_threshold"]
    confirmed = adx_ok and direction != "neutral" and in_session and htf_agrees

    return {
        "direction":     direction,
        "strength":      round(latest_adx, 2),
        "ema_fast":      round(latest_fast, 4),
        "ema_slow":      round(latest_slow, 4),
        "confirmed":     confirmed,
        "htf_direction": htf_direction,
        "htf_agrees":    htf_agrees,
        "in_session":    in_session,
        "close":         round(df["close"].iloc[-1], 4),
    }
