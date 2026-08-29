"""Arytmetyka dat i polska odmiana wieku.

Modul czysty -- tylko biblioteka standardowa, zero wejscia/wyjscia. Polska
odmiana ("1 rok", "2 lata", "5 lat", "1 miesiac", "3 miesiace", "7 miesiecy")
jest wydzielona i przetestowana, bo to klasyczne miejsce na cichy blad.
"""
from __future__ import annotations

import calendar
from datetime import date

__all__ = [
    "add_months",
    "months_between",
    "age_parts",
    "format_age_pl",
    "age_for_month",
    "month_bounds",
    "plural_pl",
]


def plural_pl(n: int, one: str, few: str, many: str) -> str:
    """Polska liczba mnoga: 1 -> one, 2-4 (poza 12-14) -> few, reszta -> many."""
    n = abs(n)
    if n == 1:
        return one
    last, last_two = n % 10, n % 100
    if 2 <= last <= 4 and not 12 <= last_two <= 14:
        return few
    return many


def _days_in_month(year: int, month: int) -> int:
    return calendar.monthrange(year, month)[1]


def add_months(start: date, months: int) -> date:
    """Przesuwa date o `months` miesiecy, przycinajac dzien do dlugosci miesiaca.

    31 stycznia + 1 miesiac = 28/29 lutego -- tak liczy sie wiek potocznie.
    """
    total = (start.year * 12 + (start.month - 1)) + months
    year, month = divmod(total, 12)
    month += 1
    return date(year, month, min(start.day, _days_in_month(year, month)))


def months_between(start: date, end: date) -> int:
    """Liczba pelnych miesiecy miedzy datami (ujemna, gdy `end` jest wczesniej)."""
    months = (end.year - start.year) * 12 + (end.month - start.month)
    if end >= start:
        if end.day < min(start.day, _days_in_month(end.year, end.month)):
            months -= 1
    elif end.day > min(start.day, _days_in_month(end.year, end.month)):
        months += 1
    return months


def age_parts(birth: date, on: date) -> tuple[int, int, int]:
    """(lata, miesiace, dni) ukonczone w dniu `on`. Przed urodzeniem: same zera."""
    if on < birth:
        return (0, 0, 0)
    years = on.year - birth.year
    months = on.month - birth.month
    days = on.day - birth.day
    if days < 0:
        months -= 1
        prev_month = on.month - 1 or 12
        prev_year = on.year if on.month > 1 else on.year - 1
        days += _days_in_month(prev_year, prev_month)
    if months < 0:
        years -= 1
        months += 12
    return (years, months, days)


def format_age_pl(birth: date, on: date) -> str:
    """Wiek po polsku, np. "2 lata i 4 miesiace", "7 miesiecy", "3 tygodnie"."""
    if on < birth:
        return "przed urodzeniem"

    years, months, days = age_parts(birth, on)

    if years == 0 and months == 0:
        if days == 0:
            return "dzien urodzenia"
        if days < 7:
            return f"{days} {plural_pl(days, 'dzien', 'dni', 'dni')}"
        weeks = days // 7
        return f"{weeks} {plural_pl(weeks, 'tydzien', 'tygodnie', 'tygodni')}"

    if years == 0:
        return f"{months} {plural_pl(months, 'miesiac', 'miesiace', 'miesiecy')}"

    years_text = f"{years} {plural_pl(years, 'rok', 'lata', 'lat')}"
    if months == 0:
        return years_text
    months_text = f"{months} {plural_pl(months, 'miesiac', 'miesiace', 'miesiecy')}"
    return f"{years_text} i {months_text}"


def month_bounds(month: str) -> tuple[date, date]:
    """'YYYY-MM' -> (pierwszy dzien, ostatni dzien)."""
    try:
        year_text, month_text = month.split("-")
        year, mon = int(year_text), int(month_text)
        first = date(year, mon, 1)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"Nieprawidlowy miesiac {month!r}, oczekiwano formatu YYYY-MM") from exc
    return first, date(year, mon, _days_in_month(year, mon))


def age_for_month(birth: date, month: str) -> str | None:
    """Wiek do naglowka miesiaca na osi czasu.

    Liczony w polowie miesiaca (reprezentatywnie dla calego miesiaca); jesli
    dziecko urodzilo sie w trakcie tego miesiaca, w jego ostatnim dniu.
    Zwraca None dla miesiecy sprzed urodzenia -- naglowek po prostu nie ma wieku.
    """
    first, last = month_bounds(month)
    if last < birth:
        return None
    midpoint = date(first.year, first.month, 15)
    reference = midpoint if midpoint >= birth else last
    return format_age_pl(birth, reference)
