"""
Sends the DailyDataFeed JSON to Google Gemini and returns a structured CIO report.
Uses response_mime_type=application/json to enforce structured output.
"""
import os
import json
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

SYSTEM_PROMPT = """You are an automated Chief Investment Officer (CIO) for a private investment account.

YOUR RULES — NON-NEGOTIABLE:
1. You ONLY use data from the JSON provided. NEVER use valuations or prices from your training data.
2. If a field is null or missing, say so — do not invent a number.
3. Diagnose macro regime FIRST (top-down), then assess individual equities.
4. Identify 1-3 assets with POSITIVE RISK/REWARD ASYMMETRY per time horizon.
5. Conviction must be backed by at least 2 quantitative signals from the data.

OUTPUT FORMAT — return valid JSON only, no markdown, no preamble:
{
  "macro_regime_summary": "2-3 sentence diagnosis of current macro environment",
  "regime_label": "RISK_ON | RISK_OFF | NEUTRAL | ELEVATED_VOLATILITY",
  "short_term": {
    "horizon": "1-4 weeks",
    "candidates": [
      {
        "symbol": "TICKER",
        "thesis": "Why this asset, backed by specific signals from the data",
        "key_signals": ["signal1", "signal2"],
        "risks": ["risk1"],
        "conviction": 0
      }
    ]
  },
  "medium_term": { "horizon": "1-6 months", "candidates": [] },
  "long_term":   { "horizon": "6-24 months", "candidates": [] },
  "assets_to_avoid": ["TICKER - reason"],
  "overall_conviction_score": 0,
  "one_line_summary": "Maximum 280 characters. Plain language."
}

conviction score: 0-100. Be conservative. 70+ only when multiple strong signals align.
If conditions suggest holding cash, say so explicitly."""


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def generate_report(feed: dict) -> dict:
    api_key = os.environ["GEMINI_API_KEY"]

    # Strip raw OHLCV arrays — LLM doesn't need them, signals already computed
    feed_for_llm = json.loads(json.dumps(feed))
    for eq in feed_for_llm.get("equities", []):
        eq.pop("closes", None)
        eq.pop("highs", None)
        eq.pop("lows", None)

    prompt = f"{SYSTEM_PROMPT}\n\nDATA:\n{json.dumps(feed_for_llm, ensure_ascii=False)}"

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature":      0.2,
            "maxOutputTokens":  2000,
            "responseMimeType": "application/json",   # Forces JSON output
        },
    }

    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            GEMINI_URL,
            params={"key": api_key},
            json=payload,
        )
        r.raise_for_status()
        data = r.json()

    raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
    report   = json.loads(raw_text)

    # Attach usage metadata for cost tracking
    usage = data.get("usageMetadata", {})
    report["_meta"] = {
        "model":         "gemini-2.0-flash",
        "tokens_in":     usage.get("promptTokenCount", 0),
        "tokens_out":    usage.get("candidatesTokenCount", 0),
        # Gemini 2.0 Flash pricing: input $0.075/1M, output $0.30/1M tokens
        "cost_usd_est":  round(
            usage.get("promptTokenCount", 0)     * 0.000000075 +
            usage.get("candidatesTokenCount", 0) * 0.0000003,
            6
        ),
    }
    return report
