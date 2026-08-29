"""Test przejscia przez CLI od `init` do `status` -- bez modeli i bez sieci."""
import pytest

from timemachine import cli, config
from timemachine import db as db_module

from .helpers import write_jpeg


@pytest.fixture(autouse=True)
def isolated_home(monkeypatch, tmp_path):
    monkeypatch.setenv("TIMEMACHINE_HOME", str(tmp_path / "dom"))
    return tmp_path


@pytest.fixture()
def archive(tmp_path):
    root = tmp_path / "archiwum"
    write_jpeg(root / "2025" / "a.jpg", datetime_original="2025:08:14 10:00:00")
    write_jpeg(root / "2025" / "b.jpg", datetime_original="2025:08:14 10:00:03")
    write_jpeg(root / "2025" / "c.jpg", datetime_original="2025:08:20 16:30:00")
    return root


def run(*args) -> int:
    return cli.main(list(args))


# ── init ─────────────────────────────────────────────────────────────────────

def test_init_creates_config_and_database(capsys):
    assert run("init") == cli.EXIT_OK
    assert config.config_path().exists()
    assert config.db_path().exists()
    assert "Utworzono" in capsys.readouterr().out


def test_init_does_not_overwrite_without_force(capsys):
    run("init")
    config.config_path().write_text('[child]\nbirth_date = "2024-02-29"\n', encoding="utf-8")

    assert run("init") == cli.EXIT_OK
    assert config.load().birth_date.isoformat() == "2024-02-29"
    assert "--force" in capsys.readouterr().out


def test_init_force_overwrites(capsys):
    run("init")
    config.config_path().write_text('[child]\nbirth_date = "2024-02-29"\n', encoding="utf-8")
    assert run("init", "--force") == cli.EXIT_OK
    assert config.load().birth_date.isoformat() == "2023-01-01"


# ── doctor ───────────────────────────────────────────────────────────────────

def test_doctor_reports_dependencies_and_paths(capsys):
    run("init")
    assert run("doctor") == cli.EXIT_OK
    out = capsys.readouterr().out
    assert "Zaleznosci:" in out
    assert "insightface" in out
    assert "data urodzenia" in out


def test_doctor_works_before_init(capsys):
    assert run("doctor") == cli.EXIT_OK
    assert "timemachine init" in capsys.readouterr().out


# ── index ────────────────────────────────────────────────────────────────────

def test_index_scans_and_reports(capsys, archive):
    run("init")
    assert run("index", str(archive), "--no-progress") == cli.EXIT_OK

    out = capsys.readouterr().out
    assert "Skanowanie" in out
    assert "nowych: 3" in out

    with db_module.connect() as database:
        assert database.scalar("SELECT count(*) FROM frames") == 3
        assert database.scalar("SELECT count(*) FROM periods") > 0


def test_index_is_incremental_on_second_run(capsys, archive):
    run("init")
    run("index", str(archive), "--no-progress")
    capsys.readouterr()

    run("index", str(archive), "--no-progress")
    assert "bez zmian: 3" in capsys.readouterr().out


def test_index_without_face_model_says_what_to_do(capsys, archive):
    run("init")
    run("index", str(archive), "--no-progress")
    out = capsys.readouterr().out
    # W tym srodowisku nie ma insightface -- narzedzie ma to powiedziec wprost,
    # a nie wywrocic sie na ImportError.
    assert "brak insightface" in out or "Analiza twarzy" in out


def test_index_of_missing_directory_fails_cleanly(capsys, tmp_path):
    run("init")
    assert run("index", str(tmp_path / "nie-ma"), "--no-progress") == cli.EXIT_ERROR


def test_index_without_config_points_at_init(capsys, archive):
    assert run("index", str(archive), "--no-progress") == cli.EXIT_ERROR
    assert "timemachine init" in capsys.readouterr().err


# ── status i log ─────────────────────────────────────────────────────────────

def test_status_summarises_library(capsys, archive):
    run("init")
    run("index", str(archive), "--no-progress")
    capsys.readouterr()

    assert run("status") == cli.EXIT_OK
    out = capsys.readouterr().out
    assert "frames" in out
    assert "2025-08" in out


def test_log_lists_events(capsys, archive):
    run("init")
    write_jpeg(archive / "bez-daty.jpg", datetime_original=None, sub_sec=None)
    run("index", str(archive), "--no-progress")
    capsys.readouterr()

    assert run("log", "--skipped") == cli.EXIT_OK
    assert "no_exif_date" in capsys.readouterr().out


# ── notatki ──────────────────────────────────────────────────────────────────

def test_note_writes_and_reads_back(capsys):
    run("init")
    assert run("note", "2025-08", "Pierwsze kroki nad morzem.") == cli.EXIT_OK
    capsys.readouterr()

    assert run("note", "2025-08") == cli.EXIT_OK
    assert "Pierwsze kroki nad morzem." in capsys.readouterr().out


def test_note_overwrites_previous_text(capsys):
    run("init")
    run("note", "2025-08", "pierwsza wersja")
    run("note", "2025-08", "druga wersja")
    capsys.readouterr()

    run("note", "2025-08")
    out = capsys.readouterr().out
    assert "druga wersja" in out and "pierwsza wersja" not in out


def test_missing_note_is_reported(capsys):
    run("init")
    assert run("note", "2030-01") == cli.EXIT_OK
    assert "Brak notatki" in capsys.readouterr().out


# ── kalibracja ───────────────────────────────────────────────────────────────

def test_calibrate_status_shows_periods_and_gaps(capsys):
    run("init")
    assert run("calibrate") == cli.EXIT_OK
    out = capsys.readouterr().out
    assert "Pula referencyjna wg okresow zycia" in out
    assert "razem: 0 referencji" in out
    assert "bez referencji" in out


def test_calibrate_list_is_empty_at_first(capsys):
    run("init")
    assert run("calibrate", "list") == cli.EXIT_OK
    assert "pusta" in capsys.readouterr().out


def test_calibrate_remove_of_unknown_id_fails(capsys):
    run("init")
    assert run("calibrate", "remove", "--id", "42") == cli.EXIT_ERROR


# ── etapy jeszcze nieukonczone ───────────────────────────────────────────────

@pytest.mark.parametrize("command", ["pick", "review", "build"])
def test_later_stages_say_so_instead_of_crashing(capsys, command):
    run("init")
    assert run(command, "2025-08") == cli.EXIT_ERROR
    assert "Etap" in capsys.readouterr().out
