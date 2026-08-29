"""Czytanie EXIF bez zadnych zaleznosci -- wlasny, ostrozny parser TIFF/EXIF.

Obsluguje dwa najczestsze przypadki w archiwum fotografa:
  * JPEG -- segment APP1 z naglowkiem "Exif\\0\\0",
  * pliki RAW oparte o TIFF (CR2, NEF, ARW, DNG, RW2, ORF, PEF, SRW) -- naglowek
    TIFF na poczatku pliku.

Formaty oparte o ISO-BMFF (Canon CR3, HEIC) nie sa tu parsowane -- dla nich
`read_exif` zwraca pusty wynik, a wyzsza warstwa siega po exiftool.

Czytamy wylacznie fragmenty, ktore sa naprawde potrzebne (seek + kilkaset bajtow),
zeby indeksowanie dziesiatek tysiecy plikow na dysku zewnetrznym nie sprowadzalo
sie do przeczytania calego archiwum.
"""
from __future__ import annotations

import struct
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, BinaryIO

from . import safety

__all__ = ["ExifData", "read_exif", "parse_exif_bytes", "parse_exif_datetime"]

# ── tagi, ktore nas interesuja ───────────────────────────────────────────────

_TAG_EXIF_IFD = 0x8769

_IFD0_TAGS = {
    0x0100: "image_width",
    0x0101: "image_height",
    0x010F: "camera_make",
    0x0110: "camera_model",
    0x0112: "orientation",
    0x0132: "datetime",
}

_EXIF_TAGS = {
    0x829A: "exposure_time",
    0x829D: "f_number",
    0x8827: "iso",
    0x9003: "datetime_original",
    0x9004: "datetime_digitized",
    0x9291: "sub_sec_original",
    0xA002: "pixel_width",
    0xA003: "pixel_height",
    0xA434: "lens_model",
}

# rozmiar w bajtach dla typow TIFF
_TYPE_SIZES = {1: 1, 2: 1, 3: 2, 4: 4, 5: 8, 6: 1, 7: 1, 8: 2, 9: 4, 10: 8, 11: 4, 12: 8}

_MAX_IFD_ENTRIES = 512
_MAX_VALUE_BYTES = 4096


@dataclass
class ExifData:
    """Znormalizowany wynik -- wszystkie pola opcjonalne."""

    capture: datetime | None = None
    sub_sec: int | None = None
    camera_make: str | None = None
    camera_model: str | None = None
    lens_model: str | None = None
    iso: int | None = None
    f_number: float | None = None
    exposure_time: float | None = None
    orientation: int | None = None
    width: int | None = None
    height: int | None = None
    source: str = "none"  # 'jpeg' | 'tiff' | 'exiftool' | 'none'

    @property
    def camera(self) -> str | None:
        parts = [p for p in (self.camera_make, self.camera_model) if p]
        if not parts:
            return None
        # Wiele aparatow powtarza producenta w modelu ("NIKON" + "NIKON Z 6").
        if len(parts) == 2 and parts[1].upper().startswith(parts[0].upper()):
            return parts[1]
        return " ".join(parts)


# ── zrodla bajtow ────────────────────────────────────────────────────────────


class _Source:
    """Dostep do bajtow po offsetach -- z bufora albo z otwartego pliku."""

    def __init__(self, data: bytes | None = None, fh: BinaryIO | None = None, size: int = 0):
        self._data = data
        self._fh = fh
        self.size = len(data) if data is not None else size

    def read(self, offset: int, length: int) -> bytes:
        if offset < 0 or length <= 0 or offset >= self.size:
            return b""
        length = min(length, self.size - offset)
        if self._data is not None:
            return self._data[offset : offset + length]
        assert self._fh is not None
        self._fh.seek(offset)
        return self._fh.read(length)


# ── parser TIFF ──────────────────────────────────────────────────────────────


