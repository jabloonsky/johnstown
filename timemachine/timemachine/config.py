"""Konfiguracja uzytkownika: ~/.timemachine/config.toml.

Czytana stdlibowym `tomllib`. Katalog domowy narzedzia mozna nadpisac zmienna
srodowiskowa TIMEMACHINE_HOME -- korzystaja z tego testy i pozwala to trzymac
kilka niezaleznych bibliotek obok siebie.
"""
from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field, fields, is_dataclass
from datetime import date
from pathlib import Path
from typing import Any

__all__ = [
    "Config",
    "ConfigError",
    "home_dir",
    "config_path",
    "db_path",
    "cache_dir",
    "load",
    "default_toml",
    "DEFAULTS",
]

CONFIG_NAME = "config.toml"


class ConfigError(Exception):
    """Konfiguracja jest niekompletna albo niespojna."""


def home_dir() -> Path:
    return Path(os.environ.get("TIMEMACHINE_HOME", "~/.timemachine")).expanduser().absolute()


def config_path() -> Path:
    return home_dir() / CONFIG_NAME


def db_path() -> Path:
    return home_dir() / "library.db"


def cache_dir() -> Path:
    return home_dir() / "cache"


@dataclass
class ChildCfg:
    name: str = ""
    birth_date: date | None = None


@dataclass
class ArchiveCfg:
    roots: list[str] = field(default_factory=list)
    extensions_jpg: list[str] = field(default_factory=lambda: [".jpg", ".jpeg"])
    extensions_raw: list[str] = field(
        default_factory=lambda: [
            ".cr2", ".cr3", ".nef", ".nrw", ".arw", ".sr2", ".raf",
            ".orf", ".rw2", ".dng", ".pef", ".srw",
        ]
    )
    extensions_heic: list[str] = field(default_factory=lambda: [".heic", ".heif"])
    pair_raw_with_jpg: bool = True
    follow_symlinks: bool = False
    skip_dir_names: list[str] = field(
        default_factory=lambda: [".Trashes", ".Spotlight-V100", ".fseventsd", "@eaDir"]
    )


@dataclass
class FacesCfg:
    backend: str = "insightface"
    model: str = "buffalo_l"
    det_size: int = 640
    min_det_score: float = 0.60
    providers: list[str] = field(
        default_factory=lambda: ["CoreMLExecutionProvider", "CPUExecutionProvider"]
    )
    max_faces_per_frame: int = 12
    # Dluzszy bok obrazu podawanego detektorowi. Wiecej = wolniej, ale male twarze
    # w szerokim kadrze maja szanse zostac znalezione.
    analysis_max_edge: int = 1600


@dataclass
class IdentityCfg:
    """Parametry wielookresowego dopasowania twarzy (patrz identity.py)."""

    threshold: float = 0.38
    thin_pool_penalty: float = 0.03
    min_refs_per_period: int = 3
    max_refs_per_period: int = 40
    neighbor_span: int = 1
    tau_months: float = 6.0
    time_bonus: float = 0.15
    top_k: int = 3


@dataclass
class ScoringCfg:
    weights: dict[str, float] = field(
        default_factory=lambda: {
            "identity": 0.30,
            "sharpness": 0.30,
            "eyes": 0.20,
            "exposure": 0.15,
            "face_size": 0.05,
        }
    )
    smile_bonus: float = 0.10
    learning_rate: float = 0.15
    min_samples: int = 3


@dataclass
class SelectionCfg:
    min_per_month: int = 5
    max_per_month: int = 10
    max_per_day: int = 2
    burst_gap_seconds: float = 5.0


@dataclass
class BuildCfg:
    output_dir: str = "~/Pictures/timemachine"
    max_edge_px: int = 2000
    thumb_edge_px: int = 600
    jpeg_quality: int = 88


