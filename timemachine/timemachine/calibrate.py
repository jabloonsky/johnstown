"""Budowanie i utrzymanie wielookresowej puli referencyjnej.

Referencje trafiaja do puli TYLKO dwiema droga:
  * `timemachine calibrate add ...` -- czlowiek wskazuje zdjecia palcem,
  * zatwierdzenie zdjecia w `timemachine review` (origin='review_confirmed').

Automatyczne dopasowanie NIGDY nie dokłada referencji. To celowa bariera: gdyby
pula rosla o wlasne trafienia, jeden falszywy pozytyw zaczalby przyciagac kolejne
i po kilku miesiacach wzorzec opisywalby cudze dziecko.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

from . import config, identity, images
from .analyze import load_periods, load_reference_pool, match_params
from .db import Database, pack_vector, utc_now
from .faces import DetectedFace, FaceEngine

__all__ = [
    "CalibrationResult",
    "ensure_periods",
    "add_references",
    "confirm_faces",
    "list_references",
    "remove_reference",
    "pool_status",
    "prune_pool",
    "AmbiguousFace",
]

ORIGIN_CALIBRATE = "calibrate"
ORIGIN_REVIEW = "review_confirmed"
_ALLOWED_ORIGINS = (ORIGIN_CALIBRATE, ORIGIN_REVIEW)


class AmbiguousFace(Exception):
    """Na zdjeciu referencyjnym jest wiecej niz jedna twarz i trzeba wskazac ktora."""

    def __init__(self, path: Path, faces: list[DetectedFace]):
        self.path = path
        self.faces = faces
        listing = "\n".join(
            f"    --face {i}  bbox={f.bbox}  rozmiar={f.bbox[2]}x{f.bbox[3]}  "
            f"pewnosc={f.det_score:.2f}"
            for i, f in enumerate(faces)
        )
        super().__init__(
            f"{path.name}: znaleziono {len(faces)} twarzy. Wskaz, ktora jest corki:\n{listing}\n"
            "    (albo dodaj --largest, zeby wziac najwieksza)"
        )


@dataclass
class CalibrationResult:
    added: int = 0
    skipped: int = 0
    errors: int = 0
    messages: list[str] = field(default_factory=list)
    deactivated: int = 0

    def note(self, text: str) -> None:
        self.messages.append(text)


# ── okresy ───────────────────────────────────────────────────────────────────


def ensure_periods(db: Database, cfg: config.Config, until: date | None = None) -> list[identity.Period]:
    """Generuje/uzupelnia okresy zycia i zapisuje je w bazie (idempotentnie)."""
    birth = cfg.birth_date
    horizon = until or date.today()
    latest = db.scalar("SELECT max(capture_ts) FROM frames")
    if latest:
        try:
            horizon = max(horizon, datetime.fromisoformat(latest).date())
        except (ValueError, TypeError):
            pass
    periods = identity.generate_periods(birth, horizon)
    with db.transaction():
        db.sync_periods(periods)
    return periods


def _period_id_for(db: Database, periods: list[identity.Period], when: date | None) -> int | None:
    period = identity.period_for_date(periods, when)
    if period is None:
        return None
    row = db.one("SELECT id FROM periods WHERE idx = ?", (period.idx,))
    return int(row["id"]) if row else None


# ── dodawanie referencji ─────────────────────────────────────────────────────


def _pick_face(path: Path, faces: list[DetectedFace], face_index: int | None, largest: bool) -> DetectedFace:
    if not faces:
        raise ValueError(f"{path.name}: nie znaleziono zadnej twarzy")
    if face_index is not None:
        if not 0 <= face_index < len(faces):
            raise ValueError(f"{path.name}: nie ma twarzy o numerze {face_index}")
        return faces[face_index]
    if len(faces) == 1 or largest:
        return faces[0]  # lista jest posortowana malejaco po powierzchni
    raise AmbiguousFace(path, faces)


def add_references(
    db: Database,
    cfg: config.Config,
    paths: list[Path],
    *,
    face_index: int | None = None,
    largest: bool = False,
    when: date | None = None,
    engine: FaceEngine | None = None,
) -> CalibrationResult:
    """Dodaje zdjecia referencyjne do puli, przypisujac je do okresow zycia."""
    result = CalibrationResult()
    if not paths:
        return result

    engine = engine or FaceEngine(
        cfg.faces.model,
        det_size=cfg.faces.det_size,
        providers=cfg.faces.providers,
        max_faces=cfg.faces.max_faces_per_frame,
    )
    periods = ensure_periods(db, cfg)

    for path in paths:
        kind = cfg.kind_of(path.suffix) or "jpg"
        try:
            decoded = images.load_rgb(path, kind, max_edge=cfg.faces.analysis_max_edge)
            faces = engine.detect(decoded.pixels)
            face = _pick_face(path, faces, face_index, largest)
        except AmbiguousFace as exc:
            result.errors += 1
            result.note(str(exc))
            continue
        except (images.UnsupportedImage, ValueError, OSError) as exc:
            result.errors += 1
            result.note(f"{path.name}: {exc}")
            continue

        if not face.embedding:
            result.errors += 1
            result.note(f"{path.name}: model nie zwrocil embeddingu")
            continue

        capture = when or _reference_date(path, kind)
        if capture is None:
            result.note(
                f"{path.name}: brak daty EXIF -- referencja nie trafi do zadnego okresu. "
                "Podaj --date YYYY-MM-DD, zeby przypisac ja do wlasciwego wieku."
            )

        existing = db.one(
            "SELECT id FROM refs WHERE source_path = ? AND embed_model = ? AND active = 1",
            (str(path), engine.embed_model),
        )
        if existing:
            result.skipped += 1
            result.note(f"{path.name}: juz jest w puli (id={existing['id']})")
            continue

        with db.transaction():
            db.execute(
                """
                INSERT INTO refs (period_id, source_path, embedding, embed_dim, embed_model,
                                  origin, capture_ts, active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
                """,
                (
                    _period_id_for(db, periods, capture),
                    str(path),
                    pack_vector(face.embedding),
                    len(face.embedding),
                    engine.embed_model,
                    ORIGIN_CALIBRATE,
                    capture.isoformat() if capture else None,
                    utc_now(),
                ),
            )
        result.added += 1

    result.deactivated = prune_pool(db, cfg, engine.embed_model)
    return result


def _reference_date(path: Path, kind: str) -> date | None:
    from .scanner import read_metadata  # noqa: PLC0415 - unikamy cyklu importow

    meta = read_metadata(path, kind)
    return meta.capture.date() if meta.capture else None


def confirm_faces(
    db: Database, cfg: config.Config, face_ids: list[int], *, embed_model: str
) -> int:
    """Dokłada do puli embeddingi twarzy potwierdzonych przez czlowieka w review.

    To jest mechanizm, dzieki ktoremu wzorzec sam rosnie o kolejne okresy zycia:
    kazdy zatwierdzony miesiac wnosi swiezy material referencyjny.
    """
    if not face_ids:
        return 0
    periods = ensure_periods(db, cfg)
    added = 0
    placeholders = ",".join("?" * len(face_ids))
    rows = db.query(
        f"""
        SELECT fa.id, fa.embedding, fa.embed_dim, fa.embed_model, fr.capture_ts, f.path
        FROM faces fa
        JOIN frames fr ON fr.id = fa.frame_id
        LEFT JOIN files f ON f.id = fr.primary_file_id
        WHERE fa.id IN ({placeholders}) AND fa.embed_model = ?
        """,
        (*face_ids, embed_model),
    )
    with db.transaction():
        for row in rows:
            if db.one("SELECT id FROM refs WHERE face_id = ?", (row["id"],)):
                continue
            capture = None
            if row["capture_ts"]:
                try:
                    capture = datetime.fromisoformat(row["capture_ts"]).date()
                except ValueError:
                    capture = None
            db.execute(
                """
                INSERT INTO refs (period_id, face_id, source_path, embedding, embed_dim,
                                  embed_model, origin, capture_ts, active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                """,
                (
                    _period_id_for(db, periods, capture),
                    row["id"],
                    row["path"],
                    row["embedding"],
                    row["embed_dim"],
                    row["embed_model"],
                    ORIGIN_REVIEW,
                    capture.isoformat() if capture else None,
                    utc_now(),
                ),
            )
            added += 1
    prune_pool(db, cfg, embed_model)
    return added


# ── utrzymanie puli ──────────────────────────────────────────────────────────


def prune_pool(db: Database, cfg: config.Config, embed_model: str) -> int:
    """Przycina przepelnione okresy, zostawiajac najbardziej roznorodne referencje.

    Wylaczone referencje sa oznaczane active=0, nie kasowane -- decyzja jest
    odwracalna, a historia kalibracji zostaje.
    """
    limit = cfg.identity.max_refs_per_period
    deactivated = 0
    rows = db.query(
        "SELECT p.idx, count(*) AS n FROM refs r JOIN periods p ON p.id = r.period_id "
        "WHERE r.active = 1 AND r.embed_model = ? GROUP BY p.idx HAVING n > ?",
        (embed_model, limit),
    )
    if not rows:
        return 0

    pool = load_reference_pool(db, embed_model)
    with db.transaction():
        for row in rows:
            in_period = [r for r in pool if r.period_idx == int(row["idx"])]
            keep = {r.id for r in identity.select_diverse(in_period, limit)}
            for ref in in_period:
                if ref.id not in keep:
                    db.execute("UPDATE refs SET active = 0 WHERE id = ?", (ref.id,))
                    deactivated += 1
    return deactivated


def list_references(db: Database, *, include_inactive: bool = False) -> list:
    condition = "" if include_inactive else "WHERE r.active = 1"
    return db.query(
        f"""
        SELECT r.id, r.source_path, r.origin, r.capture_ts, r.active, r.embed_model,
               p.idx AS period_idx, p.label AS period_label
        FROM refs r LEFT JOIN periods p ON p.id = r.period_id
        {condition}
        ORDER BY p.idx IS NULL, p.idx, r.id
        """
    )


def remove_reference(db: Database, ref_id: int) -> bool:
    row = db.one("SELECT id FROM refs WHERE id = ?", (ref_id,))
    if not row:
        return False
    with db.transaction():
        db.execute("UPDATE refs SET active = 0 WHERE id = ?", (ref_id,))
    return True


def pool_status(db: Database, cfg: config.Config) -> list[dict]:
    """Rozklad referencji po okresach -- pokazuje dziury we wzorcu."""
    periods = load_periods(db)
    if not periods:
        periods = ensure_periods(db, cfg)
    refs = load_reference_pool(db, cfg.faces.model)
    return identity.pool_summary(periods, refs, cfg.identity.min_refs_per_period)


def describe_match_params(cfg: config.Config) -> identity.MatchParams:
    return match_params(cfg)
