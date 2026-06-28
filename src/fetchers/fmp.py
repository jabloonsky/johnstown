"""
Fetches equity data from Financial Modeling Prep.
Tries the new /stable/ endpoints first, falls back to legacy /api/v3/.
Logs the real HTTP status code so failures are diagnosable.
"""
import os
import re
import httpx

STABLE = "https://financialmodelingprep.com/stable"
LEGACY = "https://financialmodelingprep.com/api/v3"


def _safe_url(url) -> str:
    """Strip apikey from URL — used in logs and error messages."""
    return re.sub(r"[?&]apikey=[^&]*", "", str(url)).rstrip("?&")


async def _get(client, url, params):
    params["apikey"] = os.environ["FMP_API_KEY"]
    r = await client.get(url, params=params)
    if r.status_code != 200:
        safe = _safe_url(r.request.url)
        print(f"[FMP] {r.status_code} on {safe} -> {r.text[:200]}")
        raise ValueError(f"HTTP {r.status_code} on {safe}")
    return r.json()


async def fetch_equity(symbol: str) -> dict:
    result = {"symbol": symbol, "src": "FMP"}
    async with httpx.AsyncClient(timeout=20) as client:

        # --- Quote: try stable, then legacy ---
        quote = None
        try:
            quote = await _get(client, f"{STABLE}/quote", {"symbol": symbol})
        except Exception:
            try:
                quote = await _get(client, f"{LEGACY}/quote/{symbol}", {})
            except Exception as e:
                result["quote_error"] = str(e)
        if quote:
            q = quote[0] if isinstance(quote, list) else quote
            result["px"] = q.get("price")
            result["px_chg_1d_pct"] = q.get("changesPercentage") or q.get("changePercentage")
            mc = q.get("marketCap")
            result["mkt_cap_b"] = round(mc / 1e9, 2) if mc else None

        # --- Ratios TTM ---
        try:
            try:
                ratios = await _get(client, f"{STABLE}/ratios-ttm", {"symbol": symbol})
            except Exception:
                ratios = await _get(client, f"{LEGACY}/ratios-ttm/{symbol}", {})
            if ratios:
                r0 = ratios[0] if isinstance(ratios, list) else ratios
                result["pe_ttm"]        = r0.get("priceToEarningsRatioTTM") or r0.get("peRatioTTM")
                result["peg"]           = r0.get("priceToEarningsGrowthRatioTTM") or r0.get("pegRatioTTM")
                fcf = r0.get("freeCashFlowYieldTTM")
                result["fcf_yield_pct"] = round(fcf * 100, 2) if fcf else None
                roe = r0.get("returnOnEquityTTM")
                result["roe_pct"]       = round(roe * 100, 2) if roe else None
                result["debt_to_equity"]= r0.get("debtToEquityRatioTTM") or r0.get("debtEquityRatioTTM")
                result["pb_ratio"]      = r0.get("priceToBookRatioTTM") or r0.get("priceBookValueRatioTTM")
                result["eps"]           = r0.get("epsTTM")
        except Exception as e:
            result["ratios_error"] = str(e)

        # --- Key metrics for Graham (book value per share) ---
        try:
            try:
                metrics = await _get(client, f"{STABLE}/key-metrics-ttm", {"symbol": symbol})
            except Exception:
                metrics = await _get(client, f"{LEGACY}/key-metrics-ttm/{symbol}", {})
            if metrics:
                m0 = metrics[0] if isinstance(metrics, list) else metrics
                result["book_value_per_share"] = m0.get("bookValuePerShareTTM")
        except Exception as e:
            result["metrics_error"] = str(e)

        # --- Derive Graham inputs when not returned directly by FMP free tier ---
        # epsTTM is absent from ratios-ttm; derive from price / PE.
        # BVPS: derive from price / P/B when key-metrics-ttm doesn't return it.
        px = result.get("px") or 0
        if not result.get("eps") and px > 0:
            pe = result.get("pe_ttm") or 0
            if pe > 0:
                result["eps"] = round(px / pe, 4)
        if not result.get("book_value_per_share") and px > 0:
            pb = result.get("pb_ratio") or 0
            if pb > 0:
                result["book_value_per_share"] = round(px / pb, 4)

        # --- Price history (for math filters) ---
        try:
            hist = None
            try:
                hist = await _get(client, f"{STABLE}/historical-price-eod/full",
                                  {"symbol": symbol})
            except Exception:
                hist = await _get(client, f"{LEGACY}/historical-price-full/{symbol}",
                                  {"timeseries": 252})
            rows = hist.get("historical") if isinstance(hist, dict) else hist
            if rows:
                rows = list(reversed(rows))[-252:]
                result["closes"] = [d["close"] for d in rows]
                result["highs"]  = [d["high"]  for d in rows]
                result["lows"]   = [d["low"]   for d in rows]
        except Exception as e:
            result["history_error"] = str(e)

    return result


async def fetch_all_equities(symbols):
    results = []
    for symbol in symbols:
        try:
            results.append(await fetch_equity(symbol))
        except Exception as e:
            results.append({"symbol": symbol, "error": str(e)})
    return results
