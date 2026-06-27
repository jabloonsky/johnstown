"""
Fetches macroeconomic data from FRED (Federal Reserve Economic Data).
Free API, no daily limits, most reliable source in the pipeline.
"""
import os
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential


FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"

# (series_id, units): units="pc1" asks FRED to return percent-change-from-year-ago
# instead of the raw index level, fixing CPI/HICP reading as ~330 instead of ~3%.
# yield_curve field is in percentage points (0.31 = 31 bps) — named _pct to match.
SERIES = {
    "fed_funds_pct":           ("FEDFUNDS",            "lin"),
    "cpi_yoy_pct":             ("CPIAUCSL",            "pc1"),
    "ust10y_pct":              ("DGS10",               "lin"),
    "yield_curve_10y_2y_pct":  ("T10Y2Y",             "lin"),
    "breakeven_inflation_pct": ("T10YIE",              "lin"),
    "unemployment_pct":        ("UNRATE",              "lin"),
    "ecb_deposit_pct":         ("ECBDFR",              "lin"),
    "eu_hicp_yoy_pct":         ("CP0000EZ19M086NEST",  "pc1"),
}


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def _fetch_series(client: httpx.AsyncClient, series_id: str, api_key: str,
                        units: str = "lin") -> dict:
    params = {
        "series_id":  series_id,
        "api_key":    api_key,
        "file_type":  "json",
        "sort_order": "desc",
        "limit":      1,
    }
    if units != "lin":
        params["units"] = units
    r = await client.get(FRED_BASE, params=params)
    r.raise_for_status()
    obs = r.json()["observations"][0]
    return {"v": float(obs["value"]) if obs["value"] != "." else None,
            "as_of": obs["date"],
            "src": f"FRED:{series_id}"}


async def fetch_macro() -> dict:
    api_key = os.environ["FRED_API_KEY"]
    result = {}
    async with httpx.AsyncClient(timeout=15) as client:
        for field, (series_id, units) in SERIES.items():
            try:
                result[field] = await _fetch_series(client, series_id, api_key, units)
            except Exception as e:
                result[field] = {"v": None, "error": str(e), "src": f"FRED:{series_id}"}
    return result
