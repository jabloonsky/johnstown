"""Skanowanie archiwum: przyrostowe, wznawialne, wylacznie do odczytu.

Faza A (ten modul) jest tania: chodzi po katalogach, porownuje (rozmiar, mtime)
z baza i tylko dla nowych albo zmienionych plikow liczy skrot i czyta EXIF.
Faza B (analyze.py) jest kosztowna -- dekoduje piksele i szuka twarzy -- i
pracuje juz tylko po tym, co faza A oznaczyla jako `pending`.

Kluczowe wlasnosci:
  * plik niezmieniony (ten sam rozmiar i mtime_ns) nie jest w ogole otwierany;
  * przeniesiony plik jest rozpoznawany po skrocie tresci, wiec decyzje z review
    i przypisanie do miesiaca przezywaja reorganizacje katalogow;
  * praca dzieli sie na paczki zapisywane osobnymi transakcjami -- Ctrl-C kosztuje
    najwyzej biezaca paczke;
  * RAW i JPG tej samej klatki laduja w jednym wierszu `frames`.
"""
from __future__ import annotations

import calendar
import hashlib
import os
import signal
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterator

from . import config, exif, exiftool, safety
from .db import Database, utc_now
from .progress import Progress

__all__ = ["ScanStats", "index_paths", "hash_file"]

_HASH_CHUNK = 1 << 20  # 1 MiB z poczatku i konca pliku
_BATCH = 200


@dataclass
class ScanStats:
    seen: int = 0
    new: int = 0
    changed: int = 0
    unchanged: int = 0
    moved: int = 0
    missing: int = 0
    errors: int = 0
    frames_created: int = 0
    frames_paired: int = 0
    interrupted: bool = False
    roots: list[str] = field(default_factory=list)

    def summary(self) -> str:
        return (
            f"plikow: {self.seen}  nowych: {self.new}  zmienionych: {self.changed}  "
            f"bez zmian: {self.unchanged}  przeniesionych: {self.moved}  "
            f"zniknietych: {self.missing}  bledow: {self.errors}\n"
            f"klatek: +{self.frames_created}  sparowanych RAW+JPG: {self.frames_paired}"
        )


# ── skroty ───────────────────────────────────────────────────────────────────


def hash_file(path: Path, *, full: bool = False) -> str:
    """Skrot tresci pliku.

    Domyslnie blake2b z (rozmiar, pierwszy MiB, ostatni MiB) -- na dysku
    zewnetrznym to roznica miedzy minutami a godzinami, a do wykrywania
    przeniesionych plikow wystarcza. `--full-hash` liczy calosc.
    """
    digest = hashlib.blake2b(digest_size=16)
    if full:
        size = 0
        with safety.open_readonly(path) as fh:
            while chunk := fh.read(1 << 20):
                size += len(chunk)
                digest.update(chunk)
        digest.update(str(size).encode())
        return "f" + digest.hexdigest()
    head, tail, size = safety.read_head_tail(path, _HASH_CHUNK)
    digest.update(str(size).encode())
    digest.update(head)
    digest.update(tail)
    return "p" + digest.hexdigest()


# ── chodzenie po katalogach ──────────────────────────────────────────────────


def _should_skip_dir(name: str, cfg: config.Config) -> bool:
    if name in set(cfg.archive.skip_dir_names):
        return True
    # Ukryte katalogi i pakiety macOS (.photoslibrary itp.) pomijamy.
    return name.startswith(".")


def walk(root: Path, cfg: config.Config) -> Iterator[tuple[Path, os.stat_result]]:
    """Iteracyjny obchod katalogu -- bez rekurencji i bez podazania za petlami."""
    extensions = cfg.photo_extensions
    follow = cfg.archive.follow_symlinks
    visited: set[tuple[int, int]] = set()
    stack = [root]

    while stack:
        current = stack.pop()
        try:
            entries = list(os.scandir(current))
        except (PermissionError, FileNotFoundError, NotADirectoryError, OSError):
            continue
        for entry in sorted(entries, key=lambda e: e.name):
            try:
                if entry.is_dir(follow_symlinks=follow):
                    if _should_skip_dir(entry.name, cfg):
                        continue
                    stat = entry.stat(follow_symlinks=follow)
                    key = (stat.st_dev, stat.st_ino)
                    if key in visited:
                        continue
                    visited.add(key)
                    stack.append(Path(entry.path))
                    continue
                if not entry.is_file(follow_symlinks=follow):
                    continue
                if entry.name.startswith("._"):  # AppleDouble
                    continue
                if Path(entry.name).suffix.lower() not in extensions:
                    continue
                yield Path(entry.path), entry.stat(follow_symlinks=follow)
            except OSError:
                continue


