"""Testy wielookresowego wzorca twarzy -- funkcje czyste, bez I/O ani modeli.

Embeddingi udajemy krotkimi wektorami; liczy sie geometria (kosinus), a nie to,
ile wymiarow ma prawdziwy model.
"""
import math
from datetime import date

import pytest

from timemachine.identity import (
    MatchParams,
    Period,
    Reference,
    cosine,
    generate_periods,
    l2_normalize,
    match_face,
    period_for_date,
    pool_summary,
    select_diverse,
)

BIRTH = date(2023, 4, 12)


# ── helpery ──────────────────────────────────────────────────────────────────

def vec(*values: float) -> list[float]:
    return l2_normalize(list(values))


def ref(ref_id: int, vector, period_idx=None, capture=None, origin="calibrate") -> Reference:
    return Reference(
        id=ref_id, embedding=vector, period_idx=period_idx, capture=capture, origin=origin
    )


def rotated(angle_deg: float) -> list[float]:
    """Wektor jednostkowy na plaszczyznie -- latwo kontrolowac kosinus miedzy nimi."""
    angle = math.radians(angle_deg)
    return [math.cos(angle), math.sin(angle), 0.0]


LOOSE = MatchParams(threshold=0.5, thin_pool_penalty=0.1, min_refs_per_period=2,
                    time_bonus=0.0, top_k=1)


# ── generowanie okresow ──────────────────────────────────────────────────────

def test_periods_start_at_birth_and_are_contiguous():
    periods = generate_periods(BIRTH, date(2029, 1, 1))
    assert periods[0].start == BIRTH
    for earlier, later in zip(periods, periods[1:]):
        assert (later.start - earlier.end).days == 1  # bez dziur i bez zakladek


def test_periods_are_quarterly_in_first_three_years():
    periods = generate_periods(BIRTH, date(2026, 5, 1))
    first_year = [p for p in periods if p.start < date(2024, 4, 12)]
    assert len(first_year) == 4  # 0-3, 3-6, 6-9, 9-12 miesiecy


def test_periods_get_longer_with_age():
    periods = generate_periods(BIRTH, date(2033, 1, 1))
    lengths = [(p.end - p.start).days for p in periods]
    early = lengths[0]
    mid = lengths[14]    # po 3. roku zycia -- polroczne
    late = lengths[-2]   # po 6. roku zycia -- roczne
    assert early < mid < late


def test_period_indexes_are_stable_when_horizon_grows():
    short = generate_periods(BIRTH, date(2025, 1, 1))
    long = generate_periods(BIRTH, date(2032, 1, 1))
    for a, b in zip(short, long):
        assert (a.idx, a.start, a.end) == (b.idx, b.start, b.end)


def test_period_for_date():
    periods = generate_periods(BIRTH, date(2027, 1, 1))
    assert period_for_date(periods, BIRTH).idx == 0
    assert period_for_date(periods, date(2023, 8, 1)).idx == 1  # 3-6 miesiecy
    assert period_for_date(periods, date(2022, 1, 1)) is None   # przed urodzeniem
    assert period_for_date(periods, None) is None


# ── kosinus ──────────────────────────────────────────────────────────────────

def test_cosine_basics():
    assert cosine([1, 0], [1, 0]) == pytest.approx(1.0)
    assert cosine([1, 0], [0, 1]) == pytest.approx(0.0)
    assert cosine([1, 0], [-1, 0]) == pytest.approx(-1.0)


def test_cosine_of_different_dimensions_is_zero():
    # Embeddingi z roznych modeli nie sa porownywalne -- nie wolno ich "prawie" dopasowac.
    assert cosine([1, 0, 0], [1, 0]) == 0.0


# ── dopasowanie ──────────────────────────────────────────────────────────────

