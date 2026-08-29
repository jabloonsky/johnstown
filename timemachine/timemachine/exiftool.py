"""Zapasowa sciezka przez exiftool -- dla formatow, ktorych nie parsujemy sami.

Dotyczy przede wszystkim Canon CR3 i HEIC (kontener ISO-BMFF). Wywolania sa
wylacznie odczytowe: nigdy nie przekazujemy exiftoolowi zadnej opcji zapisu, a
podglad wraca na stdout i ladujemy go do pamieci -- exiftool nie dotyka archiwum.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from .exif import ExifData, parse_exif_datetime

__all__ = ["available", "read_exif", "extract_preview"]

_TIMEOUT = 20

_TAGS = (
    "-DateTimeOriginal",
    "-CreateDate",
    "-SubSecTimeOriginal",
    "-Make",
    "-Model",
    "-LensModel",
    "-ISO",
    "-FNumber",
    "-ExposureTime",
    "-Orientation",
    "-ImageWidth",
    "-ImageHeight",
)


def available() -> bool:
    return shutil.which("exiftool") is not None


def _run(args: list[str]) -> bytes | None:
    try:
        result = subprocess.run(
            ["exiftool", *args],
            capture_output=True,
            timeout=_TIMEOUT,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0 or not result.stdout:
        return None
    return result.stdout


def read_exif(path: str | Path) -> ExifData:
    """Czyta metadane przez exiftool. Blad albo brak narzedzia -> pusty wynik."""
    out = _run(["-json", "-n", "-q", "-q", *_TAGS, str(path)])
    if not out:
        return ExifData()
    try:
        records = json.loads(out.decode("utf-8", "replace"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return ExifData()
    if not records:
        return ExifData()
    tags = records[0]

    def num(key: str, cast):
        value = tags.get(key)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return cast(value)
        return None

    capture = parse_exif_datetime(
        tags.get("DateTimeOriginal") or tags.get("CreateDate"),
        tags.get("SubSecTimeOriginal"),
    )
    make = tags.get("Make")
    model = tags.get("Model")
    lens = tags.get("LensModel")
    return ExifData(
        capture=capture,
        sub_sec=num("SubSecTimeOriginal", int),
        camera_make=make if isinstance(make, str) else None,
        camera_model=model if isinstance(model, str) else None,
        lens_model=lens if isinstance(lens, str) else None,
        iso=num("ISO", int),
        f_number=num("FNumber", float),
        exposure_time=num("ExposureTime", float),
        orientation=num("Orientation", int),
        width=num("ImageWidth", int),
        height=num("ImageHeight", int),
        source="exiftool" if isinstance(capture, datetime) or tags else "none",
    )


def extract_preview(path: str | Path) -> bytes | None:
    """Najwiekszy dostepny podglad JPEG wbudowany w plik -- jako bajty na stdout.

    Kolejnosc prob odpowiada malejacej rozdzielczosci podgladow w plikach RAW.
    """
    for tag in ("-JpgFromRaw", "-PreviewImage", "-OtherImage", "-ThumbnailImage"):
        data = _run(["-b", tag, str(path)])
        if data and data[:2] == b"\xff\xd8":
            return data
    return None
