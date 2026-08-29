"""Warstwa SQLite: schemat, migracje i bezpieczne, wznawialne transakcje.

Zalozenia:
  * WAL + synchronous=NORMAL -- przerwanie (Ctrl-C, a nawet kill -9) nie psuje bazy.
  * Kazda paczka plikow zapisywana w osobnej transakcji, wiec ponowny `index`
    wznawia prace od miejsca, w ktorym poprzedni przebieg zostal przerwany.
  * Embeddingi trzymane jako BLOB float32 (array('f')) -- 2 KB na twarz, bez
    zadnych zewnetrznych indeksow wektorowych.
"""
from __future__ import annotations

import sqlite3
import sys
from array import array
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator, Sequence

from . import config

__all__ = ["connect", "Database", "SCHEMA_VERSION", "pack_vector", "unpack_vector", "utc_now"]

SCHEMA_VERSION = 1


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def pack_vector(values: Sequence[float]) -> bytes:
    """float32 little-endian -- format stabilny miedzy maszynami."""
    arr = array("f", values)
    if arr.itemsize != 4:  # pragma: no cover - nie zdarza sie na CPython
        raise RuntimeError("array('f') nie jest 32-bitowy na tej platformie")
    if sys.byteorder != "little":  # pragma: no cover - Apple Silicon jest little-endian
        arr.byteswap()
    return arr.tobytes()


def unpack_vector(blob: bytes | None) -> list[float]:
    if not blob:
        return []
    arr = array("f")
    arr.frombytes(blob)
    if sys.byteorder != "little":  # pragma: no cover
        arr.byteswap()
    return list(arr)


# ── schemat ──────────────────────────────────────────────────────────────────

