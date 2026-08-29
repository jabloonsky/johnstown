"""Wielookresowy wzorzec twarzy dziecka.

Twarz dziecka zmienia sie z wiekiem szybciej niz jakikolwiek pojedynczy wzorzec
jest w stanie opisac. Dlatego:

  * pula referencyjna jest podzielona na OKRESY ZYCIA i kazdy embedding zyje w
    niej OSOBNO -- nigdy nie usredniamy referencji do jednego prototypu;
  * dopasowanie zdjecia z chwili `t` siega po referencje z okresu `p(t)` oraz
    okresow sasiednich, z lagodna premia za bliskosc w czasie;
  * gdy w danym okresie referencji jest za malo, prog jest PODNOSZONY, a klatka
    oznaczana jako niepewna -- przy niepewnosci wolimy przeoczyc wlasne zdjecie
    niz wpuscic na os czasu obce dziecko;
  * pula rosnie wylacznie z kalibracji i z zatwierdzen w `review`. Ten modul jest
    czysty (bez wejscia/wyjscia) i celowo NIE MA funkcji dodajacej referencje na
    podstawie automatycznego dopasowania -- to strukturalna bariera przed dryfem.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Iterable, Sequence

from .ages import add_months, months_between, plural_pl

__all__ = [
    "Period",
    "Reference",
    "MatchResult",
    "MatchParams",
    "generate_periods",
    "period_for_date",
    "match_face",
    "select_diverse",
    "pool_summary",
    "cosine",
    "l2_normalize",
]

# Dlugosci okresow w miesiacach: im mlodsze dziecko, tym szybciej zmienia sie twarz.
_SEGMENTS: tuple[tuple[int, int, int], ...] = (
    # (od miesiaca, do miesiaca, dlugosc segmentu)
    (0, 36, 3),      # pierwsze trzy lata -- kwartalnie
    (36, 72, 6),     # 3-6 lat -- co pol roku
    (72, 10_000, 12),  # dalej -- rocznie
)

_ONE_DAY = timedelta(days=1)


@dataclass(frozen=True)
class Period:
    """Okres zycia dziecka, do ktorego przypisywane sa referencje."""

    idx: int
    label: str
    start: date
    end: date  # wlacznie
    start_month: int  # wiek w miesiacach na poczatku okresu

    def contains(self, when: date) -> bool:
        return self.start <= when <= self.end


@dataclass(frozen=True)
class Reference:
    """Pojedynczy embedding referencyjny z puli."""

    id: int
    embedding: Sequence[float]
    period_idx: int | None = None
    capture: date | None = None
    origin: str = "calibrate"


@dataclass(frozen=True)
class MatchParams:
    threshold: float = 0.38
    thin_pool_penalty: float = 0.03
    min_refs_per_period: int = 3
    neighbor_span: int = 1
    tau_months: float = 6.0
    time_bonus: float = 0.15
    top_k: int = 3


@dataclass(frozen=True)
class MatchResult:
    similarity: float
    threshold: float
    is_match: bool
    period_idx: int | None
    uncertain: bool
    used_refs: int
    widened: bool  # trzeba bylo siegnac poza skonfigurowane sasiedztwo

    @property
    def margin(self) -> float:
        return self.similarity - self.threshold


# ── okresy ───────────────────────────────────────────────────────────────────


def _age_label(months: int) -> str:
    years, rest = divmod(months, 12)
    if years == 0:
        return f"{rest} mies."
    years_text = f"{years} {plural_pl(years, 'rok', 'lata', 'lat')}"
    if rest == 0:
        return years_text
    return f"{years_text} {rest} mies."


def generate_periods(birth: date, until: date) -> list[Period]:
    """Okresy zycia od urodzenia do (co najmniej) `until`.

    Zwraca liste w kolejnosci chronologicznej; `idx` jest stabilny miedzy
    uruchomieniami, wiec referencje przypisane do okresu nie "wedruja", gdy
    archiwum obejmie nowsze zdjecia.
    """
    horizon = max(months_between(birth, until), 0) + 1
    periods: list[Period] = []
    month = 0
    idx = 0
    while month <= horizon:
        length = next(step for lo, hi, step in _SEGMENTS if lo <= month < hi)
        end_month = month + length
        start = add_months(birth, month)
        end = add_months(birth, end_month)
        periods.append(
            Period(
                idx=idx,
                label=f"{_age_label(month)} - {_age_label(end_month)}",
                start=start,
                end=end - _ONE_DAY,
                start_month=month,
            )
        )
        month = end_month
        idx += 1
    return periods


def period_for_date(periods: Sequence[Period], when: date | None) -> Period | None:
    """Okres, w ktorym wypada `when`. None przed urodzeniem lub przy braku daty."""
    if when is None or not periods:
        return None
    if when < periods[0].start:
        return None
    for period in periods:
        if period.contains(when):
            return period
    return periods[-1] if when > periods[-1].end else None


# ── wektory ──────────────────────────────────────────────────────────────────


def l2_normalize(vector: Sequence[float]) -> list[float]:
    norm = math.sqrt(sum(v * v for v in vector))
    if norm == 0.0:
        return [0.0] * len(vector)
    return [v / norm for v in vector]


def cosine(a: Sequence[float], b: Sequence[float]) -> float:
    """Podobienstwo kosinusowe. Rozne dlugosci -> 0.0 (rozne modele embeddingow)."""
    if len(a) != len(b) or not a:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


# ── dopasowanie ──────────────────────────────────────────────────────────────


def _time_factor(ref: Reference, when: date | None, params: MatchParams) -> float:
    """Lagodna premia za bliskosc w czasie: w <0,1> przeskalowane do <1-b, 1>.

    Referencja bez daty dostaje wartosc srodkowa -- nie jest karana, ale tez nie
    wygrywa z referencja zrobiona w tym samym miesiacu.
    """
    if when is None or ref.capture is None:
        weight = 0.5
    else:
        delta = abs(months_between(ref.capture, when))
        weight = math.exp(-delta / params.tau_months) if params.tau_months > 0 else 0.0
    return (1.0 - params.time_bonus) + params.time_bonus * weight


def _refs_within(refs: Sequence[Reference], center: int | None, span: int) -> list[Reference]:
    if center is None:
        return list(refs)
    return [r for r in refs if r.period_idx is not None and abs(r.period_idx - center) <= span]


def match_face(
    embedding: Sequence[float],
    refs: Sequence[Reference],
    *,
    when: date | None,
    periods: Sequence[Period],
    params: MatchParams,
) -> MatchResult:
    """Dopasowuje twarz do puli referencyjnej wlasciwej dla jej wieku.

    Kolejnosc: okres +/- neighbor_span -> poszerzanie sasiedztwa -> cala pula.
    Kazde poszerzenie oznacza wieksza niepewnosc, wiec podnosi prog.
    """
    period = period_for_date(periods, when)
    center = period.idx if period else None

    pool = _refs_within(refs, center, params.neighbor_span)
    widened = False
    if len(pool) < params.min_refs_per_period and center is not None:
        for span in range(params.neighbor_span + 1, params.neighbor_span + 4):
            wider = _refs_within(refs, center, span)
            if len(wider) > len(pool):
                pool, widened = wider, True
            if len(pool) >= params.min_refs_per_period:
                break
        if len(pool) < params.min_refs_per_period and len(refs) > len(pool):
            pool, widened = list(refs), True

    thin = widened or len(pool) < params.min_refs_per_period
    threshold = params.threshold + (params.thin_pool_penalty if thin else 0.0)

    if not pool or not embedding:
        return MatchResult(0.0, threshold, False, center, True, 0, widened)

    adjusted = sorted(
        (cosine(embedding, ref.embedding) * _time_factor(ref, when, params) for ref in pool),
        reverse=True,
    )
    top_k = adjusted[: max(1, params.top_k)]
    similarity = 0.5 * adjusted[0] + 0.5 * (sum(top_k) / len(top_k))

    return MatchResult(
        similarity=similarity,
        threshold=threshold,
        is_match=similarity >= threshold,
        period_idx=center,
        uncertain=thin,
        used_refs=len(pool),
        widened=widened,
    )


# ── utrzymanie puli ──────────────────────────────────────────────────────────


def select_diverse(refs: Sequence[Reference], keep: int) -> list[Reference]:
    """Wybiera `keep` najbardziej roznorodnych referencji (zachlanne max-min).

    Gdy okres przekroczy limit, zostawiamy referencje pokrywajace rozne pozy i
    swiatlo, a nie po prostu najnowsze -- inaczej pula zwezalaby sie do ostatniej
    sesji zdjeciowej i przestala rozpoznawac dziecko w innych warunkach.
    """
    if keep <= 0:
        return []
    if len(refs) <= keep:
        return list(refs)

    items = list(refs)
    sims = [[cosine(a.embedding, b.embedding) for b in items] for a in items]

    # Ziarno: najbardziej "srodkowa" referencja -- deterministyczne i sensowne.
    seed = min(
        range(len(items)),
        key=lambda i: (-sum(sims[i]) / len(items), items[i].id),
    )
    chosen = [seed]
    remaining = {i for i in range(len(items)) if i != seed}

    while len(chosen) < keep and remaining:
        best = min(
            remaining,
            key=lambda i: (max(sims[i][c] for c in chosen), items[i].id),
        )
        chosen.append(best)
        remaining.discard(best)

    return [items[i] for i in sorted(chosen, key=lambda i: items[i].id)]


def pool_summary(
    periods: Sequence[Period], refs: Iterable[Reference], min_refs: int
) -> list[dict]:
    """Rozklad referencji po okresach -- zrodlo dla `timemachine calibrate --status`."""
    counts: dict[int | None, int] = {}
    origins: dict[int | None, set[str]] = {}
    for ref in refs:
        counts[ref.period_idx] = counts.get(ref.period_idx, 0) + 1
        origins.setdefault(ref.period_idx, set()).add(ref.origin)

    rows = []
    for period in periods:
        count = counts.get(period.idx, 0)
        rows.append(
            {
                "idx": period.idx,
                "label": period.label,
                "start": period.start,
                "end": period.end,
                "count": count,
                "thin": count < min_refs,
                "origins": sorted(origins.get(period.idx, set())),
            }
        )
    orphans = counts.get(None, 0)
    if orphans:
        rows.append(
            {
                "idx": None,
                "label": "bez przypisanego okresu",
                "start": None,
                "end": None,
                "count": orphans,
                "thin": False,
                "origins": sorted(origins.get(None, set())),
            }
        )
    return rows
