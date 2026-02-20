"""
ai_layer.py - Uses Claude to analyze high-impact news for deeper sentiment
Only called when Finnhub flags something as high impact, to keep API costs low.
"""

import anthropic
from config import ANTHROPIC_API_KEY, ASSET_CONFIG


client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def analyze_news_with_claude(articles: list, asset_name: str = "Gold") -> dict:
    """
    Send high-impact news articles to Claude for deeper analysis.
    Returns sentiment direction and confidence.
    """
    if not articles:
        return {"sentiment": "neutral", "confidence": 0.0, "reasoning": "No articles to analyze"}

    # Build the news digest
    news_text = "\n\n".join([
        f"Headline: {a['headline']}\nSummary: {a['summary']}\nTime: {a['datetime']}"
        for a in articles[:5]  # cap at 5 articles to keep tokens low
    ])

    prompt = f"""You are a financial analyst specializing in {asset_name} trading.

Analyze the following recent news articles and determine their impact on {asset_name} price direction.

{news_text}

Respond in this exact format:
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

    # Parse the structured response
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


def get_combined_sentiment(finnhub_score: float, articles: list, buzz: float) -> dict:
    """
    Combines Finnhub's built-in sentiment with Claude's deeper analysis.
    Only calls Claude if there are high-buzz articles worth analyzing.
    """
    from config import SENTIMENT_CONFIG

    # Start with Finnhub sentiment
    if finnhub_score > SENTIMENT_CONFIG["bullish_threshold"]:
        finnhub_direction = "bullish"
    elif finnhub_score < SENTIMENT_CONFIG["bearish_threshold"]:
        finnhub_direction = "bearish"
    else:
        finnhub_direction = "neutral"

    # Only call Claude if buzz is high enough to justify it
    claude_result = None
    if articles and buzz >= SENTIMENT_CONFIG["high_impact_score"]:
        print(f"[AI] High buzz detected ({buzz:.2f}), calling Claude for deeper analysis...")
        claude_result = analyze_news_with_claude(articles, ASSET_CONFIG["name"])

    # Combine signals
    if claude_result:
        # Claude overrides if confident
        if claude_result["confidence"] >= 0.7:
            final_direction = claude_result["sentiment"]
            source = "claude"
        else:
            # Low confidence - fall back to Finnhub
            final_direction = finnhub_direction
            source = "finnhub_fallback"
    else:
        final_direction = finnhub_direction
        source = "finnhub"

    return {
        "direction":       final_direction,
        "finnhub_score":   finnhub_score,
        "finnhub_direction": finnhub_direction,
        "claude_result":   claude_result,
        "source":          source,
    }