@dataclass
class Config:
    child: ChildCfg = field(default_factory=ChildCfg)
    archive: ArchiveCfg = field(default_factory=ArchiveCfg)
    faces: FacesCfg = field(default_factory=FacesCfg)
    identity: IdentityCfg = field(default_factory=IdentityCfg)
    scoring: ScoringCfg = field(default_factory=ScoringCfg)
    selection: SelectionCfg = field(default_factory=SelectionCfg)
    build: BuildCfg = field(default_factory=BuildCfg)
    source: Path | None = None

    # ── pochodne ──────────────────────────────────────────────────────────────

    @property
    def birth_date(self) -> date:
        if self.child.birth_date is None:
            raise ConfigError(
                f"Brak daty urodzenia. Uzupelnij [child].birth_date w {self.source or config_path()}."
            )
        return self.child.birth_date

    @property
    def photo_extensions(self) -> set[str]:
        a = self.archive
        return {e.lower() for e in (*a.extensions_jpg, *a.extensions_raw, *a.extensions_heic)}

    def kind_of(self, suffix: str) -> str | None:
        """'jpg' | 'raw' | 'heic' | None -- po rozszerzeniu pliku."""
        s = suffix.lower()
        a = self.archive
        if s in {e.lower() for e in a.extensions_jpg}:
            return "jpg"
        if s in {e.lower() for e in a.extensions_raw}:
            return "raw"
        if s in {e.lower() for e in a.extensions_heic}:
            return "heic"
        return None

    def output_dir(self) -> Path:
        return Path(self.build.output_dir).expanduser().absolute()

    def root_paths(self) -> list[Path]:
        return [Path(r).expanduser().absolute() for r in self.archive.roots]


DEFAULTS = Config()


# ── wczytywanie ──────────────────────────────────────────────────────────────


def _coerce(value: Any, target: Any, where: str) -> Any:
    """Rzutuje wartosc z TOML na typ pola dataclass, z czytelnym bledem."""
    if isinstance(target, bool):
        if not isinstance(value, bool):
            raise ConfigError(f"{where}: oczekiwano true/false, dostano {value!r}")
        return value
    if isinstance(target, float):
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ConfigError(f"{where}: oczekiwano liczby, dostano {value!r}")
        return float(value)
    if isinstance(target, int):
        if not isinstance(value, int) or isinstance(value, bool):
            raise ConfigError(f"{where}: oczekiwano liczby calkowitej, dostano {value!r}")
        return value
    if isinstance(target, str):
        if not isinstance(value, str):
            raise ConfigError(f"{where}: oczekiwano tekstu, dostano {value!r}")
        return value
    if isinstance(target, list):
        if not isinstance(value, list):
            raise ConfigError(f"{where}: oczekiwano listy, dostano {value!r}")
        return list(value)
    if isinstance(target, dict):
        if not isinstance(value, dict):
            raise ConfigError(f"{where}: oczekiwano tabeli, dostano {value!r}")
        return dict(value)
    return value


def _fill(section: Any, data: dict[str, Any], prefix: str) -> None:
    known = {f.name for f in fields(section)}
    for key, value in data.items():
        where = f"[{prefix}].{key}"
        if key not in known:
            raise ConfigError(f"{where}: nieznane ustawienie")
        setattr(section, key, _coerce(value, getattr(section, key), where))


def from_dict(data: dict[str, Any], source: Path | None = None) -> Config:
    cfg = Config(source=source)
    for f in fields(cfg):
        if f.name == "source":
            continue
        section = getattr(cfg, f.name)
        if not is_dataclass(section):
            continue
        raw = data.get(f.name, {})
        if not isinstance(raw, dict):
            raise ConfigError(f"[{f.name}]: oczekiwano sekcji")
        if f.name == "child":
            raw = dict(raw)
            birth = raw.pop("birth_date", None)
            if birth is not None:
                cfg.child.birth_date = _parse_date(birth)
        _fill(section, raw, f.name)
    _validate(cfg)
    return cfg


def _parse_date(value: Any) -> date:
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value.strip())
        except ValueError as exc:
            raise ConfigError(f"[child].birth_date: {exc}") from exc
    raise ConfigError(f"[child].birth_date: oczekiwano daty YYYY-MM-DD, dostano {value!r}")


def _validate(cfg: Config) -> None:
    sel = cfg.selection
    if sel.min_per_month < 1:
        raise ConfigError("[selection].min_per_month musi byc >= 1")
    if sel.max_per_month < sel.min_per_month:
        raise ConfigError("[selection].max_per_month musi byc >= min_per_month")
    if sel.max_per_day < 1:
        raise ConfigError("[selection].max_per_day musi byc >= 1")
    if sel.burst_gap_seconds <= 0:
        raise ConfigError("[selection].burst_gap_seconds musi byc > 0")
    if not 0.0 < cfg.identity.threshold < 1.0:
        raise ConfigError("[identity].threshold musi byc w (0, 1)")
    if cfg.identity.max_refs_per_period < cfg.identity.min_refs_per_period:
        raise ConfigError("[identity].max_refs_per_period musi byc >= min_refs_per_period")
    if not 0.0 <= cfg.faces.min_det_score <= 1.0:
        raise ConfigError("[faces].min_det_score musi byc w <0, 1>")
    if not 1 <= cfg.build.jpeg_quality <= 100:
        raise ConfigError("[build].jpeg_quality musi byc w <1, 100>")
    if cfg.build.max_edge_px < 200:
        raise ConfigError("[build].max_edge_px musi byc >= 200")
    for name, weight in cfg.scoring.weights.items():
        if not isinstance(weight, (int, float)) or isinstance(weight, bool) or weight < 0:
            raise ConfigError(f"[scoring.weights].{name} musi byc liczba >= 0")
    if sum(cfg.scoring.weights.values()) <= 0:
        raise ConfigError("[scoring.weights]: suma wag musi byc > 0")


