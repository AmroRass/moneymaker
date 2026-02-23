"""
daily_summary.py - Sends a daily trading summary to Telegram via Claude.

Run via cron at 17:00 UTC (session close):
  0 17 * * 1-5 cd /home/ec2-user/moneymaker && python3 daily_summary.py

Claude reads today's trades, identifies patterns, and suggests improvements.
"""

import os
import csv
import anthropic
from datetime import datetime, timezone, date
from telegram_alerts import send_message
from config import ANTHROPIC_API_KEY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def load_todays_trades(filepath="trade_log.csv") -> list:
    """Load only today's trades from the log."""
    today = date.today().isoformat()
    trades = []

    if not os.path.exists(filepath):
        return trades

    with open(filepath, "r") as f:
        reader = csv.reader(f)
        for row in reader:
            if row and row[0].startswith(today):
                trades.append(row)

    return trades


def parse_trades(trades: list) -> dict:
    """Extract stats from today's trade rows."""
    executed = [t for t in trades if len(t) > 5 and t[5] not in ("skipped", "none", "")]

    wins = 0
    losses = 0
    sentiment_agreed_wins = 0
    sentiment_agreed_losses = 0
    sentiment_disagreed_wins = 0
    sentiment_disagreed_losses = 0
    reasoning_list = []

    for t in executed:
        try:
            result = t[-1] if t else ""
            sentiment_agreed = t[4] if len(t) > 4 else "False"
            reasoning = t[3] if len(t) > 3 else ""

            is_win = "tp" in result.lower()
            is_loss = "sl" in result.lower()
            agreed = sentiment_agreed.lower() == "true"

            if is_win:
                wins += 1
                if agreed:
                    sentiment_agreed_wins += 1
                else:
                    sentiment_disagreed_wins += 1
            elif is_loss:
                losses += 1
                if agreed:
                    sentiment_agreed_losses += 1
                else:
                    sentiment_disagreed_losses += 1

            if reasoning:
                reasoning_list.append(reasoning)

        except Exception:
            continue

    return {
        "total_trades": len(executed),
        "wins": wins,
        "losses": losses,
        "sentiment_agreed_wins": sentiment_agreed_wins,
        "sentiment_agreed_losses": sentiment_agreed_losses,
        "sentiment_disagreed_wins": sentiment_disagreed_wins,
        "sentiment_disagreed_losses": sentiment_disagreed_losses,
        "reasoning_list": reasoning_list,
    }


def get_claude_analysis(stats: dict, raw_trades: list) -> str:
    """Ask Claude to analyse the day and suggest improvements."""

    trade_summary = f"""
Today's trading stats:
- Total trades: {stats['total_trades']}
- Wins: {stats['wins']} | Losses: {stats['losses']}
- Sentiment agreed + win: {stats['sentiment_agreed_wins']}
- Sentiment agreed + loss: {stats['sentiment_agreed_losses']}
- Sentiment disagreed + win: {stats['sentiment_disagreed_wins']}
- Sentiment disagreed + loss: {stats['sentiment_disagreed_losses']}

News reasoning seen today (sample):
{chr(10).join(stats['reasoning_list'][:5]) if stats['reasoning_list'] else 'No reasoning captured'}
"""

    prompt = f"""You are analysing the daily performance of a gold (XAU/USD) trading bot.

{trade_summary}

The bot uses EMA 9/50 crossover + ADX >= 25 + 1H HTF confirmation + Claude news sentiment.
TP is 0.4%, SL is 0.2%. Session is London/NY (07:00-17:00 UTC).

In 3-5 sentences maximum:
1. What was the dominant news theme today?
2. Did sentiment agreement improve results? (compare agreed vs disagreed win rates)
3. One concrete observation or potential improvement based on today's data.

Be specific and brutal. If there's nothing useful to say, say so."""

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text.strip()
    except Exception as e:
        return f"Claude analysis unavailable: {str(e)[:80]}"


def send_daily_summary():
    today = date.today().strftime("%b %d, %Y")
    trades = load_todays_trades()
    stats = parse_trades(trades)

    if stats["total_trades"] == 0:
        send_message(
            f"📊 <b>Daily Summary — {today}</b>\n"
            f"No trades executed today.\n"
            f"Bot was running but conditions never aligned (ADX, session, HTF)."
        )
        return

    total = stats["total_trades"]
    wins = stats["wins"]
    losses = stats["losses"]
    win_rate = (wins / total * 100) if total > 0 else 0

    agreed_total = stats["sentiment_agreed_wins"] + stats["sentiment_agreed_losses"]
    agreed_wr = (stats["sentiment_agreed_wins"] / agreed_total * 100) if agreed_total > 0 else 0

    disagreed_total = stats["sentiment_disagreed_wins"] + stats["sentiment_disagreed_losses"]
    disagreed_wr = (stats["sentiment_disagreed_wins"] / disagreed_total * 100) if disagreed_total > 0 else 0

    analysis = get_claude_analysis(stats, trades)

    msg = (
        f"📊 <b>Daily Summary — {today}</b>\n\n"
        f"Trades: {total}  |  W: {wins}  L: {losses}  |  WR: {win_rate:.0f}%\n\n"
        f"<b>Sentiment Impact:</b>\n"
        f"  Agreed:    {agreed_total} trades → {agreed_wr:.0f}% win rate\n"
        f"  Disagreed: {disagreed_total} trades → {disagreed_wr:.0f}% win rate\n\n"
        f"<b>Claude Analysis:</b>\n{analysis}"
    )

    send_message(msg)
    print(f"[SUMMARY] Sent daily summary for {today}")


if __name__ == "__main__":
    send_daily_summary()