_SCHEMA_V1 = """
CREATE TABLE IF NOT EXISTS schema_meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS roots (
    id       INTEGER PRIMARY KEY,
    path     TEXT NOT NULL UNIQUE,
    added_at TEXT NOT NULL,
    last_scan_at TEXT
);

-- Jedno logiczne zdjecie. RAW + JPG tej samej klatki wskazuja na ten sam wiersz.
CREATE TABLE IF NOT EXISTS frames (
    id               INTEGER PRIMARY KEY,
    capture_ts       TEXT,      -- ISO8601, czas lokalny aparatu
    capture_ts_epoch INTEGER,   -- sekundy; do liczenia serii
    sub_sec          INTEGER,   -- setne/tysieczne sekundy z EXIF, jesli sa
    month            TEXT,      -- 'YYYY-MM'
    day              TEXT,      -- 'YYYY-MM-DD'
    camera           TEXT,
    lens             TEXT,
    iso              INTEGER,
    f_number         REAL,
    exposure_time    REAL,
    width            INTEGER,
    height           INTEGER,
    orientation      INTEGER,
    preview_source   TEXT,      -- 'jpg' | 'raw_embedded' | 'raw_exiftool' | 'heic'
    primary_file_id  INTEGER,   -- plik uzywany do pikseli (przy parze RAW+JPG: JPG)
    analyzed_at      TEXT,
    face_count       INTEGER DEFAULT 0,
    subject_count    INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS files (
    id           INTEGER PRIMARY KEY,
    path         TEXT NOT NULL UNIQUE,
    root_id      INTEGER REFERENCES roots(id) ON DELETE SET NULL,
    frame_id     INTEGER REFERENCES frames(id) ON DELETE SET NULL,
    kind         TEXT NOT NULL,          -- 'jpg' | 'raw' | 'heic'
    stem_key     TEXT,                   -- katalog + nazwa bez rozszerzenia (parowanie RAW+JPG)
    size         INTEGER NOT NULL,
    mtime_ns     INTEGER NOT NULL,
    content_hash TEXT,
    status       TEXT NOT NULL,          -- 'pending' | 'indexed' | 'skipped' | 'error' | 'missing'
    error        TEXT,
    first_seen   TEXT NOT NULL,
    last_seen    TEXT NOT NULL,
    indexed_at   TEXT
);

-- Okresy zycia dziecka. Twarz zmienia sie z wiekiem, wiec pula referencyjna
-- jest podzielona na okresy i NIGDY nie usredniana do jednego wzorca.
CREATE TABLE IF NOT EXISTS periods (
    id         INTEGER PRIMARY KEY,
    idx        INTEGER NOT NULL UNIQUE,  -- kolejnosc chronologiczna
    label      TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS faces (
    id                 INTEGER PRIMARY KEY,
    frame_id           INTEGER NOT NULL REFERENCES frames(id) ON DELETE CASCADE,
    bbox_x             INTEGER, bbox_y INTEGER, bbox_w INTEGER, bbox_h INTEGER,
    det_score          REAL,
    embedding          BLOB,
    embed_dim          INTEGER,
    embed_model        TEXT,
    landmarks          BLOB,
    pose_yaw           REAL,
    pose_pitch         REAL,
    sharpness          REAL,   -- Laplacian variance na cropie twarzy 128x128
    exposure_mean      REAL,
    exposure_clip_low  REAL,
    exposure_clip_high REAL,
    eye_open           REAL,
    smile              REAL,
    face_ratio         REAL,   -- udzial twarzy w kadrze
    match_sim          REAL,
    match_period_id    INTEGER REFERENCES periods(id) ON DELETE SET NULL,
    is_subject         INTEGER DEFAULT 0,
    identity_uncertain INTEGER DEFAULT 0
);

-- Pula referencyjna: kazdy embedding osobno, przypisany do okresu zycia.
CREATE TABLE IF NOT EXISTS refs (
    id          INTEGER PRIMARY KEY,
    period_id   INTEGER REFERENCES periods(id) ON DELETE SET NULL,
    face_id     INTEGER REFERENCES faces(id) ON DELETE SET NULL,
    source_path TEXT,
    embedding   BLOB NOT NULL,
    embed_dim   INTEGER NOT NULL,
    embed_model TEXT NOT NULL,
    origin      TEXT NOT NULL,          -- 'calibrate' | 'review_confirmed'
    capture_ts  TEXT,
    active      INTEGER NOT NULL DEFAULT 1,
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS scores (
    frame_id        INTEGER PRIMARY KEY REFERENCES frames(id) ON DELETE CASCADE,
    face_id         INTEGER REFERENCES faces(id) ON DELETE SET NULL,
    total           REAL,
    components      TEXT,               -- JSON: surowe i wazone skladowe
    weights_version INTEGER,
    burst_key       TEXT,
    burst_best      INTEGER DEFAULT 0,
    scored_at       TEXT
);

CREATE TABLE IF NOT EXISTS decisions (
    id         INTEGER PRIMARY KEY,
    frame_id   INTEGER NOT NULL REFERENCES frames(id) ON DELETE CASCADE,
    month      TEXT NOT NULL,
    state      TEXT NOT NULL,           -- 'proposed'|'approved'|'rejected'|'favorite'
    reason     TEXT,
    decided_at TEXT NOT NULL,
    UNIQUE (frame_id, month)
);

CREATE TABLE IF NOT EXISTS notes (
    month      TEXT PRIMARY KEY,
    text       TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS weights (
    version    INTEGER PRIMARY KEY,
    json       TEXT NOT NULL,
    reason     TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS log (
    id     INTEGER PRIMARY KEY,
    ts     TEXT NOT NULL,
    level  TEXT NOT NULL,
    event  TEXT NOT NULL,
    path   TEXT,
    detail TEXT
);

CREATE INDEX IF NOT EXISTS idx_files_status  ON files(status);
CREATE INDEX IF NOT EXISTS idx_files_frame   ON files(frame_id);
CREATE INDEX IF NOT EXISTS idx_files_hash    ON files(content_hash);
CREATE INDEX IF NOT EXISTS idx_files_stem    ON files(stem_key);
CREATE INDEX IF NOT EXISTS idx_frames_month  ON frames(month);
CREATE INDEX IF NOT EXISTS idx_frames_epoch  ON frames(capture_ts_epoch);
CREATE INDEX IF NOT EXISTS idx_faces_frame   ON faces(frame_id);
CREATE INDEX IF NOT EXISTS idx_faces_subject ON faces(is_subject);
CREATE INDEX IF NOT EXISTS idx_refs_period   ON refs(period_id, active);
CREATE INDEX IF NOT EXISTS idx_decisions_m   ON decisions(month, state);
CREATE INDEX IF NOT EXISTS idx_log_event     ON log(event);
"""

