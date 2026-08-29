"""Testy skanera: przyrostowosc, parowanie RAW+JPG, nietykalnosc archiwum."""
import os
import shutil
from datetime import date

import pytest

from timemachine import config, scanner
from timemachine import db as db_module

from .helpers import write_jpeg, write_raw


@pytest.fixture()
def database(tmp_path):
    with db_module.connect(tmp_path / "library.db") as handle:
        yield handle


@pytest.fixture()
def cfg():
    settings = config.Config()
    settings.child.birth_date = date(2023, 4, 12)
    return settings


@pytest.fixture()
def archive(tmp_path):
    return tmp_path / "archiwum"


def snapshot(root):
    """Stan archiwum: sciezka -> (rozmiar, mtime_ns, tresc)."""
    state = {}
    for base, _dirs, names in os.walk(root):
        for name in names:
            path = os.path.join(base, name)
            stat = os.stat(path)
            with open(path, "rb") as fh:
                state[path] = (stat.st_size, stat.st_mtime_ns, fh.read())
    return state


def run(database, cfg, root, **kwargs):
    kwargs.setdefault("show_progress", False)
    return scanner.index_paths(database, cfg, [root], **kwargs)


# ── podstawy ─────────────────────────────────────────────────────────────────

def test_indexes_new_files(database, cfg, archive):
    write_jpeg(archive / "2025" / "a.jpg", datetime_original="2025:08:14 10:00:00")
    write_jpeg(archive / "2025" / "b.jpg", datetime_original="2025:08:14 10:00:07")

    stats = run(database, cfg, archive)

    assert (stats.seen, stats.new, stats.unchanged) == (2, 2, 0)
    assert stats.frames_created == 2
    assert database.scalar("SELECT count(*) FROM files WHERE status = 'pending'") == 2


def test_extracts_exif_into_frames(database, cfg, archive):
    write_jpeg(archive / "a.jpg", datetime_original="2025:08:14 10:11:12", iso=800)
    run(database, cfg, archive)

    frame = database.one("SELECT * FROM frames")
    assert frame["month"] == "2025-08"
    assert frame["day"] == "2025-08-14"
    assert frame["iso"] == 800
    assert frame["camera"] == "Canon EOS R5"
    assert frame["capture_ts_epoch"] is not None


def test_second_run_skips_unchanged_files(database, cfg, archive):
    write_jpeg(archive / "a.jpg")
    write_jpeg(archive / "b.jpg", datetime_original="2025:08:14 11:00:00")
    run(database, cfg, archive)

    stats = run(database, cfg, archive)

    assert (stats.new, stats.changed, stats.unchanged) == (0, 0, 2)
    assert database.scalar("SELECT count(*) FROM frames") == 2


def test_changed_file_is_reindexed(database, cfg, archive):
    path = write_jpeg(archive / "a.jpg", datetime_original="2025:08:14 10:00:00")
    run(database, cfg, archive)

    write_jpeg(path, datetime_original="2025:09:01 09:00:00", padding=128)
    os.utime(path, ns=(0, 0))  # inny mtime
    stats = run(database, cfg, archive)

    assert stats.changed == 1
    assert database.scalar("SELECT month FROM frames ORDER BY id DESC LIMIT 1") == "2025-09"


def test_changed_file_updates_its_frame_instead_of_orphaning_it(database, cfg, archive):
    """Numer klatki jest kotwica dla decyzji z review -- podmiana pliku nie moze go zgubic."""
    path = write_jpeg(archive / "a.jpg", datetime_original="2025:08:14 10:00:00")
    run(database, cfg, archive)
    frame_id = database.scalar("SELECT frame_id FROM files")
    with database.transaction():
        database.execute(
            "INSERT INTO decisions (frame_id, month, state, decided_at) "
            "VALUES (?, '2025-08', 'approved', 'now')",
            (frame_id,),
        )

    write_jpeg(path, datetime_original="2025:09:01 09:00:00", padding=64)
    os.utime(path, ns=(0, 0))
    run(database, cfg, archive)

    assert database.scalar("SELECT count(*) FROM frames") == 1
    assert database.scalar("SELECT frame_id FROM files") == frame_id
    assert database.scalar("SELECT count(*) FROM decisions") == 1
    assert database.scalar("SELECT analyzed_at FROM frames") is None  # do ponownej analizy


def test_files_without_exif_date_are_indexed_and_logged(database, cfg, archive):
    write_jpeg(archive / "bez-daty.jpg", datetime_original=None, sub_sec=None)
    run(database, cfg, archive)

    frame = database.one("SELECT * FROM frames")
    assert frame["capture_ts"] is None
    assert database.scalar("SELECT count(*) FROM log WHERE event = 'no_exif_date'") == 1


def test_non_photo_files_are_ignored(database, cfg, archive):
    write_jpeg(archive / "a.jpg")
    (archive / "notatki.txt").write_text("nie zdjecie")
    (archive / "film.mov").write_bytes(b"\x00" * 10)

    stats = run(database, cfg, archive)
    assert stats.seen == 1


def test_hidden_and_system_directories_are_skipped(database, cfg, archive):
    write_jpeg(archive / "a.jpg")
    write_jpeg(archive / ".Trashes" / "skasowane.jpg")
    write_jpeg(archive / ".git" / "cos.jpg")

    assert run(database, cfg, archive).seen == 1


def test_apple_double_files_are_skipped(database, cfg, archive):
    write_jpeg(archive / "a.jpg")
    write_jpeg(archive / "._a.jpg")

    assert run(database, cfg, archive).seen == 1


