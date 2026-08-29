"""Testy konfiguracji: szablon, walidacja, rozpoznawanie rozszerzen."""
import tomllib
from datetime import date

import pytest

from timemachine import config


def load(text: str) -> config.Config:
    return config.from_dict(tomllib.loads(text))


BASE = """
[child]
birth_date = "2023-04-12"
"""


# ── szablon ──────────────────────────────────────────────────────────────────

def test_default_template_is_valid_toml_and_parses():
    cfg = load(config.default_toml())
    assert cfg.child.birth_date == date(2023, 1, 1)
    assert cfg.selection.max_per_day == 2
    assert cfg.selection.burst_gap_seconds == 5.0
    assert cfg.scoring.weights["sharpness"] > 0


def test_default_template_mentions_every_section():
    text = config.default_toml()
    for section in ("[child]", "[archive]", "[faces]", "[identity]",
                    "[scoring]", "[scoring.weights]", "[selection]", "[build]"):
        assert section in text


# ── data urodzenia ───────────────────────────────────────────────────────────

def test_birth_date_is_parsed():
    assert load(BASE).birth_date == date(2023, 4, 12)


def test_missing_birth_date_is_a_clear_error():
    cfg = config.from_dict({})
    with pytest.raises(config.ConfigError, match="birth_date"):
        _ = cfg.birth_date


def test_malformed_birth_date_is_rejected():
    with pytest.raises(config.ConfigError, match="birth_date"):
        load('[child]\nbirth_date = "12-04-2023"\n')


# ── walidacja ────────────────────────────────────────────────────────────────

def test_unknown_setting_is_rejected():
    with pytest.raises(config.ConfigError, match="nieznane ustawienie"):
        load(BASE + "\n[selection]\nmax_per_wek = 3\n")


def test_wrong_type_is_rejected():
    with pytest.raises(config.ConfigError, match="liczby calkowitej"):
        load(BASE + '\n[selection]\nmax_per_day = "dwa"\n')


@pytest.mark.parametrize(
    "snippet,message",
    [
        ("[selection]\nmin_per_month = 0", "min_per_month"),
        ("[selection]\nmin_per_month = 8\nmax_per_month = 4", "max_per_month"),
        ("[selection]\nmax_per_day = 0", "max_per_day"),
        ("[selection]\nburst_gap_seconds = 0.0", "burst_gap_seconds"),
        ("[identity]\nthreshold = 1.5", "threshold"),
        ("[faces]\nmin_det_score = 2.0", "min_det_score"),
        ("[build]\njpeg_quality = 0", "jpeg_quality"),
        ("[build]\nmax_edge_px = 100", "max_edge_px"),
        ("[scoring.weights]\nsharpness = -1.0", "sharpness"),
    ],
)
def test_out_of_range_values_are_rejected(snippet, message):
    with pytest.raises(config.ConfigError, match=message):
        load(BASE + "\n" + snippet + "\n")


def test_max_refs_must_not_be_below_min_refs():
    with pytest.raises(config.ConfigError, match="max_refs_per_period"):
        load(BASE + "\n[identity]\nmin_refs_per_period = 10\nmax_refs_per_period = 2\n")


# ── rozszerzenia ─────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "suffix,expected",
    [(".jpg", "jpg"), (".JPG", "jpg"), (".jpeg", "jpg"), (".cr3", "raw"), (".NEF", "raw"),
     (".dng", "raw"), (".heic", "heic"), (".mov", None), (".txt", None), ("", None)],
)
def test_kind_of(suffix, expected):
    assert config.Config().kind_of(suffix) == expected


def test_photo_extensions_are_lowercase():
    extensions = config.Config().photo_extensions
    assert all(e == e.lower() for e in extensions)
    assert ".jpg" in extensions and ".cr3" in extensions


# ── sciezki ──────────────────────────────────────────────────────────────────

def test_home_dir_follows_environment(monkeypatch, tmp_path):
    monkeypatch.setenv("TIMEMACHINE_HOME", str(tmp_path / "gdzie-indziej"))
    assert config.home_dir() == tmp_path / "gdzie-indziej"
    assert config.db_path() == tmp_path / "gdzie-indziej" / "library.db"


def test_load_without_config_points_at_init(monkeypatch, tmp_path):
    monkeypatch.setenv("TIMEMACHINE_HOME", str(tmp_path))
    with pytest.raises(config.ConfigError, match="timemachine init"):
        config.load()


def test_roots_and_output_are_expanded(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    cfg = load(BASE + '\n[archive]\nroots = ["~/zdjecia"]\n[build]\noutput_dir = "~/os-czasu"\n')
    assert cfg.root_paths() == [tmp_path / "zdjecia"]
    assert cfg.output_dir() == tmp_path / "os-czasu"
