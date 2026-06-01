"""
Main pipeline orchestrator.
Runs every weekday at 06:00 Polish time via GitHub Actions cron.

Sequence:
  1. Fetch macro (FRED)
  2. Fetch sentiment (CNN F&G + alternative.me)
  3. Fetch equity data (FMP) for watchlist symbols
  4. Run math filters (Sortino, Squeeze, Graham, Momentum, EMA, RSI, R/R)
  5. Build DailyDataFeed JSON
  6. Send to OpenAI → get CIO report
  7. Render HTML
  8. Write to output/ (GitHub Actions deploys to GitHub Pages)
  9. Send Discord notification
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx
from jinja2 import Environment, FileSystemLoader

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from fetchers.fred      import fetch_macro
from fetchers.fmp       import fetch_all_equities
from fetchers.sentiment import fetch_sentiment
from analytics.filters  import screen_equity
from llm.client         import generate_report


# ── Configuration ────────────────────────────────────────────────────────────
# Phase 0: 5 symbols. Add more in Phase 1.
WATCHLIST = ["SPY", "QQQ", "NVDA", "MSFT", "XOM"]

OUTPUT_DIR   = Path(__file__).parent.parent / "output"
TEMPLATE_DIR = Path(__file__).parent.parent / "templates"


# ── Discord notification ──────────────────────────────────────────────────────
async def notify_discord(message: str, success: bool = True):
    webhook = os.environ.get("DISCORD_WEBHOOK")
    if not webhook:
        return
    color   = 0x4ade80 if success else 0xf87171
    payload = {"embeds": [{"description": message, "color": color}]}
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            await client.post(webhook, json=payload)
        except Exception:
            pass   # Discord failure must never crash the pipeline


# ── HTML index generator ──────────────────────────────────────────────────────
def regenerate_index(output_dir: Path):
    """Scans output/ and writes index.html listing all past reports."""
    reports = sorted(output_dir.glob("report_*.html"), reverse=True)
    rows = ""
    for p in reports:
        date = p.stem.replace("report_", "")
        rows += f'<li><a href="{p.name}">{date}</a></li>\n'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>CIO Reports Archive</title>
  <style>
    body {{ font-family: -apple-system, sans-serif; background:#0f0f0f;
           color:#e8e8e8; max-width:600px; margin:3rem auto; padding:0 1.5rem; }}
    h1   {{ font-size:1.3rem; margin-bottom:1.5rem; color:#fff; }}
    ul   {{ list-style:none; padding:0; }}
    li   {{ padding:0.6rem 0; border-bottom:1px solid #1e1e1e; }}
    a    {{ color:#93c5fd; text-decoration:none; }}
    a:hover {{ text-decoration:underline; }}
  </style>
</head>
<body>
  <h1>CIO Daily Reports</h1>
  <ul>{rows}</ul>
</body>
</html>"""
    (output_dir / "index.html").write_text(html, encoding="utf-8")


