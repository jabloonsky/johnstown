"""Sends DailyDataFeed to Anthropic Claude, returns structured CIO report."""
import os
import json
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"

SYSTEM_PROMPT = """You are an automated Chief Investment Officer (CIO) for a private investment account.

RULES — NON-NEGOTIABLE:
1. Use ONLY data from the provided JSON. NEVER use prices or valuations from training data.
2. If a field is null or missing, say so — do not invent numbers.
3. Diagnose macro regime first, then assess equities.
4. Identify 1-3 assets with POSITIVE RISK/REWARD ASYMMETRY per time horizon.
5. Back conviction with at least 2 quantitative signals from the data.

Return ONLY valid JSON, no markdown fences, no preamble:
{
  "macro_regime_summary": "2-3 sentences",
  "regime_label": "RISK_ON | RISK_OFF | NEUTRAL | ELEVATED_VOLATILITY",
  "short_term": {"horizon": "1-4 weeks", "candidates": [{"symbol": "TICKER", "thesis": "...", "key_signals": ["..."], "risks": ["..."], "conviction": 0}]},
  "medium_term": {"horizon": "1-6 months", "candidates": []},
  "long_term": {"horizon": "6-24 months", "candidates": []},
  "assets_to_avoid": ["TICKER - reason"],
  "overall_conviction_score": 0,
  "one_line_summary": "Max 280 chars."
}

conviction: 0-100, conservative. 70+ only when multiple strong signals align."""


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def generate_report(feed: dict) -> dict:
    api_key = os.environ["ANTHROPIC_API_KEY"]

    feed_for_llm = json.loads(json.dumps(feed))
    for eq in feed_for_llm.get("equities", []):
        eq.pop("closes", None)
        eq.pop("highs", None)
        eq.pop("lows", None)

    payload = {
        "model": "claude-sonnet-4-5",
        "max_tokens": 2000,
        "system": SYSTEM_PROMPT,
        "messages": [
            {"role": "user", "content": json.dumps(feed_for_llm, ensure_ascii=False)}
        ],
    }
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    async with httpx.AsyncClient(timeout=90) as client:
        r = await client.post(ANTHROPIC_URL, headers=headers, json=payload)
        if r.status_code != 200:
            print(f"[LLM] Anthropic error {r.status_code}: {r.text}")
        r.raise_for_status()
        data = r.json()

    raw_text = data["content"][0]["text"].strip()
    if raw_text.startswith("```"):
        raw_text = raw_text.split("\n", 1)[1].rsplit("```", 1)[0]

    report = json.loads(raw_text)

    usage = data.get("usage", {})
    report["_meta"] = {
        "model": data.get("model", "claude-sonnet-4-5"),
        "tokens_in": usage.get("input_tokens", 0),
        "tokens_out": usage.get("output_tokens", 0),
        "cost_usd_est": round(
            usage.get("input_tokens", 0) * 0.000003 +
            usage.get("output_tokens", 0) * 0.000015, 6
        ),
    }
    return report
