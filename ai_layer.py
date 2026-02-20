"""
ai_layer.py - Uses Claude to analyze news sentiment for gold trading.
No dependency on Finnhub sentiment scores (paid tier).
Claude reads the actual headlines and makes the call.
"""

import anthropic
from config import ANTHROPIC_API_KEY, ASSET_CONFIG


client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def analyze_news_with_claude(articles: list, asset_name: str = "Gold") -> dict:
    """
    Send news articles to Claude for sentiment analysis.
    Returns direction, confidence, and reasoning.
    """
    if not articles:
        return {
            "sentiment":  "neutral",
            "confidence": 0.0,
            "reasoning":  "No relevant articles found"
        }

    news_text = "\n\n".join([
        f"Headline: {a['headline']}\nSummary: {a['summary']}"
        for a in articles[:5]  # cap at 5 to keep tokens low
    ])

    prompt = f"""You are a financial analyst specializing in {asset_name} (XAU/USD) trading.

Analyze these recent news headlines and determine their short-term impact on {asset_name} price.

{news_text}

Respond in exactly this format:
SENTIMENT: [BULLISH or BEARISH or NEUTRAL]
CONFIDENCE: [0.0 to 1.0]
REASONING: [one sentence max]

Only respond with those three lines, nothing else."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=150,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.content[0].text.strip()

    result = {"sentiment": "neutral", "confidence": 0.0, "reasoning": raw}
    for line in raw.split("\n"):
        if line.startswith("SENTIMENT:"):
            result["sentiment"] = line.split(":", 1)[1].strip().lower()
        elif line.startswith("CONFIDENCE:"):
            try:
                result["confidence"] = float(line.split(":", 1)[1].strip())
            except ValueError:
                pass
        elif line.startswith("REASONING:"):
            result["reasoning"] = line.split(":", 1)[1].strip()

    return result


def get_combined_sentiment(articles: list) -> dict:
    """
    Gets sentiment purely from Claude analyzing the news articles.
    Falls back to neutral if no articles or Claude fails.
    """
    if not articles:
        return {
            "direction":  "neutral",
            "confidence": 0.0,
            "reasoning":  "No news articles available",
            "source":     "default",
        }

    print(f"[AI] Analyzing {len(articles)} articles with Claude...")
    result = analyze_news_with_claude(articles, ASSET_CONFIG["name"])

    return {
        "direction":  result["sentiment"],
        "confidence": result["confidence"],
        "reasoning":  result["reasoning"],
        "source":     "claude",
    }
