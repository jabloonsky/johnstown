"""
Sends the DailyDataFeed JSON to OpenAI and returns a structured CIO report.
Uses response_format=json_object to prevent free-text hallucination.
"""
import os
import json
from openai import AsyncOpenAI

SYSTEM_PROMPT = """You are an automated Chief Investment Officer (CIO) for a private investment account.

YOUR RULES — NON-NEGOTIABLE:
1. You ONLY use data from the JSON provided. You NEVER use valuations, prices, or facts from your training data.
2. If a field is null or missing, say so — do not invent a number.
3. You diagnose macro regime FIRST (top-down), then assess individual equities.
4. You identify 1-3 assets with POSITIVE RISK/REWARD ASYMMETRY per time horizon.
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
  "medium_term": {
    "horizon": "1-6 months",
    "candidates": []
  },
  "long_term": {
    "horizon": "6-24 months",
    "candidates": []
  },
  "assets_to_avoid": ["TICKER - reason"],
  "overall_conviction_score": 0,
  "one_line_summary": "Maximum 280 characters. Plain language."
}

conviction score: 0-100. Be conservative. 70+ only when multiple strong signals align.
If market conditions suggest holding cash, say so explicitly with reasoning.
"""


async def generate_report(feed: dict) -> dict:
    client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])

    # Remove raw OHLCV arrays before sending — they are large and the LLM
    # doesn't need them (signals are already computed)
    feed_for_llm = json.loads(json.dumps(feed))
    for eq in feed_for_llm.get("equities", []):
        eq.pop("closes", None)
        eq.pop("highs", None)
        eq.pop("lows", None)

    response = await client.chat.completions.create(
        model="gpt-4o-mini",          # ~$0.001 per report; upgrade to gpt-4o when ready
        response_format={"type": "json_object"},
        temperature=0.2,              # low temperature = less creative, more factual
        max_tokens=2000,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": json.dumps(feed_for_llm, ensure_ascii=False)},
        ],
    )

    raw = response.choices[0].message.content
    report = json.loads(raw)

    # Attach token usage for cost tracking
    report["_meta"] = {
        "model":       response.model,
        "tokens_in":   response.usage.prompt_tokens,
        "tokens_out":  response.usage.completion_tokens,
        "cost_usd_est": round(
            response.usage.prompt_tokens * 0.00000015 +
            response.usage.completion_tokens * 0.0000006, 5
        ),
    }
    return report
