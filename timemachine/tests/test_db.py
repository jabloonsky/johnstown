"""Testy warstwy SQLite: schemat, migracje, transakcje, pakowanie embeddingow."""
import sqlite3
from datetime import date

import pytest

from timemachine import db as db_module
from timemachine import identity


@pytest.fixture()
def database(tmp_path):
    with db_module.connect(tmp_path / "library.db") as handle:
        yield handle


# ── schemat ──────────────────────────────────────────────────────────────────

def test_connect_creates_schema_and_version(database):
    version = database.scalar("SELECT value FROM schema_meta WHERE key = 'schema_version'")
    assert int(version) == db_module.SCHEMA_VERSION


def test_expected_tables_exist(database):
    rows = database.query("SELECT name FROM sqlite_master WHERE type = 'table'")
    names = {r["name"] for r in rows}
    assert {"files", "frames", "faces", "refs", "periods", "decisions", "notes",
            "weights", "scores", "log", "roots"} <= names


def test_reopening_is_idempotent(tmp_path):
    path = tmp_path / "library.db"
    with db_module.connect(path) as first:
        with first.transaction():
            first.execute("INSERT INTO notes (month, text, updated_at) VALUES ('2025-08', 'x', 'now')")
    with db_module.connect(path) as second:
        assert second.scalar("SELECT count(*) FROM notes") == 1
        assert int(second.scalar(
            "SELECT value FROM schema_meta WHERE key = 'schema_version'"
        )) == db_module.SCHEMA_VERSION


def test_wal_mode_is_enabled(database):
    assert database.scalar("PRAGMA journal_mode").lower() == "wal"


def test_refuses_database_from_a_newer_version(tmp_path):
    path = tmp_path / "library.db"
    with db_module.connect(path) as handle:
        with handle.transaction():
            handle.execute(
                "UPDATE schema_meta SET value = ? WHERE key = 'schema_version'",
                (str(db_module.SCHEMA_VERSION + 5),),
            )
    with pytest.raises(RuntimeError, match="Zaktualizuj timemachine"):
        db_module.connect(path)


def test_read_only_connect_requires_existing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        db_module.connect(tmp_path / "nie-ma.db", read_only=True)


# ── transakcje ───────────────────────────────────────────────────────────────

def test_transaction_commits_on_success(database):
    with database.transaction():
        database.execute("INSERT INTO notes (month, text, updated_at) VALUES ('2025-01', 'a', 'now')")
    assert database.scalar("SELECT count(*) FROM notes") == 1


def test_transaction_rolls_back_on_error(database):
    with pytest.raises(ValueError):
        with database.transaction():
            database.execute(
                "INSERT INTO notes (month, text, updated_at) VALUES ('2025-01', 'a', 'now')"
            )
            raise ValueError("cos poszlo nie tak")
    assert database.scalar("SELECT count(*) FROM notes") == 0


def test_interrupted_batch_leaves_earlier_batches_intact(database):
    """Przerwanie kosztuje najwyzej biezaca paczke -- to podstawa wznawialnosci."""
    with database.transaction():
        database.execute("INSERT INTO notes (month, text, updated_at) VALUES ('2025-01', 'a', 'now')")

    with pytest.raises(KeyboardInterrupt):
        with database.transaction():
            database.execute(
                "INSERT INTO notes (month, text, updated_at) VALUES ('2025-02', 'b', 'now')"
            )
            raise KeyboardInterrupt

    months = [r["month"] for r in database.query("SELECT month FROM notes")]
    assert months == ["2025-01"]


def test_foreign_keys_are_enforced(database):
    with pytest.raises(sqlite3.IntegrityError):
        with database.transaction():
            database.execute(
                "INSERT INTO faces (frame_id, det_score) VALUES (999999, 0.9)"
            )


def test_deleting_a_frame_cascades_to_faces(database):
    with database.transaction():
        cur = database.execute("INSERT INTO frames (month) VALUES ('2025-08')")
        frame_id = cur.lastrowid
        database.execute("INSERT INTO faces (frame_id, det_score) VALUES (?, 0.9)", (frame_id,))
    with database.transaction():
        database.execute("DELETE FROM frames WHERE id = ?", (frame_id,))
    assert database.scalar("SELECT count(*) FROM faces") == 0


# ── embeddingi ───────────────────────────────────────────────────────────────

def test_vector_roundtrip_keeps_float32_precision():
    original = [0.1, -0.25, 0.5, 1.0, -1.0]
    restored = db_module.unpack_vector(db_module.pack_vector(original))
    assert restored == pytest.approx(original, abs=1e-6)


def test_vector_roundtrip_preserves_length():
    original = [i / 512 for i in range(512)]
    assert len(db_module.unpack_vector(db_module.pack_vector(original))) == 512


def test_empty_blob_unpacks_to_empty_list():
    assert db_module.unpack_vector(None) == []
    assert db_module.unpack_vector(b"") == []


# ── okresy ───────────────────────────────────────────────────────────────────

def test_sync_periods_is_idempotent(database):
    periods = identity.generate_periods(date(2023, 4, 12), date(2026, 1, 1))
    with database.transaction():
        database.sync_periods(periods)
    with database.transaction():
        database.sync_periods(periods)
    assert database.scalar("SELECT count(*) FROM periods") == len(periods)


def test_sync_periods_extends_without_renumbering(database):
    birth = date(2023, 4, 12)
    with database.transaction():
        database.sync_periods(identity.generate_periods(birth, date(2025, 1, 1)))
    before = database.query("SELECT idx, start_date FROM periods ORDER BY idx")

    with database.transaction():
        database.sync_periods(identity.generate_periods(birth, date(2030, 1, 1)))
    after = database.query("SELECT idx, start_date FROM periods ORDER BY idx")

    assert len(after) > len(before)
    for old, new in zip(before, after):
        assert (old["idx"], old["start_date"]) == (new["idx"], new["start_date"])