def test_match_uses_references_from_the_same_period():
    periods = generate_periods(BIRTH, date(2027, 1, 1))
    when = date(2025, 8, 1)
    target = period_for_date(periods, when)

    pool = [
        ref(1, rotated(0), period_idx=target.idx, capture=when),
        ref(2, rotated(5), period_idx=target.idx, capture=when),
        # Bardzo podobny wektor, ale z zupelnie innego okresu zycia.
        ref(3, rotated(1), period_idx=0, capture=BIRTH),
    ]
    result = match_face(rotated(2), pool, when=when, periods=periods, params=LOOSE)
    assert result.period_idx == target.idx
    assert result.used_refs == 2  # tylko okres docelowy (+/- 1), nie caly zbior
    assert result.is_match


def test_match_widens_to_neighbours_when_period_is_thin():
    periods = generate_periods(BIRTH, date(2027, 1, 1))
    when = date(2025, 8, 1)
    target = period_for_date(periods, when)
    pool = [
        ref(1, rotated(0), period_idx=target.idx - 1, capture=date(2025, 5, 1)),
        ref(2, rotated(3), period_idx=target.idx + 1, capture=date(2025, 11, 1)),
    ]
    result = match_face(rotated(1), pool, when=when, periods=periods, params=LOOSE)
    assert result.used_refs == 2
    assert not result.widened  # sasiedzi mieszcza sie w domyslnym neighbor_span


def test_thin_pool_raises_threshold_and_flags_uncertainty():
    periods = generate_periods(BIRTH, date(2027, 1, 1))
    when = date(2025, 8, 1)
    params = MatchParams(threshold=0.5, thin_pool_penalty=0.1, min_refs_per_period=3,
                         time_bonus=0.0, top_k=1)
    pool = [ref(1, rotated(0), period_idx=0, capture=BIRTH)]  # tylko odlegly okres

    result = match_face(rotated(0), pool, when=when, periods=periods, params=params)
    assert result.widened
    assert result.uncertain
    assert result.threshold == pytest.approx(0.6)  # 0.5 + kara za chuda pule


def test_empty_pool_never_matches():
    periods = generate_periods(BIRTH, date(2027, 1, 1))
    result = match_face(rotated(0), [], when=date(2025, 8, 1), periods=periods, params=LOOSE)
    assert not result.is_match
    assert result.uncertain
    assert result.used_refs == 0
    assert result.similarity == 0.0


def test_photo_from_period_without_references_is_conservative():
    """Zdjecie z okresu, ktorego wzorzec jeszcze nie zna, ma podniesiony prog."""
    periods = generate_periods(BIRTH, date(2027, 1, 1))
    params = MatchParams(threshold=0.5, thin_pool_penalty=0.1, min_refs_per_period=2,
                         time_bonus=0.0, top_k=1)
    pool = [
        ref(1, rotated(0), period_idx=0, capture=BIRTH),
        ref(2, rotated(2), period_idx=0, capture=BIRTH),
    ]
    known = match_face(rotated(1), pool, when=BIRTH, periods=periods, params=params)
    unknown = match_face(rotated(1), pool, when=date(2026, 6, 1), periods=periods, params=params)

    assert known.threshold < unknown.threshold
    assert not known.uncertain
    assert unknown.uncertain


def test_time_proximity_boosts_but_never_vetoes():
    periods = generate_periods(BIRTH, date(2027, 1, 1))
    when = date(2025, 8, 1)
    target = period_for_date(periods, when)
    params = MatchParams(threshold=0.1, min_refs_per_period=1, neighbor_span=1,
                         time_bonus=0.15, tau_months=6.0, top_k=1)

    near = [ref(1, rotated(0), period_idx=target.idx, capture=when)]
    far = [ref(1, rotated(0), period_idx=target.idx, capture=date(2024, 1, 1))]

    near_result = match_face(rotated(0), near, when=when, periods=periods, params=params)
    far_result = match_face(rotated(0), far, when=when, periods=periods, params=params)

    assert near_result.similarity > far_result.similarity
    # Odlegla w czasie referencja nadal potrafi dopasowac -- premia nie jest wetem.
    assert far_result.is_match


