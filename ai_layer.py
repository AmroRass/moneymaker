"""
ai_layer.py - Uses Claude to analyze news sentiment for gold trading.

Fixes:
  - Uses claude-haiku (cheapest model, ~20x cheaper than sonnet)
  - Caches results based on article headlines
  - Only calls Claude when NEW articles appear since last check
  - Falls back to neutral if Claude unavailable (no credits = no crash)
"""

import anthropic
import hashlib
from config import ANTHROPIC_API_KEY, ASSET_CONFIG

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# Cache: stores last sentiment result and the hash of articles that produced it
_cache = {
    "articles_hash": None,
    "result": None,
}


def _hash_articles(articles: list) -> str:
    """Create a hash of article headlines to detect new articles."""
    headlines = "".join([a.get("headline", "") for a in articles[:5]])
    return hashlib.md5(headlines.encode()).hexdigest()


def analyze_news_with_claude(articles: list, asset_name: str = "Gold") -> dict:
    """
    Send news articles to Claude for sentiment analysis.
    Uses Haiku model — cheapest, fast, good enough for this task.
    """
    if not articles:
        return {
            "sentiment":  "neutral",
            "confidence": 0.0,
            "reasoning":  "No relevant articles found"
        }

    news_text = "\n\n".join([
        f"Headline: {a['headline']}\nSummary: {a['summary']}"
        for a in articles[:5]
    ])

    prompt = f"""You are a financial analyst specializing in {asset_name} (XAU/USD) trading.

Analyze these recent news headlines and determine their short-term impact on {asset_name} price.

{news_text}

Respond in exactly this format:
SENTIMENT: [BULLISH or BEARISH or NEUTRAL]
CONFIDENCE: [0.0 to 1.0]
REASONING: [one sentence max]

Only respond with those three lines, nothing else."""

    try:
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
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

    except Exception as e:
        print(f"[AI] Claude API error: {e}")
        return {
            "sentiment":  "neutral",
            "confidence": 0.0,
            "reasoning":  f"Claude unavailable: {str(e)[:80]}"
        }


def get_combined_sentiment(articles: list) -> dict:
    """
    Gets sentiment from Claude — but only calls API when articles change.
    Caches the last result and reuses it if same articles seen again.
    Falls back to neutral if Claude fails — bot continues without crashing.
    """
    global _cache

    if not articles:
        return {
            "direction":  "neutral",
            "confidence": 0.0,
            "reasoning":  "No news articles available",
            "source":     "default",
        }

    # Check if articles have changed since last call
    current_hash = _hash_articles(articles)

    if current_hash == _cache["articles_hash"] and _cache["result"] is not None:
        # Same articles — reuse cached result, no API call
        cached = _cache["result"]
        print(f"[AI] Using cached sentiment: {cached['direction']} (no new articles)")
        return cached

    # New articles — call Claude
    print(f"[AI] New articles detected — calling Claude Haiku...")
    result = analyze_news_with_claude(articles, ASSET_CONFIG["name"])

    sentiment = {
        "direction":  result["sentiment"],
        "confidence": result["confidence"],
        "reasoning":  result["reasoning"],
        "source":     "claude",
    }

    # Cache the result
    _cache["articles_hash"] = current_hash
    _cache["result"] = sentiment

    return sentiment
