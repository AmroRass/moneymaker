# Gold AI Trading Bot

Trend-following bot for Gold (XAU/USD) that combines technical analysis with AI-powered news sentiment.

## Architecture

```
Finnhub (price + news) → Technical Analysis (EMA + ADX)
                       → Sentiment (Finnhub score + Claude deep analysis)
                       → Signal Engine
                       → Alpaca Paper Trading
                       → CSV Log
```

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Get your API keys

| Service   | URL                                      | Cost        |
|-----------|------------------------------------------|-------------|
| Finnhub   | https://finnhub.io                       | Free tier   |
| Anthropic | https://console.anthropic.com            | ~pennies/day|
| OANDA     | https://www.oanda.com/forex-trading/     | Free demo   |

**OANDA setup (2 min):**
1. Create a free demo account at oanda.com
2. Log into the portal → **Tools → API → Generate token**
3. Your Account ID is shown as `101-XXX-XXXXXXX-XXX` under Accounts

### 3. Fill in config.py
```python
FINNHUB_API_KEY    = "your_key"
ANTHROPIC_API_KEY  = "your_key"
OANDA_ACCESS_TOKEN = "your_token"
OANDA_ACCOUNT_ID   = "101-XXX-XXXXXXX-XXX"
OANDA_ENVIRONMENT  = "practice"   # keep this as "practice" for demo!
```

### 4. Run
```bash
python main.py
```

## Output

Every cycle prints to console:
```
============================================================
[14:32:01] Gold @ 2345.67
  TECH:      BULLISH | ADX=28.4 | confirmed=True
  SENTIMENT: BULLISH | source=finnhub | score=0.31
  SIGNAL:    BUY (strong) → Both agree: tech=bullish, sentiment=bullish
  TP=2354.99 | SL=2338.63
  EXECUTION: submitted
============================================================
```

All decisions are logged to `trade_log.csv` for backtesting and analysis.

## Swap Assets

To trade a different instrument, just change `ASSET_CONFIG` in `config.py`:

```python
# Example: S&P 500 ETF
ASSET_CONFIG = {
    "name": "S&P 500",
    "finnhub_symbol": "OANDA:SPX500_USD",
    "alpaca_symbol": "SPY",
    "news_keywords": ["fed", "interest rate", "inflation", "recession", "sp500", "stocks"],
    "description": "S&P 500 Index"
}
```

## Files

| File            | Purpose                                      |
|-----------------|----------------------------------------------|
| config.py       | All settings and API keys                    |
| main.py         | Main loop                                    |
| data.py         | Finnhub price + news fetcher                 |
| technicals.py   | EMA crossover + ADX trend detection          |
| ai_layer.py     | Claude sentiment analysis                    |
| signal.py       | Combines signals into trade decision         |
| execution.py    | Alpaca paper trading execution               |
| logger.py       | CSV logging + console output                 |

## Strategy Logic

1. Fetch 100 bars of 15min candles
2. Compute EMA(9) and EMA(21) crossover for trend direction
3. Compute ADX(14) — only trade if ADX > 20 (trend confirmed)
4. Fetch recent news filtered by gold-relevant keywords
5. Get Finnhub's built-in sentiment score
6. If news buzz is high → send to Claude for deeper analysis
7. Combine technical + sentiment → signal
8. In risky mode: trade even on conflicts (logs disagreements for analysis)
9. Fixed take profit (0.4%) and stop loss (0.3%)
10. Never stack positions — one trade at a time
