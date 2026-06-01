"""
Fetches sentiment indicators.
- CNN Fear & Greed (unofficial endpoint, cached on failure)
- alternative.me crypto F&G (official, stable)
"""
import httpx
from datetime import datetime, timedelta
from tenacity import retry, stop_after_attempt, wait_exponential


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
async def fetch_cnn_fng() -> dict:
    """
    Uses CNN's internal dataviz endpoint.
    Requires a real browser User-Agent or CNN returns 403.
    """
    start = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
    url = f"https://production.dataviz.cnn.io/index/fearandgreed/graphdata/{start}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Referer": "https://www.cnn.com/",
    }
    async with httpx.AsyncClient(timeout=15, headers=headers) as client:
        r = await client.get(url)
        r.raise_for_status()
        data = r.json()["fear_and_greed"]
        return {
            "v":     round(float(data["score"]), 1),
            "label": data["rating"],
            "prev_close": data.get("previous_close"),
            "src":   "CNN",
        }


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
async def fetch_crypto_fng() -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get("https://api.alternative.me/fng/?limit=1")
        r.raise_for_status()
        d = r.json()["data"][0]
        return {
            "v":     int(d["value"]),
            "label": d["value_classification"],
            "src":   "alternative.me",
        }


async def fetch_sentiment() -> dict:
    result = {}

    try:
        result["stock_fng"] = await fetch_cnn_fng()
    except Exception as e:
        # Fallback: neutral value with error flag so LLM knows data is missing
        result["stock_fng"] = {"v": None, "label": "unavailable",
                               "error": str(e), "src": "CNN"}

    try:
        result["crypto_fng"] = await fetch_crypto_fng()
    except Exception as e:
        result["crypto_fng"] = {"v": None, "label": "unavailable",
                                "error": str(e), "src": "alternative.me"}

    return result