# ── parowanie RAW + JPG ──────────────────────────────────────────────────────

def test_raw_and_jpg_of_the_same_frame_share_one_frame(database, cfg, archive):
    stamp = "2025:08:14 10:11:12"
    write_jpeg(archive / "IMG_1234.jpg", datetime_original=stamp)
    write_raw(archive / "IMG_1234.cr2", datetime_original=stamp)

    stats = run(database, cfg, archive)

    assert stats.seen == 2
    assert stats.frames_created == 1
    assert stats.frames_paired == 1
    assert database.scalar("SELECT count(*) FROM frames") == 1


def test_paired_frame_uses_the_jpg_for_pixels(database, cfg, archive):
    stamp = "2025:08:14 10:11:12"
    # RAW pierwszy alfabetycznie, zeby sprawdzic, ze JPG i tak przejmuje role.
    write_raw(archive / "IMG_1234.cr2", datetime_original=stamp)
    write_jpeg(archive / "IMG_1234.jpg", datetime_original=stamp)

    run(database, cfg, archive)

    row = database.one(
        "SELECT f.kind, fr.preview_source FROM frames fr JOIN files f ON f.id = fr.primary_file_id"
    )
    assert row["kind"] == "jpg"
    assert row["preview_source"] == "jpg"


def test_same_name_but_different_time_stays_separate(database, cfg, archive):
    write_jpeg(archive / "IMG_1234.jpg", datetime_original="2025:08:14 10:11:12")
    write_raw(archive / "IMG_1234.cr2", datetime_original="2025:08:14 10:11:59")

    stats = run(database, cfg, archive)
    assert stats.frames_created == 2
    assert stats.frames_paired == 0


def test_pairing_can_be_switched_off(database, cfg, archive):
    stamp = "2025:08:14 10:11:12"
    cfg.archive.pair_raw_with_jpg = False
    write_jpeg(archive / "IMG_1234.jpg", datetime_original=stamp)
    write_raw(archive / "IMG_1234.cr2", datetime_original=stamp)

    assert run(database, cfg, archive).frames_created == 2


def test_files_in_different_folders_are_not_paired(database, cfg, archive):
    stamp = "2025:08:14 10:11:12"
    write_jpeg(archive / "jpg" / "IMG_1234.jpg", datetime_original=stamp)
    write_raw(archive / "raw" / "IMG_1234.cr2", datetime_original=stamp)

    assert run(database, cfg, archive).frames_created == 2


# ── przenoszenie i znikanie plikow ───────────────────────────────────────────

def test_moved_file_keeps_its_history(database, cfg, archive):
    source = write_jpeg(archive / "stare" / "a.jpg")
    run(database, cfg, archive)

    frame_id = database.scalar("SELECT frame_id FROM files")
    with database.transaction():
        database.execute(
            "INSERT INTO decisions (frame_id, month, state, decided_at) "
            "VALUES (?, '2025-08', 'approved', 'now')",
            (frame_id,),
        )

    target = archive / "nowe" / "a.jpg"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source), str(target))

    stats = run(database, cfg, archive)

    assert stats.moved == 1
    assert database.scalar("SELECT count(*) FROM files") == 1
    assert database.scalar("SELECT path FROM files") == str(target)
    assert database.scalar("SELECT frame_id FROM files") == frame_id
    assert database.scalar("SELECT count(*) FROM decisions WHERE state = 'approved'") == 1


def test_vanished_file_is_marked_missing_not_deleted(database, cfg, archive):
    path = write_jpeg(archive / "a.jpg")
    write_jpeg(archive / "b.jpg", datetime_original="2025:08:14 12:00:00")
    run(database, cfg, archive)

    os.remove(path)
    stats = run(database, cfg, archive)

    assert stats.missing == 1
    assert database.scalar("SELECT count(*) FROM files") == 2  # wiersz zostaje
    assert database.scalar("SELECT status FROM files WHERE path = ?", (str(path),)) == "missing"


# ── nietykalnosc archiwum ────────────────────────────────────────────────────

def test_indexing_never_touches_the_archive(database, cfg, archive):
    write_jpeg(archive / "2025" / "a.jpg")
    write_raw(archive / "2025" / "a.cr2")
    write_jpeg(archive / "2025" / "b.jpg", datetime_original="2025:08:14 12:00:00")

    before = snapshot(archive)
    run(database, cfg, archive)
    run(database, cfg, archive)  # takze przy powtornym uruchomieniu
    after = snapshot(archive)

    assert before == after


def test_database_lives_outside_the_archive(database, cfg, archive):
    write_jpeg(archive / "a.jpg")
    run(database, cfg, archive)
    assert not str(database.path).startswith(str(archive))


# ── bledy ────────────────────────────────────────────────────────────────────

def test_missing_root_is_a_clear_error(database, cfg, tmp_path):
    with pytest.raises(FileNotFoundError):
        run(database, cfg, tmp_path / "nie-ma-takiego")


def test_root_that_is_a_file_is_rejected(database, cfg, tmp_path):
    path = write_jpeg(tmp_path / "a.jpg")
    with pytest.raises(NotADirectoryError):
        run(database, cfg, path)


def test_hash_detects_content_change(tmp_path):
    path = write_jpeg(tmp_path / "a.jpg")
    first = scanner.hash_file(path)
    write_jpeg(path, padding=64)
    assert scanner.hash_file(path) != first


def test_full_hash_and_partial_hash_are_distinguishable(tmp_path):
    path = write_jpeg(tmp_path / "a.jpg")
    assert scanner.hash_file(path, full=True) != scanner.hash_file(path, full=False)