# ── EXIF ─────────────────────────────────────────────────────────────────────


def read_metadata(path: Path, kind: str) -> exif.ExifData:
    """EXIF wlasnym parserem, a dla CR3/HEIC (ISO-BMFF) przez exiftool."""
    data = exif.ExifData()
    if kind in ("jpg", "raw"):
        try:
            data = exif.read_exif(path)
        except (OSError, ValueError):
            data = exif.ExifData()
    if data.capture is None and exiftool.available():
        fallback = exiftool.read_exif(path)
        if fallback.capture is not None or data.source == "none":
            return fallback
    return data


def _epoch(moment: datetime) -> int:
    """Sekundy liczone jak dla czasu 'sciennego' aparatu -- bez wplywu strefy maszyny."""
    return calendar.timegm(moment.timetuple())


# ── przerwanie ───────────────────────────────────────────────────────────────


class _InterruptGuard:
    """Ctrl-C nie przerywa transakcji -- konczymy paczke i wychodzimy czysto."""

    def __init__(self) -> None:
        self.requested = False
        self._previous = None

    def __enter__(self) -> "_InterruptGuard":
        try:
            self._previous = signal.signal(signal.SIGINT, self._handle)
        except ValueError:  # nie glowny watek (np. w testach)
            self._previous = None
        return self

    def _handle(self, *_args) -> None:
        self.requested = True

    def __exit__(self, *exc) -> None:
        if self._previous is not None:
            signal.signal(signal.SIGINT, self._previous)


# ── indeksowanie ─────────────────────────────────────────────────────────────


def _stem_key(path: Path) -> str:
    return str(path.parent / path.stem).lower()


def _frame_fields(meta: exif.ExifData, kind: str, file_id: int) -> tuple:
    capture_epoch = _epoch(meta.capture) if meta.capture else None
    return (
        meta.capture.isoformat() if meta.capture else None,
        capture_epoch,
        meta.sub_sec,
        meta.capture.strftime("%Y-%m") if meta.capture else None,
        meta.capture.strftime("%Y-%m-%d") if meta.capture else None,
        meta.camera,
        meta.lens_model,
        meta.iso,
        meta.f_number,
        meta.exposure_time,
        meta.width,
        meta.height,
        meta.orientation,
        "jpg" if kind == "jpg" else kind,
        file_id,
    )


def _drop_if_orphaned(db: Database, frame_id: int | None) -> None:
    """Klatka bez zadnego pliku nie ma juz sensu -- kasujemy ja wraz z twarzami."""
    if not frame_id:
        return
    if db.scalar("SELECT count(*) FROM files WHERE frame_id = ?", (frame_id,)):
        return
    db.execute("DELETE FROM frames WHERE id = ?", (frame_id,))


