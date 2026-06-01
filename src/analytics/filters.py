"""
Pre-AI mathematical filters — pure pandas/numpy, no pandas-ta dependency.
"""
import numpy as np
import pandas as pd


def sortino_ratio(closes, annual_risk_free=0.045):
    if len(closes) < 60:
        return None
    prices  = np.array(closes, dtype=float)
    returns = np.diff(prices) / prices[:-1]
    mar     = annual_risk_free / 252
    downside = np.minimum(0.0, returns - mar) ** 2
    downside_risk = np.sqrt(np.mean(downside))
    if downside_risk == 0:
        return None
    return round(float((np.mean(returns) - mar) / downside_risk), 3)


def bollinger_squeeze(closes):
    if len(closes) < 30:
        return False
    s = pd.Series(closes, dtype=float)
    ma  = s.rolling(20).mean()
    std = s.rolling(20).std()
    bb_width = (2 * std / ma).iloc[-1]
    avg_width = (2 * std / ma).rolling(60).mean().iloc[-1]
    if pd.isna(bb_width) or pd.isna(avg_width):
        return False
    return bool(bb_width < avg_width * 0.75)


def graham_margin_of_safety(current_price, eps, book_value_per_share,
                             growth_rate_5y=None, is_growth_stock=False):
    if not current_price or current_price <= 0:
        return {"intrinsic": None, "margin_pct": None, "method": "n/a"}
    if is_growth_stock and growth_rate_5y and growth_rate_5y > 0:
        intrinsic = eps * (8.5 + 2 * growth_rate_5y * 100)
        method = "graham_growth"
    else:
        if not eps or not book_value_per_share or eps <= 0 or book_value_per_share <= 0:
            return {"intrinsic": None, "margin_pct": None, "method": "missing_data"}
        intrinsic = (22.5 * eps * book_value_per_share) ** 0.5
        method = "graham_classic"
    margin_pct = round((intrinsic - current_price) / current_price * 100, 1)
    return {"intrinsic": round(intrinsic, 2), "margin_pct": margin_pct, "method": method}


def momentum_mom2_12(closes):
    if len(closes) < 252:
        return None
    p_12m = closes[-252]
    p_1m  = closes[-21]
    if p_12m <= 0:
        return None
    return round((p_1m - p_12m) / p_12m, 4)


def ema(series, span):
    return series.ewm(span=span, adjust=False).mean()


def ema_signal(closes):
    if len(closes) < 200:
        return {"ema_20_50_200": "insufficient_data", "ema_cross": "n/a", "px_vs_ema200_pct": None}
    s = pd.Series(closes, dtype=float)
    e20  = ema(s, 20).iloc[-1]
    e50  = ema(s, 50).iloc[-1]
    e200 = ema(s, 200).iloc[-1]
    if e20 > e50 > e200:
        alignment = "bull_aligned"
    elif e20 < e50 < e200:
        alignment = "bear_aligned"
    else:
        alignment = "mixed"
    e50_s  = ema(s, 50)
    e200_s = ema(s, 200)
    cross = "none"
    if len(s) >= 6:
        if e50_s.iloc[-1] > e200_s.iloc[-1] and e50_s.iloc[-6] <= e200_s.iloc[-6]:
            cross = "golden_cross"
        elif e50_s.iloc[-1] < e200_s.iloc[-1] and e50_s.iloc[-6] >= e200_s.iloc[-6]:
            cross = "death_cross"
    return {"ema_20_50_200": alignment, "ema_cross": cross,
            "px_vs_ema200_pct": round((closes[-1] / e200 - 1) * 100, 2)}


def rsi(series, period=14):
    delta = series.diff()
    gain  = delta.clip(lower=0).rolling(period).mean()
    loss  = (-delta.clip(upper=0)).rolling(period).mean()
    rs    = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def rsi_signal(closes, benchmark_closes=None):
    if len(closes) < 15:
        return {"rsi_14": None, "rsi_signal": "n/a"}
    s = pd.Series(closes, dtype=float)
    rsi_val = float(rsi(s).iloc[-1])
    signal = "overbought" if rsi_val > 70 else ("oversold" if rsi_val < 30 else "neutral")
    result = {"rsi_14": round(rsi_val, 1), "rsi_signal": signal}
    if benchmark_closes and len(benchmark_closes) >= 15:
        b = pd.Series(benchmark_closes, dtype=float)
        bench_rsi = float(rsi(b).iloc[-1])
        rs_ratio = rsi_val / bench_rsi if bench_rsi > 0 else 1.0
        result["rs_vs_spy"] = round(rs_ratio, 3)
        result["rs_class"] = "leader" if rs_ratio > 1.1 else ("laggard" if rs_ratio < 0.9 else "inline")
    return result


def risk_reward(closes, highs, lows):
    if len(closes) < 60:
        return {"risk_reward": None, "asymmetry_pass": False}
    px         = closes[-1]
    support    = min(lows[-60:])
    resistance = max(highs[-60:])
    upside     = max(resistance - px, 0)
    downside   = max(px - support, 0.01)
    rr         = upside / downside
    return {
        "support": round(support, 2), "resistance": round(resistance, 2),
        "upside_pct": round(upside / px * 100, 1),
        "downside_pct": round(downside / px * 100, 1),
        "risk_reward": round(rr, 2), "asymmetry_pass": rr >= 2.0,
    }


def screen_equity(equity, risk_free_rate=0.045, spy_closes=None):
    closes = equity.get("closes", [])
    highs  = equity.get("highs", [])
    lows   = equity.get("lows", [])
    signals = {}
    signals["sortino"]          = sortino_ratio(closes, risk_free_rate)
    signals["squeeze_active"]   = bollinger_squeeze(closes)
    signals["momentum_mom2_12"] = momentum_mom2_12(closes)
    signals.update(ema_signal(closes))
    signals.update(rsi_signal(closes, spy_closes))
    signals.update(risk_reward(closes, highs, lows))
    px   = equity.get("px") or 0
    eps  = equity.get("eps")
    bvps = equity.get("book_value_per_share")
    pe   = equity.get("pe_ttm") or 0
    signals["graham"] = graham_margin_of_safety(px, eps or 0, bvps or 0, None, pe > 30)
    passes = sum([
        signals.get("asymmetry_pass", False),
        (signals.get("sortino") or 0) > 0.5,
        signals.get("squeeze_active", False),
        (signals.get("momentum_mom2_12") or 0) > 0.1,
        (signals.get("graham", {}).get("margin_pct") or 0) < -10,
    ])
    signals["overall_score"] = passes
    signals["candidate"]     = passes >= 2
    return signals
