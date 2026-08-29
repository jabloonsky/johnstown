"""Wykrywanie opcjonalnych zaleznosci i uprzejme degradowanie funkcji.

Rdzen pakietu dziala na samej bibliotece standardowej. Wszystko, co ciezkie
(Pillow, numpy, insightface, onnxruntime, rawpy, exiftool) jest opcjonalne,
importowane leniwie i opisane tutaj, zeby `timemachine doctor` mogl pokazac
jedna tabelke: co jest, czego nie ma i co przez to nie zadziala.
"""
from __future__ import annotations

import importlib.metadata
import importlib.util
import shutil
from dataclasses import dataclass, field

__all__ = ["Capability", "MissingDependency", "probe", "have", "require", "format_report"]


class MissingDependency(Exception):
    """Brak opcjonalnej zaleznosci potrzebnej do danej komendy."""


@dataclass(frozen=True)
class Capability:
    key: str
    label: str
    enables: str
    install: str
    available: bool = False
    version: str | None = None
    detail: str = ""


@dataclass
class _Spec:
    key: str
    label: str
    enables: str
    install: str
    module: str | None = None
    distribution: str | None = None
    binary: str | None = None
    needs: tuple[str, ...] = field(default_factory=tuple)


_SPECS: tuple[_Spec, ...] = (
    _Spec(
        key="pillow",
        label="Pillow",
        enables="dekodowanie JPG, miniatury, eksport osi czasu",
        install='pip install "timemachine[images]"',
        module="PIL",
        distribution="pillow",
    ),
    _Spec(
        key="numpy",
        label="numpy",
        enables="szybkie metryki jakosci i podobienstwo embeddingow",
        install='pip install "timemachine[faces]"',
        module="numpy",
        distribution="numpy",
    ),
    _Spec(
        key="onnxruntime",
        label="onnxruntime",
        enables="uruchamianie modeli twarzy (CoreML/CPU na Apple Silicon)",
        install='pip install "timemachine[faces]"',
        module="onnxruntime",
        distribution="onnxruntime",
    ),
    _Spec(
        key="insightface",
        label="insightface",
        enables="detekcja twarzy, embeddingi, landmarki",
        install='pip install "timemachine[faces]"',
        module="insightface",
        distribution="insightface",
        needs=("numpy", "onnxruntime"),
    ),
    _Spec(
        key="rawpy",
        label="rawpy",
        enables="podglady wbudowane w pliki RAW",
        install='pip install "timemachine[raw]"',
        module="rawpy",
        distribution="rawpy",
    ),
    _Spec(
        key="exiftool",
        label="exiftool",
        enables="zapasowe czytanie EXIF i podgladow z RAW (np. Canon CR3)",
        install="brew install exiftool",
        binary="exiftool",
    ),
)


def _version(distribution: str | None) -> str | None:
    if not distribution:
        return None
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return None


def probe() -> dict[str, Capability]:
    """Sprawdza dostepnosc bez importowania ciezkich modulow."""
    found: dict[str, Capability] = {}
    for spec in _SPECS:
        if spec.binary:
            path = shutil.which(spec.binary)
            available, version, detail = bool(path), None, path or ""
        else:
            available = importlib.util.find_spec(spec.module) is not None if spec.module else False
            version = _version(spec.distribution) if available else None
            detail = ""
        missing = [n for n in spec.needs if n in found and not found[n].available]
        if available and missing:
            available = False
            detail = "brak: " + ", ".join(missing)
        found[spec.key] = Capability(
            key=spec.key,
            label=spec.label,
            enables=spec.enables,
            install=spec.install,
            available=available,
            version=version,
            detail=detail,
        )
    return found


def have(key: str, caps: dict[str, Capability] | None = None) -> bool:
    caps = caps if caps is not None else probe()
    cap = caps.get(key)
    return bool(cap and cap.available)


def require(*keys: str, purpose: str = "ta operacja") -> None:
    """Podnosi czytelny blad zamiast ImportError w srodku petli po 40 tys. plikow."""
    caps = probe()
    missing = [caps[k] for k in keys if k in caps and not caps[k].available]
    if not missing:
        return
    lines = [f"{purpose} wymaga brakujacych zaleznosci:"]
    for cap in missing:
        suffix = f" ({cap.detail})" if cap.detail else ""
        lines.append(f"  - {cap.label}{suffix}: {cap.install}")
    raise MissingDependency("\n".join(lines))


def format_report() -> str:
    """Tabelka dla `timemachine doctor`."""
    caps = probe()
    width = max(len(c.label) for c in caps.values())
    lines = []
    for cap in caps.values():
        mark = "OK  " if cap.available else "BRAK"
        version = cap.version or cap.detail or ("znaleziony" if cap.available else "")
        lines.append(f"  [{mark}] {cap.label:<{width}}  {version:<12}  {cap.enables}")
        if not cap.available:
            lines.append(f"         {'':<{width}}  -> {cap.install}")
    return "\n".join(lines)