def _attach_frame(
    db: Database,
    cfg: config.Config,
    file_id: int,
    path: Path,
    kind: str,
    meta: exif.ExifData,
    existing_frame_id: int | None = None,
) -> tuple[int, bool, bool]:
    """Zwraca (frame_id, czy_utworzona, czy_sparowana).

    Plik, ktory juz mial wlasna klatke, aktualizuje ja w miejscu. To wazne:
    numer klatki jest tym, do czego dowiazane sa decyzje z review, wiec podmiana
    pliku (np. ponowny eksport JPG) nie moze skasowac zatwierdzenia miesiaca.
    """
    capture_epoch = _epoch(meta.capture) if meta.capture else None
    stem = _stem_key(path)

    if existing_frame_id:
        shared = db.scalar(
            "SELECT count(*) FROM files WHERE frame_id = ? AND id != ?",
            (existing_frame_id, file_id),
        )
        if not shared:
            db.execute(
                """
                UPDATE frames SET capture_ts = ?, capture_ts_epoch = ?, sub_sec = ?, month = ?,
                    day = ?, camera = ?, lens = ?, iso = ?, f_number = ?, exposure_time = ?,
                    width = ?, height = ?, orientation = ?, preview_source = ?,
                    primary_file_id = ?, analyzed_at = NULL
                WHERE id = ?
                """,
                (*_frame_fields(meta, kind, file_id), existing_frame_id),
            )
            return existing_frame_id, False, False
        if db.scalar(
            "SELECT capture_ts_epoch FROM frames WHERE id = ?", (existing_frame_id,)
        ) == capture_epoch:
            return existing_frame_id, False, True
        # Czas sie zmienil -- ten plik nie jest juz ta sama klatka co jego para.
        db.execute("UPDATE files SET frame_id = NULL WHERE id = ?", (file_id,))

    if cfg.archive.pair_raw_with_jpg:
        for row in db.query(
            "SELECT f.frame_id, fr.capture_ts_epoch FROM files f "
            "JOIN frames fr ON fr.id = f.frame_id "
            "WHERE f.stem_key = ? AND f.id != ? AND f.frame_id IS NOT NULL",
            (stem, file_id),
        ):
            if row["capture_ts_epoch"] == capture_epoch:
                frame_id = int(row["frame_id"])
                _maybe_promote_primary(db, frame_id, file_id, kind)
                return frame_id, False, True

    cur = db.execute(
        """
        INSERT INTO frames (
            capture_ts, capture_ts_epoch, sub_sec, month, day, camera, lens, iso,
            f_number, exposure_time, width, height, orientation, preview_source,
            primary_file_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        _frame_fields(meta, kind, file_id),
    )
    return int(cur.lastrowid), True, False


def _maybe_promote_primary(db: Database, frame_id: int, file_id: int, kind: str) -> None:
    """Do pikseli zawsze wolimy JPG -- szybciej i bez dekodowania RAW."""
    if kind != "jpg":
        return
    row = db.one(
        "SELECT fr.primary_file_id, f.kind FROM frames fr "
        "LEFT JOIN files f ON f.id = fr.primary_file_id WHERE fr.id = ?",
        (frame_id,),
    )
    if row and row["kind"] == "jpg":
        return
    db.execute(
        "UPDATE frames SET primary_file_id = ?, preview_source = 'jpg', analyzed_at = NULL "
        "WHERE id = ?",
        (file_id, frame_id),
    )


def _index_one(
    db: Database, cfg: config.Config, path: Path, stat: os.stat_result, root_id: int,
    *, full_hash: bool, stats: ScanStats,
) -> None:
    kind = cfg.kind_of(path.suffix)
    if kind is None:
        return
    text_path = str(path)
    now = utc_now()
    row = db.one("SELECT * FROM files WHERE path = ?", (text_path,))

    if (
        row
        and row["size"] == stat.st_size
        and row["mtime_ns"] == stat.st_mtime_ns
        and row["status"] in ("indexed", "pending", "skipped")
    ):
        db.execute("UPDATE files SET last_seen = ? WHERE id = ?", (now, row["id"]))
        stats.unchanged += 1
        return

    try:
        content_hash = hash_file(path, full=full_hash)
    except OSError as exc:
        stats.errors += 1
        if row:
            db.execute(
                "UPDATE files SET status = 'error', error = ?, last_seen = ? WHERE id = ?",
                (str(exc), now, row["id"]),
            )
        else:
            db.execute(
                "INSERT INTO files (path, root_id, kind, stem_key, size, mtime_ns, status, "
                "error, first_seen, last_seen) VALUES (?, ?, ?, ?, ?, ?, 'error', ?, ?, ?)",
                (text_path, root_id, kind, _stem_key(path), stat.st_size,
                 stat.st_mtime_ns, str(exc), now, now),
            )
        db.log("error", "read_failed", text_path, str(exc))
        return

    if row is None:
        # Ten sam skrot pod inna sciezka = plik przeniesiony. Przejmujemy jego
        # historie (klatke, twarze, decyzje) zamiast indeksowac go od zera.
        moved = db.one(
            "SELECT * FROM files WHERE content_hash = ? AND path != ? AND size = ?",
            (content_hash, text_path, stat.st_size),
        )
        if moved and not Path(moved["path"]).exists():
            db.execute(
                "UPDATE files SET path = ?, root_id = ?, stem_key = ?, mtime_ns = ?, "
                "status = CASE WHEN status = 'missing' THEN 'indexed' ELSE status END, "
                "last_seen = ? WHERE id = ?",
                (text_path, root_id, _stem_key(path), stat.st_mtime_ns, now, moved["id"]),
            )
            db.log("info", "moved", text_path, f"z {moved['path']}")
            stats.moved += 1
            return

    meta = read_metadata(path, kind)

    if row is None:
        cur = db.execute(
            "INSERT INTO files (path, root_id, kind, stem_key, size, mtime_ns, content_hash, "
            "status, first_seen, last_seen) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)",
            (text_path, root_id, kind, _stem_key(path), stat.st_size, stat.st_mtime_ns,
             content_hash, now, now),
        )
        file_id = int(cur.lastrowid)
        stats.new += 1
    else:
        file_id = int(row["id"])
        db.execute(
            "UPDATE files SET root_id = ?, kind = ?, stem_key = ?, size = ?, mtime_ns = ?, "
            "content_hash = ?, status = 'pending', error = NULL, last_seen = ? WHERE id = ?",
            (root_id, kind, _stem_key(path), stat.st_size, stat.st_mtime_ns, content_hash,
             now, file_id),
        )
        stats.changed += 1

    previous_frame = int(row["frame_id"]) if row and row["frame_id"] else None
    frame_id, created, paired = _attach_frame(
        db, cfg, file_id, path, kind, meta, previous_frame
    )
    db.execute("UPDATE files SET frame_id = ? WHERE id = ?", (frame_id, file_id))
    if previous_frame and previous_frame != frame_id:
        _drop_if_orphaned(db, previous_frame)
    stats.frames_created += int(created)
    stats.frames_paired += int(paired)

    if meta.capture is None:
        db.log("warn", "no_exif_date", text_path, "brak DateTimeOriginal")


def _mark_missing(db: Database, root: Path, seen: set[str], stats: ScanStats) -> None:
    """Pliki znane bazie, ktorych juz nie ma na dysku -- oznaczamy, nie kasujemy.

    Dzieki temu zatwierdzone zdjecia znikaja z listy kandydatow, ale historia
    decyzji i notatki zostaja nietkniete.
    """
    # LIKE traktuje % i _ jako wieloznaczniki, a katalogi potrafia je zawierac.
    prefix = str(root) + os.sep
    escaped = prefix.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    for row in db.query(
        r"SELECT id, path FROM files WHERE path LIKE ? ESCAPE '\' AND status != 'missing'",
        (escaped + "%",),
    ):
        if row["path"] in seen:
            continue
        db.execute("UPDATE files SET status = 'missing' WHERE id = ?", (row["id"],))
        db.log("info", "missing", row["path"], "plik zniknal z archiwum")
        stats.missing += 1


def index_paths(
    db: Database,
    cfg: config.Config,
    roots: list[Path],
    *,
    full_hash: bool = False,
    show_progress: bool = True,
    batch_size: int = _BATCH,
) -> ScanStats:
    """Indeksuje wskazane katalogi. Bezpieczne do przerwania i ponownego uruchomienia."""
    stats = ScanStats(roots=[str(r) for r in roots])

    for root in roots:
        if not root.exists():
            raise FileNotFoundError(f"Nie ma takiego katalogu: {root}")
        if not root.is_dir():
            raise NotADirectoryError(f"To nie jest katalog: {root}")

    with _InterruptGuard() as guard:
        for root in roots:
            with db.transaction():
                root_id = db.get_root_id(root)

            print(f"[1/2] Zliczam pliki w {root} ...", flush=True)
            total = sum(1 for _ in walk(root, cfg))
            print(f"      znaleziono {total} plikow zdjeciowych", flush=True)

            seen: set[str] = set()
            progress = Progress(total, "[2/2] indeksowanie", enabled=show_progress)
            pending: list[tuple[Path, os.stat_result]] = []

            def flush(items: list[tuple[Path, os.stat_result]]) -> None:
                if not items:
                    return
                with db.transaction():
                    for item_path, item_stat in items:
                        _index_one(
                            db, cfg, item_path, item_stat, root_id,
                            full_hash=full_hash, stats=stats,
                        )
                items.clear()

            for path, stat in walk(root, cfg):
                seen.add(str(path))
                pending.append((path, stat))
                stats.seen += 1
                progress.advance(note=path.name[:40])
                if len(pending) >= batch_size:
                    flush(pending)
                    if guard.requested:
                        break

            flush(pending)
            progress.finish()

            if guard.requested:
                stats.interrupted = True
                break

            with db.transaction():
                _mark_missing(db, root, seen, stats)
                db.execute(
                    "UPDATE roots SET last_scan_at = ? WHERE id = ?", (utc_now(), root_id)
                )

    return stats