_MIGRATIONS = {1: _SCHEMA_V1}


class Database:
    """Cienka warstwa nad sqlite3 -- zapytania zostaja u wolajacych."""

    def __init__(self, conn: sqlite3.Connection, path: Path):
        self.conn = conn
        self.path = path

    # ── transakcje ────────────────────────────────────────────────────────────

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        """Jedna paczka pracy. Blad -> rollback, sukces -> commit.

        Indeksowanie dzieli prace na takie paczki, wiec przerwanie kosztuje
        najwyzej biezaca paczke, nigdy calego przebiegu.
        """
        try:
            self.conn.execute("BEGIN IMMEDIATE")
            yield self.conn
        except BaseException:
            self.conn.rollback()
            raise
        else:
            self.conn.commit()

    def execute(self, sql: str, params: Sequence = ()) -> sqlite3.Cursor:
        return self.conn.execute(sql, params)

    def query(self, sql: str, params: Sequence = ()) -> list[sqlite3.Row]:
        return self.conn.execute(sql, params).fetchall()

    def one(self, sql: str, params: Sequence = ()) -> sqlite3.Row | None:
        return self.conn.execute(sql, params).fetchone()

    def scalar(self, sql: str, params: Sequence = ()):
        row = self.one(sql, params)
        return row[0] if row else None

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "Database":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    # ── pomocnicze ────────────────────────────────────────────────────────────

    def log(self, level: str, event: str, path: str | None = None, detail: str = "") -> None:
        self.conn.execute(
            "INSERT INTO log (ts, level, event, path, detail) VALUES (?, ?, ?, ?, ?)",
            (utc_now(), level, event, path, detail),
        )

    def get_root_id(self, path: Path) -> int:
        text = str(path)
        row = self.one("SELECT id FROM roots WHERE path = ?", (text,))
        if row:
            return row["id"]
        cur = self.conn.execute(
            "INSERT INTO roots (path, added_at) VALUES (?, ?)", (text, utc_now())
        )
        return int(cur.lastrowid)

    def counts(self) -> dict[str, int]:
        tables = ("files", "frames", "faces", "refs", "periods", "decisions", "notes")
        return {t: int(self.scalar(f"SELECT count(*) FROM {t}") or 0) for t in tables}

    def sync_periods(self, periods: Iterable) -> None:
        """Zapisuje wygenerowane okresy zycia (idempotentnie, po `idx`)."""
        for period in periods:
            self.conn.execute(
                """
                INSERT INTO periods (idx, label, start_date, end_date)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(idx) DO UPDATE SET
                    label = excluded.label,
                    start_date = excluded.start_date,
                    end_date = excluded.end_date
                """,
                (period.idx, period.label, period.start.isoformat(), period.end.isoformat()),
            )


def _apply_migrations(conn: sqlite3.Connection) -> None:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
    )
    row = conn.execute("SELECT value FROM schema_meta WHERE key = 'schema_version'").fetchone()
    current = int(row[0]) if row else 0
    if current > SCHEMA_VERSION:
        raise RuntimeError(
            f"Baza ma schemat w wersji {current}, a to narzedzie zna {SCHEMA_VERSION}. "
            "Zaktualizuj timemachine."
        )
    for version in range(current + 1, SCHEMA_VERSION + 1):
        conn.executescript(_MIGRATIONS[version])
        conn.execute(
            "INSERT INTO schema_meta (key, value) VALUES ('schema_version', ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (str(version),),
        )
    conn.commit()


def connect(path: Path | None = None, *, read_only: bool = False) -> Database:
    """Otwiera (i w razie potrzeby tworzy) baze biblioteki."""
    target = Path(path).expanduser() if path else config.db_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    if read_only and not target.exists():
        raise FileNotFoundError(f"Brak bazy {target}. Uruchom najpierw `timemachine index`.")

    conn = sqlite3.connect(target, isolation_level=None, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=30000")
    if not read_only:
        _apply_migrations(conn)
    return Database(conn, target)