def _decode_value(raw: bytes, type_id: int, count: int, endian: str) -> Any:
    if type_id == 2:  # ASCII
        return raw.split(b"\x00", 1)[0].decode("utf-8", "replace").strip() or None
    fmt = {1: "B", 3: "H", 4: "I", 6: "b", 8: "h", 9: "i", 11: "f", 12: "d"}.get(type_id)
    if fmt:
        size = _TYPE_SIZES[type_id]
        usable = min(count, len(raw) // size)
        if usable <= 0:
            return None
        values = struct.unpack(f"{endian}{usable}{fmt}", raw[: usable * size])
        return values[0] if usable == 1 else list(values)
    if type_id in (5, 10):  # RATIONAL / SRATIONAL
        fmt = "II" if type_id == 5 else "ii"
        if len(raw) < 8:
            return None
        num, den = struct.unpack(f"{endian}{fmt}", raw[:8])
        return float(num) / den if den else None
    if type_id == 7:  # UNDEFINED -- w praktyce tekst (np. SubSecTime)
        return raw.split(b"\x00", 1)[0].decode("utf-8", "replace").strip() or None
    return None


def _read_ifd(
    src: _Source, offset: int, endian: str, wanted: dict[int, str], base: int = 0
) -> tuple[dict, int | None]:
    """Czyta jeden IFD; zwraca (znalezione pola, wskaznik na ExifIFD).

    `base` to poczatek bloku TIFF w pliku -- offsety w tagach sa liczone wzgledem
    niego, a nie wzgledem poczatku pliku (w JPEG blok siedzi w segmencie APP1).
    """
    header = src.read(offset, 2)
    if len(header) < 2:
        return {}, None
    (count,) = struct.unpack(f"{endian}H", header)
    if count == 0 or count > _MAX_IFD_ENTRIES:
        return {}, None

    entries = src.read(offset + 2, count * 12)
    found: dict[str, Any] = {}
    exif_ptr: int | None = None

    for i in range(len(entries) // 12):
        tag, type_id, value_count, payload = struct.unpack(
            f"{endian}HHI4s", entries[i * 12 : i * 12 + 12]
        )
        if tag == _TAG_EXIF_IFD:
            (exif_ptr,) = struct.unpack(f"{endian}I", payload)
            continue
        name = wanted.get(tag)
        if not name:
            continue
        size = _TYPE_SIZES.get(type_id)
        if not size:
            continue
        total = size * value_count
        if total > _MAX_VALUE_BYTES:
            continue
        if total <= 4:
            raw = payload[:total]
        else:
            (value_offset,) = struct.unpack(f"{endian}I", payload)
            raw = src.read(base + value_offset, total)
        value = _decode_value(raw, type_id, value_count, endian)
        if value is not None:
            found[name] = value

    return found, exif_ptr


def _parse_tiff(src: _Source, base: int = 0) -> dict[str, Any]:
    magic = src.read(base, 8)
    if len(magic) < 8:
        return {}
    if magic[:2] == b"II":
        endian = "<"
    elif magic[:2] == b"MM":
        endian = ">"
    else:
        return {}
    (marker,) = struct.unpack(f"{endian}H", magic[2:4])
    if marker not in (42, 85):  # 42 = TIFF, 85 = Panasonic RW2
        return {}
    (ifd0_offset,) = struct.unpack(f"{endian}I", magic[4:8])

    fields, exif_ptr = _read_ifd(src, base + ifd0_offset, endian, _IFD0_TAGS, base)
    if exif_ptr:
        exif_fields, _ = _read_ifd(src, base + exif_ptr, endian, _EXIF_TAGS, base)
        fields.update(exif_fields)
    return fields


def _find_jpeg_exif(src: _Source) -> int | None:
    """Zwraca offset naglowka TIFF wewnatrz segmentu APP1, albo None."""
    if src.read(0, 2) != b"\xff\xd8":
        return None
    offset = 2
    # Segmenty naglowkowe siedza na poczatku pliku; nie skanujemy calego JPEG-a.
    while offset < min(src.size, 1 << 20):
        marker = src.read(offset, 4)
        if len(marker) < 4 or marker[0] != 0xFF:
            return None
        kind = marker[1]
        if kind in (0xD8, 0x01) or 0xD0 <= kind <= 0xD7:
            offset += 2
            continue
        if kind == 0xDA:  # poczatek danych obrazu -- dalej nie ma metadanych
            return None
        (length,) = struct.unpack(">H", marker[2:4])
        if length < 2:
            return None
        if kind == 0xE1 and src.read(offset + 4, 6) == b"Exif\x00\x00":
            return offset + 10
        offset += 2 + length
    return None


def parse_exif_datetime(text: str | None, sub_sec: Any = None) -> datetime | None:
    """"2023:04:12 10:11:12" -> datetime. Puste/zerowe daty traktujemy jak brak."""
    if not text or not isinstance(text, str):
        return None
    cleaned = text.strip().replace("/", ":")
    if cleaned.startswith("0000"):
        return None
    for fmt in ("%Y:%m:%d %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y:%m:%d %H:%M", "%Y-%m-%dT%H:%M:%S"):
        try:
            parsed = datetime.strptime(cleaned, fmt)
        except ValueError:
            continue
        if sub_sec is not None:
            digits = "".join(ch for ch in str(sub_sec) if ch.isdigit())[:6]
            if digits:
                parsed = parsed.replace(microsecond=int(digits.ljust(6, "0")))
        return parsed
    return None


def _normalize(fields: dict[str, Any], source: str) -> ExifData:
    def as_int(value: Any) -> int | None:
        if isinstance(value, list):
            value = value[0] if value else None
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return int(value)
        if isinstance(value, str) and value.strip().isdigit():
            return int(value.strip())
        return None

    def as_float(value: Any) -> float | None:
        if isinstance(value, list):
            value = value[0] if value else None
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value)
        return None

    def as_text(value: Any) -> str | None:
        if isinstance(value, str):
            return value.strip() or None
        return None

    sub_sec = fields.get("sub_sec_original")
    capture = parse_exif_datetime(
        fields.get("datetime_original")
        or fields.get("datetime_digitized")
        or fields.get("datetime"),
        sub_sec,
    )
    return ExifData(
        capture=capture,
        sub_sec=as_int(sub_sec),
        camera_make=as_text(fields.get("camera_make")),
        camera_model=as_text(fields.get("camera_model")),
        lens_model=as_text(fields.get("lens_model")),
        iso=as_int(fields.get("iso")),
        f_number=as_float(fields.get("f_number")),
        exposure_time=as_float(fields.get("exposure_time")),
        orientation=as_int(fields.get("orientation")),
        width=as_int(fields.get("pixel_width")) or as_int(fields.get("image_width")),
        height=as_int(fields.get("pixel_height")) or as_int(fields.get("image_height")),
        source=source if capture or fields else "none",
    )


def parse_exif_bytes(data: bytes) -> ExifData:
    """Parsuje EXIF z bufora -- uzywane w testach i dla malych plikow."""
    src = _Source(data=data)
    tiff_base = _find_jpeg_exif(src)
    if tiff_base is not None:
        return _normalize(_parse_tiff(src, tiff_base), "jpeg")
    return _normalize(_parse_tiff(src, 0), "tiff")


def read_exif(path: str | Path) -> ExifData:
    """Czyta EXIF z pliku archiwum (wylacznie odczyt, minimum operacji I/O)."""
    with safety.open_readonly(path) as fh:
        fh.seek(0, 2)
        size = fh.tell()
        src = _Source(fh=fh, size=size)
        tiff_base = _find_jpeg_exif(src)
        if tiff_base is not None:
            return _normalize(_parse_tiff(src, tiff_base), "jpeg")
        return _normalize(_parse_tiff(src, 0), "tiff")
