"""Faza B indeksowania: piksele, twarze, embeddingi, metryki jakosci.

Kosztowna czesc pracy. Pracuje wylacznie po klatkach, ktore skaner oznaczyl jako
niezanalizowane, i zapisuje wyniki paczkami -- przerwanie kosztuje najwyzej
biezaca paczke, a ponowne uruchomienie podejmuje prace w tym samym miejscu.

Kazda klatka jest dekodowana DOKLADNIE RAZ i od razu liczone sa wszystkie
metryki (ostrosc, ekspozycja, oczy, usmiech, dopasowanie tozsamosci). Powtorne
czytanie dziesiatek tysiecy RAW-ow z dysku zewnetrznego jest dokladnie tym, czego
chcemy uniknac.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from . import config, identity, images, quality
from .db import Database, pack_vector, unpack_vector, utc_now
from .faces import DetectedFace, FaceEngine
from .progress import Progress
from .scanner import _InterruptGuard

__all__ = ["AnalyzeStats", "analyze_pending", "load_reference_pool", "load_periods"]

_BATCH = 20


@dataclass
class AnalyzeStats:
    frames: int = 0
    faces: int = 0
    subjects: int = 0
    uncertain: int = 0
    skipped: int = 0
    errors: int = 0
    interrupted: bool = False

    def summary(self) -> str:
        return (
            f"klatek przeanalizowanych: {self.frames}  twarzy: {self.faces}  "
            f"twarzy corki: {self.subjects}  niepewnych: {self.uncertain}\n"
            f"pominietych (brak podgladu): {self.skipped}  bledow: {self.errors}"
        )


# ── dane referencyjne ────────────────────────────────────────────────────────


def load_periods(db: Database) -> list[identity.Period]:
    rows = db.query("SELECT idx, label, start_date, end_date FROM periods ORDER BY idx")
    return [
        identity.Period(
            idx=int(r["idx"]),
            label=r["label"],
            start=date.fromisoformat(r["start_date"]),
            end=date.fromisoformat(r["end_date"]),
            start_month=0,
        )
        for r in rows
    ]


def load_reference_pool(db: Database, embed_model: str) -> list[identity.Reference]:
    """Aktywne referencje dla danego modelu embeddingow.

    Filtr po modelu jest istotny: embeddingi z roznych modeli nie sa
    porownywalne, wiec zmiana modelu w configu nie miesza starych referencji z
    nowymi.
    """
    rows = db.query(
        """
        SELECT r.id, r.embedding, r.capture_ts, r.origin, p.idx AS period_idx
        FROM refs r LEFT JOIN periods p ON p.id = r.period_id
        WHERE r.active = 1 AND r.embed_model = ?
        """,
        (embed_model,),
    )
    pool = []
    for row in rows:
        capture = None
        if row["capture_ts"]:
            try:
                capture = datetime.fromisoformat(row["capture_ts"]).date()
            except ValueError:
                capture = None
        pool.append(
            identity.Reference(
                id=int(row["id"]),
                embedding=unpack_vector(row["embedding"]),
                period_idx=int(row["period_idx"]) if row["period_idx"] is not None else None,
                capture=capture,
                origin=row["origin"],
            )
        )
    return pool


def match_params(cfg: config.Config) -> identity.MatchParams:
    ident = cfg.identity
    return identity.MatchParams(
        threshold=ident.threshold,
        thin_pool_penalty=ident.thin_pool_penalty,
        min_refs_per_period=ident.min_refs_per_period,
        neighbor_span=ident.neighbor_span,
        tau_months=ident.tau_months,
        time_bonus=ident.time_bonus,
        top_k=ident.top_k,
    )


# ── metryki jednej twarzy ────────────────────────────────────────────────────


def measure_face(gray, face: DetectedFace, frame_area: int) -> dict:
    """Wszystkie metryki liczone na cropie twarzy przeskalowanym do 128x128."""
    crop = quality.crop_face(gray, face.bbox)
    canonical = quality.resize_gray(crop, quality.CROP_SIZE)
    exposure = quality.exposure_stats(canonical)

    eye_open = None
    if len(face.keypoints) >= 2:
        left, right = face.keypoints[0], face.keypoints[1]
        interocular = ((left[0] - right[0]) ** 2 + (left[1] - right[1]) ** 2) ** 0.5
        if interocular > 0:
            radius = max(interocular * 0.18, 2.0)
            eye_open = (
                quality.eye_openness_from_pixels(gray, left, radius)
                + quality.eye_openness_from_pixels(gray, right, radius)
            ) / 2.0

    smile = _smile_proxy(face)

    return {
        "sharpness": quality.laplacian_variance(canonical),
        "exposure_mean": exposure.mean,
        "exposure_clip_low": exposure.clip_low,
        "exposure_clip_high": exposure.clip_high,
        "eye_open": eye_open,
        "smile": smile,
        "face_ratio": (face.area / frame_area) if frame_area else 0.0,
    }


def _smile_proxy(face: DetectedFace) -> float | None:
    """Przyblizenie usmiechu z 5 punktow: szerokosc ust wzgledem rozstawu oczu.

    To heurystyka, nie pomiar. Dlatego usmiech jest wylacznie PREMIA i mozna go
    calkiem wylaczyc, ustawiajac [scoring].smile_bonus = 0.
    """
    if len(face.keypoints) < 5:
        return None
    left_eye, right_eye = face.keypoints[0], face.keypoints[1]
    left_mouth, right_mouth = face.keypoints[3], face.keypoints[4]
    interocular = ((left_eye[0] - right_eye[0]) ** 2 + (left_eye[1] - right_eye[1]) ** 2) ** 0.5
    if interocular <= 0:
        return None
    mouth = ((left_mouth[0] - right_mouth[0]) ** 2 + (left_mouth[1] - right_mouth[1]) ** 2) ** 0.5
    ratio = mouth / interocular
    # ~0.80 to usta neutralne, ~1.05 to wyrazny usmiech.
    return max(0.0, min((ratio - 0.80) / 0.25, 1.0))


# ── przebieg ─────────────────────────────────────────────────────────────────


def _pending_frames(db: Database, limit: int | None, reanalyze: bool) -> list:
    clauses = ["f.status != 'missing'"]
    if not reanalyze:
        clauses.append("fr.analyzed_at IS NULL")
    sql = (
        "SELECT fr.id AS frame_id, fr.capture_ts, f.id AS file_id, f.path, f.kind "
        "FROM frames fr JOIN files f ON f.id = fr.primary_file_id "
        f"WHERE {' AND '.join(clauses)} ORDER BY fr.id"
    )
    if limit:
        sql += f" LIMIT {int(limit)}"
    return db.query(sql)


def analyze_pending(
    db: Database,
    cfg: config.Config,
    *,
    limit: int | None = None,
    reanalyze: bool = False,
    show_progress: bool = True,
    engine: FaceEngine | None = None,
) -> AnalyzeStats:
    """Analizuje klatki bez wynikow. Wznawialne i bezpieczne dla Ctrl-C."""
    stats = AnalyzeStats()
    rows = _pending_frames(db, limit, reanalyze)
    if not rows:
        return stats

    engine = engine or FaceEngine(
        cfg.faces.model,
        det_size=cfg.faces.det_size,
        providers=cfg.faces.providers,
        max_faces=cfg.faces.max_faces_per_frame,
    )
    periods = load_periods(db)
    period_ids = {
        int(r["idx"]): int(r["id"]) for r in db.query("SELECT id, idx FROM periods")
    }
    refs = load_reference_pool(db, engine.embed_model)
    params = match_params(cfg)
    min_det = cfg.faces.min_det_score

    if not refs:
        print(
            "Uwaga: pula referencyjna jest pusta -- twarze zostana zapisane, ale zadna "
            "nie zostanie uznana za corke. Uruchom `timemachine calibrate add ...`.",
            flush=True,
        )

    progress = Progress(len(rows), "analiza", enabled=show_progress)
    batch: list = []

    def flush(items: list) -> None:
        if not items:
            return
        with db.transaction():
            for row in items:
                _analyze_frame(
                    db, cfg, engine, row, periods, period_ids, refs, params, min_det, stats
                )
        items.clear()

    with _InterruptGuard() as guard:
        for row in rows:
            batch.append(row)
            progress.advance(note=Path(row["path"]).name[:40])
            if len(batch) >= _BATCH:
                flush(batch)
                if guard.requested:
                    stats.interrupted = True
                    break
        if not stats.interrupted:
            flush(batch)
    progress.finish()
    return stats


def _analyze_frame(
    db: Database,
    cfg: config.Config,
    engine: FaceEngine,
    row,
    periods: list[identity.Period],
    period_ids: dict[int, int],
    refs: list[identity.Reference],
    params: identity.MatchParams,
    min_det: float,
    stats: AnalyzeStats,
) -> None:
    frame_id = int(row["frame_id"])
    path = Path(row["path"])

    try:
        decoded = images.load_rgb(path, row["kind"], max_edge=cfg.faces.analysis_max_edge)
    except images.UnsupportedImage as exc:
        db.execute("UPDATE files SET status = 'skipped', error = ? WHERE id = ?",
                   (str(exc), row["file_id"]))
        db.execute("UPDATE frames SET analyzed_at = ?, face_count = 0 WHERE id = ?",
                   (utc_now(), frame_id))
        db.log("warn", "skipped_no_preview", str(path), str(exc))
        stats.skipped += 1
        return
    except (OSError, ValueError) as exc:
        db.execute("UPDATE files SET status = 'error', error = ? WHERE id = ?",
                   (str(exc), row["file_id"]))
        db.log("error", "decode_failed", str(path), str(exc))
        stats.errors += 1
        return

    detected = engine.detect(decoded.pixels)
    gray = quality.to_gray(decoded.pixels)
    frame_area = decoded.width * decoded.height
    when = _capture_date(row["capture_ts"])

    db.execute("DELETE FROM faces WHERE frame_id = ?", (frame_id,))

    subjects = 0
    uncertain = 0
    for face in detected:
        if face.det_score < min_det:
            continue
        metrics = measure_face(gray, face, frame_area)
        result = identity.match_face(
            face.embedding, refs, when=when, periods=periods, params=params
        )
        if result.is_match:
            subjects += 1
        if result.uncertain and result.similarity > 0:
            uncertain += 1

        db.execute(
            """
            INSERT INTO faces (
                frame_id, bbox_x, bbox_y, bbox_w, bbox_h, det_score, embedding,
                embed_dim, embed_model, landmarks, sharpness, exposure_mean,
                exposure_clip_low, exposure_clip_high, eye_open, smile, face_ratio,
                match_sim, match_period_id, is_subject, identity_uncertain, pose_yaw, pose_pitch
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                frame_id, *face.bbox, face.det_score,
                pack_vector(face.embedding), len(face.embedding), engine.embed_model,
                pack_vector([c for point in face.keypoints for c in point]),
                metrics["sharpness"], metrics["exposure_mean"], metrics["exposure_clip_low"],
                metrics["exposure_clip_high"], metrics["eye_open"], metrics["smile"],
                metrics["face_ratio"], result.similarity,
                period_ids.get(result.period_idx) if result.period_idx is not None else None,
                int(result.is_match), int(result.uncertain), face.yaw, face.pitch,
            ),
        )
        stats.faces += 1

    db.execute(
        "UPDATE frames SET analyzed_at = ?, face_count = ?, subject_count = ?, "
        "preview_source = ? WHERE id = ?",
        (utc_now(), len(detected), subjects, decoded.source, frame_id),
    )
    db.execute("UPDATE files SET status = 'indexed', indexed_at = ?, error = NULL WHERE id = ?",
               (utc_now(), row["file_id"]))
    stats.frames += 1
    stats.subjects += subjects
    stats.uncertain += uncertain


def _capture_date(value) -> date | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).date()
    except (ValueError, TypeError):
        return None
