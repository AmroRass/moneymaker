"""
signal.py - Combines technical trend + sentiment into a trade signal
"""

from config import TRADE_CONFIG


def generate_signal(trend: dict, sentiment: dict) -> dict:
    """
    Combines trend and sentiment into a final trade signal.

    conflict_mode:
        "risky"        - trade even if signals conflict, log the conflict
        "conservative" - only trade when both agree
    """
    tech_direction  = trend.get("direction", "neutral")
    sent_direction  = sentiment.get("direction", "neutral")
    tech_confirmed  = trend.get("confirmed", False)
    conflict_mode   = TRADE_CONFIG["conflict_mode"]

    # Map directions to action
    def to_action(direction):
        if direction == "bullish": return "buy"
        if direction == "bearish": return "sell"
        return None

    tech_action = to_action(tech_direction)
    sent_action = to_action(sent_direction)

    # Both neutral = no trade
    if not tech_action and not sent_action:
        return _no_trade("Both signals neutral")

    # Technical trend not confirmed by ADX = weak signal
    if not tech_confirmed:
        return _no_trade(f"Trend not confirmed by ADX (strength={trend.get('strength', 0):.1f})")

    signals_agree = tech_action == sent_action

    if signals_agree:
        action = tech_action
        signal_type = "strong"
        reason = f"Both agree: tech={tech_direction}, sentiment={sent_direction}"
    else:
        # They conflict
        if conflict_mode == "risky":
            # Take the trade anyway, bias toward technicals
            action = tech_action or sent_action
            signal_type = "weak"
            reason = f"CONFLICT (risky mode): tech={tech_direction}, sentiment={sent_direction} → following tech"
        else:
            return _no_trade(f"Conflict: tech={tech_direction}, sentiment={sent_direction}")

    price = trend.get("close", 0)
    tp = round(price * (1 + TRADE_CONFIG["take_profit_pct"]) if action == "buy"
               else price * (1 - TRADE_CONFIG["take_profit_pct"]), 4)
    sl = round(price * (1 - TRADE_CONFIG["stop_loss_pct"]) if action == "buy"
               else price * (1 + TRADE_CONFIG["stop_loss_pct"]), 4)

    return {
        "action":      action,
        "signal_type": signal_type,
        "entry_price": price,
        "take_profit": tp,
        "stop_loss":   sl,
        "reason":      reason,
        "trade":       True,
    }


def _no_trade(reason: str) -> dict:
    return {
        "action":      None,
        "signal_type": "none",
        "entry_price": None,
        "take_profit": None,
        "stop_loss":   None,
        "reason":      reason,
        "trade":       False,
    }
