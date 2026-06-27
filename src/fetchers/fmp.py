"""
Fetches equity fundamentals and price history from Financial Modeling Prep.
Free tier: 250 calls/day. We use ~30-40 calls for 5 symbols.
"""
import os
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

FMP_BASE = "https://financialmodelingprep.com/api/v3"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def _get(client: httpx.AsyncClient, path: str, params: dict) -> dict | list:
    params["apikey"] = os.environ["FMP_API_KEY"]
    r = await client.get(f"{FMP_BASE}{path}", params=params)
    r.raise_for_status()
    data = r.json()
    # FMP returns 200 with {"Error Message": "..."} when the key is invalid or
    # the endpoint requires a higher plan tier.
    if isinstance(data, dict) and "Error Message" in data:
        raise ValueError(data["Error Message"])
    return data


async def fetch_equity(symbol: str) -> dict:
    """Returns quote + ratios + 1yr price history for one symbol."""
    async with httpx.AsyncClient(timeout=20) as client:
        result = {"symbol": symbol, "src": "FMP"}

        # --- Current price + basic stats ---
        try:
            quote = await _get(client, f"/quote/{symbol}", {})
            if quote:
                q = quote[0]
                result["px"]            = q.get("price")
                result["px_chg_1d_pct"] = q.get("changesPercentage")
                result["mkt_cap_b"]     = round(q.get("marketCap", 0) / 1e9, 2)
        except Exception as e:
            result["quote_error"] = str(e)
            print(f"[FMP] {symbol} quote error: {e}")

        # --- TTM ratios (P/E, FCF yield, etc.) ---
        try:
            ratios = await _get(client, f"/ratios-ttm/{symbol}", {})
            if ratios:
                r0 = ratios[0]
                result["pe_ttm"]         = r0.get("peRatioTTM")
                result["peg"]            = r0.get("pegRatioTTM")
                result["fcf_yield_pct"]  = round((r0.get("freeCashFlowYieldTTM") or 0) * 100, 2)
                result["roe_pct"]        = round((r0.get("returnOnEquityTTM") or 0) * 100, 2)
                result["debt_to_equity"] = r0.get("debtEquityRatioTTM")
                result["eps"]            = r0.get("epsTTM")
        except Exception as e:
            result["ratios_error"] = str(e)
            print(f"[FMP] {symbol} ratios error: {e}")

        # --- Key metrics for Graham analysis (book value per share) ---
        try:
            metrics = await _get(client, f"/key-metrics-ttm/{symbol}", {})
            if metrics:
                result["book_value_per_share"] = metrics[0].get("bookValuePerShareTTM")
        except Exception as e:
            result["metrics_error"] = str(e)
            print(f"[FMP] {symbol} key-metrics error: {e}")

        # --- 1 year of daily closes (for math filters) ---
        try:
            hist = await _get(client, f"/historical-price-full/{symbol}",
                              {"timeseries": 252})
            if hist and "historical" in hist:
                result["closes"] = [d["close"] for d in reversed(hist["historical"])]
                result["highs"]  = [d["high"]  for d in reversed(hist["historical"])]
                result["lows"]   = [d["low"]   for d in reversed(hist["historical"])]
        except Exception as e:
            result["history_error"] = str(e)
            print(f"[FMP] {symbol} history error: {e}")

        # --- Latest news headlines ---
        try:
            news = await _get(client, "/stock_news",
                              {"tickers": symbol, "limit": 5})
            result["news"] = [
                {"t": n["title"], "ts": n["publishedDate"]}
                for n in (news or [])
            ]
        except Exception as e:
            result["news_error"] = str(e)
            print(f"[FMP] {symbol} news error: {e}")

    return result


async def fetch_all_equities(symbols: list[str]) -> list[dict]:
    """Fetch multiple symbols. Sequential to respect FMP rate limits."""
    results = []
    for symbol in symbols:
        try:
            data = await fetch_equity(symbol)
            results.append(data)
        except Exception as e:
            results.append({"symbol": symbol, "error": str(e)})
    return results
