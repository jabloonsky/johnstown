"""
Pre-AI mathematical filters.
All arithmetic happens here. The LLM receives only the OUTPUT signals,
never raw price series or OHLCV data.
"""
import numpy as np
import pandas as pd
try:
    import pandas_ta as ta
    HAS_TA = True
except Exception:
    HAS_TA = False


# ---------------------------------------------------------------------------
# 1. SORTINO RATIO
#    Penalises only downside volatility. Better than Sharpe for asymmetry hunting.
#    MAR = daily risk-free rate derived from FEDFUNDS (passed in at runtime).
# ---------------------------------------------------------------------------
def sortino_ratio(closes: list[float], annual_risk_free: float = 0.045) -> float | None:
    if len(closes) < 60:
        return None
    prices  = np.array(closes, dtype=float)
    returns = np.diff(prices) / prices[:-1]
    mar     = annual_risk_free / 252          # daily minimum acceptable return
    downside = np.minimum(0.0, returns - mar) ** 2
    downside_risk = np.sqrt(np.mean(downside))
    if downside_risk == 0:
        return None
    excess = np.mean(returns) - mar
    return round(float(excess / downside_risk), 3)


# ---------------------------------------------------------------------------
# 2. BOLLINGER BAND SQUEEZE
#    Volatility compression → imminent breakout.
#    True = squeeze active now = watch for explosion.
# ---------------------------------------------------------------------------
def bollinger_squeeze(closes: list[float]) -> bool:
    if not HAS_TA or len(closes) < 30:
        return False
    df = pd.DataFrame({"close": closes})
    try:
        sq = ta.squeeze(df["close"], lazybear=False)
        # SQZ column: 1 = no squeeze (fired), 0 = squeeze ON
        if sq is not None and not sq.empty:
            last = sq.iloc[-1]
            # pandas_ta squeeze returns SQZ_ON column when squeeze is active
            col = [c for c in sq.columns if "SQZ_ON" in c or "ON" in c]
            if col:
                return bool(last[col[0]])
    except Exception:
        pass
    # Fallback: manual Bollinger vs Keltner width check
    s = pd.Series(closes)
    bb_std  = s.rolling(20).std()
    bb_upper = s.rolling(20).mean() + 2 * bb_std
    bb_lower = s.rolling(20).mean() - 2 * bb_std
    bb_width = (bb_upper - bb_lower) / s.rolling(20).mean()
    return bool(bb_width.iloc[-1] < bb_width.rolling(60).mean().iloc[-1] * 0.75)


# ---------------------------------------------------------------------------
# 3. GRAHAM MARGIN OF SAFETY
#    Classic: sqrt(22.5 * EPS * BookValue). Negative % = UNDERVALUED.
#    Note: unreliable for asset-light tech stocks — flag "growth_sector" in output.
# ---------------------------------------------------------------------------
def graham_margin_of_safety(current_price: float,
                             eps: float,
                             book_value_per_share: float,
                             growth_rate_5y: float | None = None,
                             is_growth_stock: bool = False) -> dict:
    if current_price is None or current_price <= 0:
        return {"intrinsic": None, "margin_pct": None, "method": "n/a"}

    if is_growth_stock and growth_rate_5y is not None and growth_rate_5y > 0:
        # Graham growth formula: V = EPS × (8.5 + 2g) × 4.4 / Y
        # Y = current AAA bond yield (we approximate with 4.4 baseline)
        intrinsic = eps * (8.5 + 2 * growth_rate_5y * 100)
        method = "graham_growth"
    else:
        if eps is None or book_value_per_share is None:
            return {"intrinsic": None, "margin_pct": None, "method": "missing_data"}
        if eps <= 0 or book_value_per_share <= 0:
            return {"intrinsic": None, "margin_pct": None, "method": "negative_earnings"}
        intrinsic = (22.5 * eps * book_value_per_share) ** 0.5
        method = "graham_classic"

    margin_pct = round((intrinsic - current_price) / current_price * 100, 1)
    return {
        "intrinsic": round(intrinsic, 2),
        "margin_pct": margin_pct,   # negative = undervalued vs intrinsic
        "method": method,
    }


# ---------------------------------------------------------------------------
# 4. AQR MOMENTUM (MOM2-12)
#    12-month return, excluding the most recent month.
#    Skipping last month removes short-term reversal noise.
# ---------------------------------------------------------------------------
def momentum_mom2_12(closes: list[float]) -> float | None:
    if len(closes) < 252:
        return None
    # Price 12 months ago (252 trading days)
    p_12m  = closes[-252]
    # Price 1 month ago (21 trading days) — skip the last month
    p_1m   = closes[-21]
    if p_12m <= 0:
        return None
    return round((p_1m - p_12m) / p_12m, 4)