# ── Main pipeline ─────────────────────────────────────────────────────────────
async def run():
    now       = datetime.now(timezone.utc)
    date_str  = now.strftime("%Y-%m-%d")
    ts_str    = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    log       = {"run_date": date_str, "steps": {}}

    OUTPUT_DIR.mkdir(exist_ok=True)

    print(f"[CIO] Starting pipeline for {date_str}")

    # ── Step 1: Macro ─────────────────────────────────────────────────────────
    print("[CIO] Fetching macro data (FRED)...")
    try:
        macro = await fetch_macro()
        log["steps"]["macro"] = "ok"
    except Exception as e:
        macro = {}
        log["steps"]["macro"] = f"ERROR: {e}"
        print(f"[CIO] Macro fetch failed: {e}")

    # ── Step 2: Sentiment ─────────────────────────────────────────────────────
    print("[CIO] Fetching sentiment (F&G)...")
    try:
        sentiment = await fetch_sentiment()
        log["steps"]["sentiment"] = "ok"
    except Exception as e:
        sentiment = {}
        log["steps"]["sentiment"] = f"ERROR: {e}"

    # ── Step 3: Equity data ───────────────────────────────────────────────────
    print(f"[CIO] Fetching equity data for: {WATCHLIST}")
    try:
        raw_equities = await fetch_all_equities(WATCHLIST)
        log["steps"]["equities"] = f"ok ({len(raw_equities)} symbols)"
    except Exception as e:
        raw_equities = []
        log["steps"]["equities"] = f"ERROR: {e}"

    # ── Step 4: Math filters ──────────────────────────────────────────────────
    print("[CIO] Running quantitative filters...")
    risk_free = float((macro.get("fed_funds_pct") or {}).get("v") or 4.5) / 100

    # Get SPY closes as benchmark for relative strength
    spy_closes = None
    for eq in raw_equities:
        if eq.get("symbol") == "SPY":
            spy_closes = eq.get("closes")
            break

    equities_with_signals = []
    for eq in raw_equities:
        if eq.get("closes"):
            signals = screen_equity(eq, risk_free, spy_closes)
            equities_with_signals.append({**eq, "signals": signals})
        else:
            equities_with_signals.append(eq)

    # ── Step 5: Build DailyDataFeed ───────────────────────────────────────────
    print("[CIO] Assembling DailyDataFeed JSON...")

    # Slim down equity objects for the feed (drop raw arrays, keep signals)
    equities_clean = []
    for eq in equities_with_signals:
        sig = eq.get("signals", {})
        entry = {
            "symbol":       eq.get("symbol"),
            "px":           eq.get("px"),
            "px_chg_1d_pct":eq.get("px_chg_1d_pct"),
            "mkt_cap_b":    eq.get("mkt_cap_b"),
            "fundamentals": {
                "pe_ttm":         eq.get("pe_ttm"),
                "peg":            eq.get("peg"),
                "fcf_yield_pct":  eq.get("fcf_yield_pct"),
                "roe_pct":        eq.get("roe_pct"),
                "debt_to_equity": eq.get("debt_to_equity"),
                "src":            "FMP",
            },
            "technicals": {
                "rsi_14":          sig.get("rsi_14"),
                "rsi_signal":      sig.get("rsi_signal"),
                "ema_20_50_200":   sig.get("ema_20_50_200"),
                "ema_cross":       sig.get("ema_cross"),
                "px_vs_ema200_pct":sig.get("px_vs_ema200_pct"),
                "squeeze_active":  sig.get("squeeze_active"),
                "momentum_mom2_12":sig.get("momentum_mom2_12"),
                "rs_vs_spy":       sig.get("rs_vs_spy"),
                "rs_class":        sig.get("rs_class"),
            },
            "risk_reward": {
                "support":       sig.get("support"),
                "resistance":    sig.get("resistance"),
                "upside_pct":    sig.get("upside_pct"),
                "downside_pct":  sig.get("downside_pct"),
                "risk_reward":   sig.get("risk_reward"),
                "asymmetry_pass":sig.get("asymmetry_pass"),
            },
            "graham":      sig.get("graham"),
            "sortino":     sig.get("sortino"),
            "candidate":   sig.get("candidate", False),
            "score":       sig.get("overall_score", 0),
            "news":        eq.get("news", []),
        }
        equities_clean.append(entry)

    feed = {
        "report_date":   date_str,
        "generated_at":  ts_str,
        "feed_version":  "1.0",
        "macro": {
            "us": {k: v for k, v in macro.items() if not k.startswith("ecb") and not k.startswith("eu")},
            "eu": {k: v for k, v in macro.items() if k.startswith("ecb") or k.startswith("eu")},
        },
        "sentiment": sentiment,
        "equities":  equities_clean,
        "watchlist": WATCHLIST,
    }

    # Save feed for debugging
    feed_path = OUTPUT_DIR / f"feed_{date_str}.json"
    feed_path.write_text(json.dumps(feed, indent=2, default=str), encoding="utf-8")
    print(f"[CIO] Feed saved → {feed_path}")

    # ── Step 6: LLM inference ─────────────────────────────────────────────────
    print("[CIO] Sending to LLM (OpenAI)...")
    try:
        cio_report = await generate_report(feed)
        log["steps"]["llm"] = f"ok (${cio_report['_meta']['cost_usd_est']})"
        print(f"[CIO] LLM done. Cost: ${cio_report['_meta']['cost_usd_est']}")
    except Exception as e:
        log["steps"]["llm"] = f"ERROR: {e}"
        print(f"[CIO] LLM failed: {e}")
        await notify_discord(f"❌ CIO pipeline FAILED at LLM step: {e}", success=False)
        raise

    # ── Step 7: Render HTML ───────────────────────────────────────────────────
    print("[CIO] Rendering HTML report...")
    env      = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    template = env.get_template("report.html")

    html = template.render(
        report_date    = date_str,
        generated_at   = ts_str,
        regime_label   = cio_report.get("regime_label", "NEUTRAL"),
        one_line_summary = cio_report.get("one_line_summary", ""),
        macro_regime_summary = cio_report.get("macro_regime_summary", ""),
        macro          = feed["macro"],
        report         = cio_report,
        meta           = cio_report.get("_meta", {}),
    )

    report_path = OUTPUT_DIR / f"report_{date_str}.html"
    report_path.write_text(html, encoding="utf-8")
    print(f"[CIO] Report saved → {report_path}")

    # ── Step 8: Regenerate index ──────────────────────────────────────────────
    regenerate_index(OUTPUT_DIR)

    # ── Step 9: Save pipeline log ─────────────────────────────────────────────
    log["status"] = "success"
    log_path = OUTPUT_DIR / f"pipeline_log_{date_str}.json"
    log_path.write_text(json.dumps(log, indent=2), encoding="utf-8")

    # ── Step 10: Discord success notification ─────────────────────────────────
    summary = cio_report.get("one_line_summary", "Report generated.")
    score   = cio_report.get("overall_conviction_score", "?")
    await notify_discord(
        f"✅ **CIO Report {date_str}** | Conviction: {score}/100\n{summary}",
        success=True,
    )
    print("[CIO] Pipeline complete ✓")


if __name__ == "__main__":
    asyncio.run(run())