def load(path: Path | None = None) -> Config:
    """Wczytuje konfiguracje; brak pliku to blad z podpowiedzia `timemachine init`."""
    target = Path(path).expanduser() if path else config_path()
    if not target.exists():
        raise ConfigError(
            f"Nie znaleziono {target}. Uruchom `timemachine init`, zeby utworzyc szablon."
        )
    with open(target, "rb") as fh:
        data = tomllib.load(fh)
    return from_dict(data, source=target)


def default_toml() -> str:
    """Szablon konfiguracji zapisywany przez `timemachine init`."""
    d = DEFAULTS
    raw_ext = ", ".join(f'"{e}"' for e in d.archive.extensions_raw)
    providers = ", ".join(f'"{p}"' for p in d.faces.providers)
    return f"""# timemachine -- konfiguracja lokalna. Wszystko dziala offline.

[child]
name = "Corka"
# WYMAGANE: data urodzenia. Z niej licza sie okresy zycia (wielookresowy wzorzec
# twarzy) oraz wiek wypisywany na osi czasu.
birth_date = "2023-01-01"

[archive]
# Katalogi archiwum. Sa czytane WYLACZNIE do odczytu -- nic tu nie jest zapisywane,
# przenoszone ani zmieniane. Mozna tez podac sciezke wprost: `timemachine index /Volumes/...`
roots = []
extensions_jpg = [".jpg", ".jpeg"]
extensions_raw = [{raw_ext}]
extensions_heic = [".heic", ".heif"]
# RAW i JPG tej samej klatki (ten sam katalog, ta sama nazwa, ten sam czas EXIF)
# traktowane jako jedno zdjecie; do analizy uzywany jest JPG.
pair_raw_with_jpg = {str(d.archive.pair_raw_with_jpg).lower()}
follow_symlinks = {str(d.archive.follow_symlinks).lower()}

[faces]
backend = "{d.faces.backend}"
model = "{d.faces.model}"
det_size = {d.faces.det_size}
# Ponizej tego progu detekcji twarz nie jest w ogole brana pod uwage.
min_det_score = {d.faces.min_det_score}
providers = [{providers}]
max_faces_per_frame = {d.faces.max_faces_per_frame}
analysis_max_edge = {d.faces.analysis_max_edge}

[identity]
# Prog podobienstwa kosinusowego do puli referencyjnej corki.
threshold = {d.identity.threshold}
# Gdy w danym okresie zycia jest za malo referencji, prog jest podnoszony o tyle
# (przy niepewnosci wolimy przeoczyc zdjecie niz wpuscic obce dziecko).
thin_pool_penalty = {d.identity.thin_pool_penalty}
min_refs_per_period = {d.identity.min_refs_per_period}
max_refs_per_period = {d.identity.max_refs_per_period}
# Ile sasiednich okresow dolaczyc do puli przy dopasowaniu.
neighbor_span = {d.identity.neighbor_span}
tau_months = {d.identity.tau_months}
time_bonus = {d.identity.time_bonus}
top_k = {d.identity.top_k}

[scoring]
# Usmiech to premia doliczana ponad sume wag -- nigdy warunek konieczny.
smile_bonus = {d.scoring.smile_bonus}
learning_rate = {d.scoring.learning_rate}
min_samples = {d.scoring.min_samples}

[scoring.weights]
identity = {d.scoring.weights["identity"]}
sharpness = {d.scoring.weights["sharpness"]}
eyes = {d.scoring.weights["eyes"]}
exposure = {d.scoring.weights["exposure"]}
face_size = {d.scoring.weights["face_size"]}

[selection]
min_per_month = {d.selection.min_per_month}
max_per_month = {d.selection.max_per_month}
max_per_day = {d.selection.max_per_day}
burst_gap_seconds = {d.selection.burst_gap_seconds}

[build]
# Katalog wyjsciowy MUSI lezec poza archiwum -- narzedzie to sprawdza.
output_dir = "{d.build.output_dir}"
max_edge_px = {d.build.max_edge_px}
thumb_edge_px = {d.build.thumb_edge_px}
jpeg_quality = {d.build.jpeg_quality}
"""