# ---------------------------------------------------------------------------
# 5. EMA ALIGNMENT (TREND)
# ---------------------------------------------------------------------------
def ema_signal(closes: list[float]) -> dict:
    if not HAS_TA or len(closes) < 200:
        return {"ema_20_50_200": "insufficient_data", "ema_cross": "n/a"}

    s = pd.Series(closes, dtype=float)
    e20  = ta.ema(s, length=20)
    e50  = ta.ema(s, length=50)
    e200 = ta.ema(s, length=200)

    v20, v50, v200 = e20.iloc[-1], e50.iloc[-1], e200.iloc[-1]

    if v20 > v50 > v200:
        alignment = "bull_aligned"
    elif v20 < v50 < v200:
        alignment = "bear_aligned"
    else:
        alignment = "mixed"

    # Golden / Death cross in last 5 days
    cross = "none"
    if len(e50) >= 6 and len(e200) >= 6:
        if e50.iloc[-1] > e200.iloc[-1] and e50.iloc[-6] <= e200.iloc[-6]:
            cross = "golden_cross"
        elif e50.iloc[-1] < e200.iloc[-1] and e50.iloc[-6] >= e200.iloc[-6]:
            cross = "death_cross"

    return {"ema_20_50_200": alignment, "ema_cross": cross,
            "px_vs_ema200_pct": round((closes[-1] / v200 - 1) * 100, 2)}


# ---------------------------------------------------------------------------
# 6. RSI + RELATIVE STRENGTH vs BENCHMARK
# ---------------------------------------------------------------------------
def rsi_signal(closes: list[float], benchmark_closes: list[float] | None = None) -> dict:
    if not HAS_TA or len(closes) < 15:
        return {"rsi_14": None, "rsi_signal": "n/a"}

    s = pd.Series(closes, dtype=float)
    rsi_val = float(ta.rsi(s, length=14).iloc[-1])

    signal = "neutral"
    if rsi_val > 70:
        signal = "overbought"
    elif rsi_val < 30:
        signal = "oversold"

    result = {"rsi_14": round(rsi_val, 1), "rsi_signal": signal}

    if benchmark_closes and len(benchmark_closes) >= 15:
        b = pd.Series(benchmark_closes, dtype=float)
        bench_rsi = float(ta.rsi(b, length=14).iloc[-1])
        rs = rsi_val / bench_rsi if bench_rsi > 0 else 1.0
        result["rs_vs_spy"] = round(rs, 3)
        result["rs_class"] = "leader" if rs > 1.1 else ("laggard" if rs < 0.9 else "inline")

    return result


# ---------------------------------------------------------------------------
# 7. RISK / REWARD RATIO
#    Uses 60-day rolling support/resistance as price targets.
#    asymmetry_pass = True when upside is at least 2× the downside.
# ---------------------------------------------------------------------------
def risk_reward(closes: list[float], highs: list[float], lows: list[float]) -> dict:
    if len(closes) < 60:
        return {"risk_reward": None, "asymmetry_pass": False}

    px         = closes[-1]
    support    = min(lows[-60:])
    resistance = max(highs[-60:])

    upside   = max(resistance - px, 0)
    downside = max(px - support, 0.01)
    rr       = upside / downside

    return {
        "support":       round(support, 2),
        "resistance":    round(resistance, 2),
        "upside_pct":    round(upside / px * 100, 1),
        "downside_pct":  round(downside / px * 100, 1),
        "risk_reward":   round(rr, 2),
        "asymmetry_pass": rr >= 2.0,
    }


# ---------------------------------------------------------------------------
# MASTER SCREENER — runs all filters on one equity, returns clean signal dict
# ---------------------------------------------------------------------------
def screen_equity(equity: dict,
                  risk_free_rate: float = 0.045,
                  spy_closes: list[float] | None = None) -> dict:
    closes = equity.get("closes", [])
    highs  = equity.get("highs", [])
    lows   = equity.get("lows", [])

    signals = {}
    signals["sortino"]           = sortino_ratio(closes, risk_free_rate)
    signals["squeeze_active"]    = bollinger_squeeze(closes)
    signals["momentum_mom2_12"]  = momentum_mom2_12(closes)
    signals.update(ema_signal(closes))
    signals.update(rsi_signal(closes, spy_closes))
    signals.update(risk_reward(closes, highs, lows))

    # Graham (needs fundamentals from FMP)
    px   = equity.get("px") or 0
    eps  = equity.get("eps")
    bvps = equity.get("book_value_per_share")
    g5   = equity.get("revenue_growth_5y")
    # Simple heuristic: P/E > 30 suggests growth stock
    pe   = equity.get("pe_ttm") or 0
    is_growth = pe > 30
    graham = graham_margin_of_safety(px, eps or 0, bvps or 0, g5, is_growth)
    signals["graham"] = graham

    # Overall pass: positive asymmetry requires at least 2 of these
    passes = sum([
        signals.get("asymmetry_pass", False),
        (signals.get("sortino") or 0) > 0.5,
        signals.get("squeeze_active", False),
        (signals.get("momentum_mom2_12") or 0) > 0.1,
        (graham.get("margin_pct") or 0) < -10,
    ])
    signals["overall_score"] = passes     # 0-5
    signals["candidate"]     = passes >= 2

    return signals
