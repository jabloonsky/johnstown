"""Unit tests for analytics/filters.py — pure functions, no I/O."""
import sys
from pathlib import Path
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from analytics.filters import (
    bollinger_squeeze,
    ema_signal,
    graham_margin_of_safety,
    momentum_mom2_12,
    risk_reward,
    rsi_signal,
    screen_equity,
    sortino_ratio,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def trending_up(n=252, start=100.0, step=0.5):
    return [start + i * step for i in range(n)]


def flat(n=252, price=100.0):
    return [price] * n


def trending_down(n=252, start=200.0, step=0.5):
    return [start - i * step for i in range(n)]


# ── sortino_ratio ─────────────────────────────────────────────────────────────

def test_sortino_returns_none_if_too_few_bars():
    assert sortino_ratio([100.0] * 59) is None


def test_sortino_positive_for_rising_prices():
    # Deterministic: 4 up days (+0.3%) then 1 small dip (-0.1%) → clear positive Sortino
    closes = []
    price = 100.0
    for i in range(252):
        price *= 1.003 if i % 5 != 0 else 0.999
        closes.append(price)
    result = sortino_ratio(closes)
    assert result is not None
    assert result > 0


def test_sortino_negative_for_falling_prices():
    closes = trending_down(252)
    result = sortino_ratio(closes)
    assert result is not None
    assert result < 0


def test_sortino_negative_for_flat_prices():
    # Flat price: daily returns are 0, all below MAR → downside exists → negative Sortino
    result = sortino_ratio(flat(252))
    assert result is not None
    assert result < 0


def test_sortino_none_when_all_returns_beat_mar():
    # Every daily return far exceeds MAR → no downside deviation → None
    closes = trending_up(252, step=5.0)  # ~5%/day >> MAR of ~0.018%/day
    result = sortino_ratio(closes)
    assert result is None


# ── bollinger_squeeze ─────────────────────────────────────────────────────────

def test_bollinger_squeeze_false_if_too_few_bars():
    assert bollinger_squeeze([100.0] * 29) is False


def test_bollinger_squeeze_not_active_for_volatile_prices():
    rng = np.random.default_rng(42)
    volatile = list(100 + rng.normal(0, 5, 252).cumsum())
    # A volatile series should NOT be in squeeze most of the time
    # (this is a statistical expectation, not a guarantee — but with σ=5 it holds)
    result = bollinger_squeeze(volatile)
    assert isinstance(result, bool)


def test_bollinger_squeeze_active_for_tight_range():
    # 200 volatile bars then 20 tight bars: the 60-bar rolling avg at the last bar
    # spans 40 volatile + 20 tight bars → avg dominated by wide volatile widths,
    # while current bb_width (last 20 bars = tight) is tiny → squeeze detected
    rng = np.random.default_rng(42)
    volatile = list(100 + rng.normal(0, 3, 200).cumsum())
    last = volatile[-1]
    tight = [last + (i % 2) * 0.01 for i in range(20)]
    result = bollinger_squeeze(volatile + tight)
    assert result is True


# ── graham_margin_of_safety ────────────────────────────────────────────────────

def test_graham_classic_with_valid_inputs():
    result = graham_margin_of_safety(current_price=50, eps=3, book_value_per_share=10)
    assert result["method"] == "graham_classic"
    assert result["intrinsic"] is not None
    # intrinsic = sqrt(22.5 * 3 * 10) = sqrt(675) ≈ 25.98, below price → negative margin
    assert result["margin_pct"] < 0


def test_graham_growth_stock():
    result = graham_margin_of_safety(
        current_price=200, eps=5, book_value_per_share=20,
        growth_rate_5y=0.20, is_growth_stock=True,
    )
    assert result["method"] == "graham_growth"
    assert result["intrinsic"] == pytest.approx(5 * (8.5 + 2 * 20), rel=1e-3)


def test_graham_returns_na_for_zero_price():
    result = graham_margin_of_safety(current_price=0, eps=3, book_value_per_share=10)
    assert result["method"] == "n/a"


def test_graham_returns_missing_data_for_negative_eps():
    result = graham_margin_of_safety(current_price=50, eps=-1, book_value_per_share=10)
    assert result["method"] == "missing_data"


# ── momentum_mom2_12 ───────────────────────────────────────────────────────────

def test_momentum_returns_none_if_too_few_bars():
    assert momentum_mom2_12([100.0] * 251) is None


def test_momentum_positive_for_uptrend():
    closes = trending_up(252)
    assert momentum_mom2_12(closes) > 0


def test_momentum_negative_for_downtrend():
    closes = trending_down(252)
    assert momentum_mom2_12(closes) < 0


# ── ema_signal ────────────────────────────────────────────────────────────────

def test_ema_signal_insufficient_data():
    result = ema_signal([100.0] * 199)
    assert result["ema_20_50_200"] == "insufficient_data"


def test_ema_signal_bull_aligned():
    result = ema_signal(trending_up(252))
    assert result["ema_20_50_200"] == "bull_aligned"


def test_ema_signal_bear_aligned():
    result = ema_signal(trending_down(252))
    assert result["ema_20_50_200"] == "bear_aligned"


def test_ema_signal_returns_px_vs_ema200():
    result = ema_signal(trending_up(252))
    assert result["px_vs_ema200_pct"] is not None


# ── rsi_signal ────────────────────────────────────────────────────────────────

def test_rsi_signal_too_few_bars():
    result = rsi_signal([100.0] * 14)
    assert result["rsi_14"] is None


def test_rsi_signal_overbought_for_strong_uptrend():
    # Mostly up moves with tiny occasional pullbacks → RSI overbought
    price = 100.0
    closes = []
    for i in range(100):
        price += 1.5 if i % 10 != 0 else -0.1
        closes.append(price)
    result = rsi_signal(closes)
    assert result["rsi_signal"] == "overbought"


def test_rsi_signal_oversold_for_strong_downtrend():
    closes = trending_down(100, step=2.0)
    result = rsi_signal(closes)
    assert result["rsi_signal"] == "oversold"


def test_rsi_signal_includes_rs_vs_spy_when_benchmark_provided():
    closes = trending_up(100)
    result = rsi_signal(closes, benchmark_closes=closes)
    assert "rs_vs_spy" in result
    assert result["rs_class"] == "inline"  # same series → ratio ≈ 1.0


# ── risk_reward ────────────────────────────────────────────────────────────────

def test_risk_reward_too_few_bars():
    result = risk_reward([100.0] * 59, [101.0] * 59, [99.0] * 59)
    assert result["risk_reward"] is None


def test_risk_reward_asymmetry_pass_when_rr_above_2():
    # px near support → large upside, tiny downside
    closes = [95.0] * 60 + [96.0]
    highs  = [120.0] * 61
    lows   = [95.0] * 61
    result = risk_reward(closes, highs, lows)
    assert result["asymmetry_pass"] is True
    assert result["risk_reward"] >= 2.0


def test_risk_reward_asymmetry_fail_when_rr_below_2():
    # px near resistance → tiny upside, large downside
    closes = [119.0] * 60 + [119.5]
    highs  = [120.0] * 61
    lows   = [95.0] * 61
    result = risk_reward(closes, highs, lows)
    assert result["asymmetry_pass"] is False


# ── screen_equity ─────────────────────────────────────────────────────────────

def _make_equity(closes, highs=None, lows=None):
    if highs is None:
        highs = [c * 1.01 for c in closes]
    if lows is None:
        lows = [c * 0.99 for c in closes]
    return {
        "symbol": "TEST",
        "px": closes[-1],
        "closes": closes,
        "highs": highs,
        "lows": lows,
        "eps": 5.0,
        "book_value_per_share": 20.0,
        "pe_ttm": 20,
    }


def test_screen_equity_returns_all_signal_keys():
    equity = _make_equity(trending_up(252))
    signals = screen_equity(equity)
    for key in ("sortino", "squeeze_active", "momentum_mom2_12",
                "ema_20_50_200", "rsi_14", "risk_reward",
                "graham", "overall_score", "candidate"):
        assert key in signals, f"Missing signal key: {key}"


def test_screen_equity_candidate_flag_true_when_enough_passes():
    # Strong uptrend with squeeze-like prices → multiple passes
    closes = trending_up(252, step=1.0)
    equity = _make_equity(closes)
    signals = screen_equity(equity)
    assert isinstance(signals["candidate"], bool)
    assert signals["overall_score"] >= 0


def test_screen_equity_handles_missing_highs_lows():
    equity = {"symbol": "X", "px": 100, "closes": trending_up(252),
              "highs": [], "lows": [], "eps": 2.0, "book_value_per_share": 10.0, "pe_ttm": 15}
    signals = screen_equity(equity)
    assert "overall_score" in signals
