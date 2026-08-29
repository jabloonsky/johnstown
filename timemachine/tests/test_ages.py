"""Testy arytmetyki dat i polskiej odmiany wieku -- funkcje czyste, bez I/O."""
from datetime import date

import pytest

from timemachine.ages import (
    add_months,
    age_for_month,
    age_parts,
    format_age_pl,
    month_bounds,
    months_between,
    plural_pl,
)

BIRTH = date(2023, 4, 12)


# ── plural_pl ────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "n,expected",
    [(1, "rok"), (2, "lata"), (3, "lata"), (4, "lata"), (5, "lat"), (11, "lat"),
     (12, "lat"), (13, "lat"), (14, "lat"), (22, "lata"), (25, "lat"), (0, "lat")],
)
def test_plural_years(n, expected):
    assert plural_pl(n, "rok", "lata", "lat") == expected


@pytest.mark.parametrize(
    "n,expected",
    [(1, "miesiac"), (2, "miesiace"), (4, "miesiace"), (5, "miesiecy"),
     (11, "miesiecy"), (12, "miesiecy")],
)
def test_plural_months(n, expected):
    assert plural_pl(n, "miesiac", "miesiace", "miesiecy") == expected


# ── add_months ───────────────────────────────────────────────────────────────

def test_add_months_clamps_to_shorter_month():
    assert add_months(date(2023, 1, 31), 1) == date(2023, 2, 28)
    assert add_months(date(2024, 1, 31), 1) == date(2024, 2, 29)  # rok przestepny


def test_add_months_crosses_year():
    assert add_months(date(2023, 11, 15), 3) == date(2024, 2, 15)
    assert add_months(date(2023, 4, 12), 36) == date(2026, 4, 12)


# ── months_between ───────────────────────────────────────────────────────────

def test_months_between_counts_full_months_only():
    assert months_between(date(2023, 1, 15), date(2023, 2, 14)) == 0
    assert months_between(date(2023, 1, 15), date(2023, 2, 15)) == 1
    assert months_between(date(2023, 1, 15), date(2024, 1, 15)) == 12


def test_months_between_is_negative_backwards():
    assert months_between(date(2023, 3, 15), date(2023, 1, 20)) == -1


# ── age_parts ────────────────────────────────────────────────────────────────

def test_age_parts_borrows_days_from_previous_month():
    assert age_parts(BIRTH, date(2023, 5, 10)) == (0, 0, 28)
    assert age_parts(BIRTH, date(2025, 8, 12)) == (2, 4, 0)


def test_age_parts_before_birth_is_zero():
    assert age_parts(BIRTH, date(2023, 1, 1)) == (0, 0, 0)


# ── format_age_pl ────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "on,expected",
    [
        (date(2023, 4, 12), "dzien urodzenia"),
        (date(2023, 4, 13), "1 dzien"),
        (date(2023, 4, 15), "3 dni"),
        (date(2023, 4, 26), "2 tygodnie"),
        (date(2023, 5, 10), "4 tygodnie"),
        (date(2023, 5, 12), "1 miesiac"),
        (date(2023, 7, 12), "3 miesiace"),
        (date(2023, 11, 12), "7 miesiecy"),
        (date(2024, 4, 12), "1 rok"),
        (date(2024, 5, 12), "1 rok i 1 miesiac"),
        (date(2025, 8, 12), "2 lata i 4 miesiace"),
        (date(2026, 4, 12), "3 lata"),
        (date(2028, 6, 12), "5 lat i 2 miesiace"),
        (date(2031, 4, 12), "8 lat"),
    ],
)
def test_format_age_pl(on, expected):
    assert format_age_pl(BIRTH, on) == expected


def test_format_age_before_birth():
    assert format_age_pl(BIRTH, date(2022, 12, 1)) == "przed urodzeniem"


# ── month_bounds / age_for_month ─────────────────────────────────────────────

def test_month_bounds():
    assert month_bounds("2024-02") == (date(2024, 2, 1), date(2024, 2, 29))
    assert month_bounds("2023-12") == (date(2023, 12, 1), date(2023, 12, 31))


def test_month_bounds_rejects_garbage():
    with pytest.raises(ValueError):
        month_bounds("2024/02")


def test_age_for_month_uses_midpoint():
    # 15 sierpnia 2025 to 2 lata i 4 miesiace od 12 kwietnia 2023.
    assert age_for_month(BIRTH, "2025-08") == "2 lata i 4 miesiace"


def test_age_for_month_of_birth_uses_midpoint_when_already_born():
    # Urodziny 12 kwietnia: 15 kwietnia dziecko ma juz 3 dni.
    assert age_for_month(BIRTH, "2023-04") == "3 dni"


def test_age_for_month_falls_back_to_last_day_when_born_after_midpoint():
    # Urodziny 20 kwietnia: polowa miesiaca wypada przed urodzeniem, wiec
    # naglowek pokazuje wiek na koniec miesiaca zamiast "przed urodzeniem".
    late = date(2023, 4, 20)
    assert age_for_month(late, "2023-04") == "1 tydzien"


def test_age_for_month_before_birth_is_none():
    assert age_for_month(BIRTH, "2023-01") is None