def test_top_k_resists_a_single_outlier_reference():
    """Jedna przypadkowo pasujaca referencja nie moze przepchnac obcej twarzy."""
    periods = generate_periods(BIRTH, date(2027, 1, 1))
    when = date(2025, 8, 1)
    target = period_for_date(periods, when)
    params = MatchParams(threshold=0.9, min_refs_per_period=1, time_bonus=0.0, top_k=3)

    pool = [
        ref(1, rotated(0), period_idx=target.idx, capture=when),    # trafia idealnie
        ref(2, rotated(80), period_idx=target.idx, capture=when),   # zupelnie inna
        ref(3, rotated(85), period_idx=target.idx, capture=when),
    ]
    result = match_face(rotated(0), pool, when=when, periods=periods, params=params)
    assert result.similarity < 1.0  # usredniamy z top-3, wiec nie ufamy jednemu trafieniu
    assert not result.is_match


def test_match_without_capture_date_uses_whole_pool():
    periods = generate_periods(BIRTH, date(2027, 1, 1))
    pool = [ref(1, rotated(0), period_idx=3, capture=date(2024, 1, 1))]
    result = match_face(rotated(0), pool, when=None, periods=periods, params=LOOSE)
    assert result.period_idx is None
    assert result.used_refs == 1


# ── anty-dryf ────────────────────────────────────────────────────────────────

def test_module_has_no_way_to_add_references():
    """Strukturalna bariera: automatyczne dopasowanie nie moze rozbudowac puli.

    Gdyby pula rosla o wlasne trafienia, jeden falszywy pozytyw przyciagnalby
    kolejne. Referencje dodaje wylacznie kalibracja albo zatwierdzenie w review.
    """
    import timemachine.identity as module

    suspicious = [
        name for name in dir(module)
        if any(word in name.lower() for word in ("add_ref", "insert", "save", "store", "commit"))
    ]
    assert suspicious == []


# ── roznorodnosc puli ────────────────────────────────────────────────────────

def test_select_diverse_keeps_spread_not_duplicates():
    # Trzy niemal identyczne wektory i dwa wyraznie inne.
    pool = [
        ref(1, rotated(0)), ref(2, rotated(1)), ref(3, rotated(2)),
        ref(4, rotated(60)), ref(5, rotated(120)),
    ]
    kept = {r.id for r in select_diverse(pool, 3)}
    assert 4 in kept and 5 in kept          # skrajnosci zostaja
    assert len(kept & {1, 2, 3}) == 1       # z kepy prawie identycznych zostaje jedna


def test_select_diverse_is_deterministic():
    pool = [ref(i, rotated(i * 17)) for i in range(1, 9)]
    first = [r.id for r in select_diverse(pool, 4)]
    second = [r.id for r in select_diverse(list(reversed(pool)), 4)]
    assert first == second


def test_select_diverse_returns_everything_when_under_limit():
    pool = [ref(1, rotated(0)), ref(2, rotated(30))]
    assert [r.id for r in select_diverse(pool, 5)] == [1, 2]


# ── podsumowanie puli ────────────────────────────────────────────────────────

def test_pool_summary_marks_thin_periods():
    periods = generate_periods(BIRTH, date(2024, 6, 1))
    pool = [ref(1, rotated(0), period_idx=0), ref(2, rotated(10), period_idx=0)]
    rows = pool_summary(periods, pool, min_refs=3)

    assert rows[0]["count"] == 2
    assert rows[0]["thin"] is True          # 2 < 3
    assert all(r["count"] == 0 for r in rows[1:])
    assert all(r["thin"] for r in rows[1:])  # puste okresy tez sa "chude"


def test_pool_summary_reports_references_without_period():
    periods = generate_periods(BIRTH, date(2024, 1, 1))
    rows = pool_summary(periods, [ref(9, rotated(0), period_idx=None)], min_refs=1)
    orphan = rows[-1]
    assert orphan["idx"] is None
    assert orphan["count"] == 1
