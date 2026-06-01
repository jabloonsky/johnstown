"""
Fetches macroeconomic data from FRED (Federal Reserve Economic Data).
Free API, no daily limits, most reliable source in the pipeline.
"""
import os
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential


FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"

SERIES = {
    "fed_funds_pct":          "FEDFUNDS",
    "cpi_yoy_pct":            "CPIAUCSL",
    "ust10y_pct":             "DGS10",
    "yield_curve_10y_2y_bps": "T10Y2Y",
    "breakeven_inflation_pct":"T10YIE",
    "unemployment_pct":       "UNRATE",
    "ecb_deposit_pct":        "ECBDFR",
    "eu_hicp_yoy_pct":        "CP0000EZ19M086NEST",
}


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def _fetch_series(client: httpx.AsyncClient, series_id: str, api_key: str) -> dict:
    r = await client.get(FRED_BASE, params={
        "series_id":  series_id,
        "api_key":    api_key,
        "file_type":  "json",
        "sort_order": "desc",
        "limit":      1,
    })
    r.raise_for_status()
    obs = r.json()["observations"][0]
    return {"v": float(obs["value"]) if obs["value"] != "." else None,
            "as_of": obs["date"],
            "src": f"FRED:{series_id}"}


async def fetch_macro() -> dict:
    api_key = os.environ["FRED_API_KEY"]
    result = {}
    async with httpx.AsyncClient(timeout=15) as client:
        for field, series_id in SERIES.items():
            try:
                result[field] = await _fetch_series(client, series_id, api_key)
            except Exception as e:
                result[field] = {"v": None, "error": str(e), "src": f"FRED:{series_id}"}
    return result
