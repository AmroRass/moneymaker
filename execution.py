"""
execution.py - Submits trades to OANDA demo account via direct REST calls.
Uses requests instead of oandapyV20 library to avoid URL routing issues.
"""

import requests
import json
from config import OANDA_ACCESS_TOKEN, OANDA_ACCOUNT_ID, TRADE_CONFIG, ASSET_CONFIG

BASE_URL = "https://api-fxpractice.oanda.com/v3"

HEADERS = {
    "Authorization": f"Bearer {OANDA_ACCESS_TOKEN}",
    "Content-Type":  "application/json",
}


def get_open_trades() -> list:
    resp = requests.get(
        f"{BASE_URL}/accounts/{OANDA_ACCOUNT_ID}/openTrades",
        headers=HEADERS,
        timeout=10
    )
    if resp.status_code == 200:
        return resp.json().get("trades", [])
    print(f"[EXEC] Error fetching trades: {resp.text}")
    return []


def has_open_position(instrument: str) -> bool:
    trades = get_open_trades()
    return any(t.get("instrument") == instrument for t in trades)


def submit_order(signal: dict) -> dict:
    instrument = ASSET_CONFIG["oanda_instrument"]

    if not signal.get("trade"):
        return {"status": "skipped", "reason": signal.get("reason")}

    if has_open_position(instrument):
        return {"status": "skipped", "reason": "Position already open"}

    units = TRADE_CONFIG["oanda_units"]
    if signal["action"] == "sell":
        units = -abs(units)
    else:
        units = abs(units)

    tp = str(round(signal["take_profit"], 2))
    sl = str(round(signal["stop_loss"], 2))

    order = {
        "order": {
            "type":         "MARKET",
            "instrument":   instrument,
            "units":        str(units),
            "timeInForce":  "FOK",
            "takeProfitOnFill": {"price": tp},
            "stopLossOnFill":   {"price": sl},
        }
    }

    resp = requests.post(
        f"{BASE_URL}/accounts/{OANDA_ACCOUNT_ID}/orders",
        headers=HEADERS,
        data=json.dumps(order),
        timeout=10
    )

    if resp.status_code in (200, 201):
        data = resp.json()
        fill = data.get("orderFillTransaction", {})
        return {
            "status":     "submitted",
            "order_id":   fill.get("id", "?"),
            "instrument": instrument,
            "side":       signal["action"],
            "units":      units,
            "fill_price": fill.get("price", "?"),
            "tp":         tp,
            "sl":         sl,
        }
    else:
        return {
            "status": "error",
            "code":   resp.status_code,
            "body":   resp.text,
        }


def close_all_positions(instrument: str) -> dict:
    data = {"longUnits": "ALL", "shortUnits": "ALL"}
    resp = requests.put(
        f"{BASE_URL}/accounts/{OANDA_ACCOUNT_ID}/positions/{instrument}/close",
        headers=HEADERS,
        data=json.dumps(data),
        timeout=10
    )
    if resp.status_code == 200:
        return {"status": "closed", "instrument": instrument}
    return {"status": "error", "body": resp.text}
