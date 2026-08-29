"""Budowanie syntetycznych plikow JPEG z EXIF-em -- bez zadnych zaleznosci.

Dzieki temu testy skanera i parsera EXIF dzialaja na golym Pythonie: nie trzeba
Pillow ani prawdziwego archiwum, a mimo to sprawdzamy realny format pliku.
"""
from __future__ import annotations

import struct
from pathlib import Path

# typy TIFF
ASCII, SHORT, LONG, RATIONAL = 2, 3, 4, 5

TAG_MAKE = 0x010F
TAG_MODEL = 0x0110
TAG_ORIENTATION = 0x0112
TAG_EXIF_IFD = 0x8769
TAG_EXPOSURE = 0x829A
TAG_FNUMBER = 0x829D
TAG_ISO = 0x8827
TAG_DATETIME_ORIGINAL = 0x9003
TAG_SUBSEC = 0x9291
TAG_PIXEL_X = 0xA002
TAG_PIXEL_Y = 0xA003


def _ascii(text: str) -> bytes:
    return text.encode("ascii") + b"\x00"


def _rational(numerator: int, denominator: int) -> bytes:
    return struct.pack("<II", numerator, denominator)


def _layout_ifd(entries: list[tuple[int, int, int, bytes]], ifd_offset: int) -> tuple[bytes, bytes, int]:
    """Zwraca (bajty IFD, bajty obszaru wartosci, offset za obszarem wartosci)."""
    entries = sorted(entries, key=lambda e: e[0])
    ifd_size = 2 + 12 * len(entries) + 4
    value_offset = ifd_offset + ifd_size

    packed = struct.pack("<H", len(entries))
    values = b""
    cursor = value_offset
    for tag, type_id, count, raw in entries:
        if len(raw) <= 4:
            payload = raw.ljust(4, b"\x00")
        else:
            payload = struct.pack("<I", cursor)
            padded = raw + (b"\x00" if len(raw) % 2 else b"")
            values += padded
            cursor += len(padded)
        packed += struct.pack("<HHI", tag, type_id, count) + payload
    packed += struct.pack("<I", 0)  # brak kolejnego IFD
    return packed, values, cursor


def build_exif_tiff(
    *,
    datetime_original: str | None = "2025:08:14 10:11:12",
    sub_sec: str | None = "25",
    make: str | None = "Canon",
    model: str | None = "Canon EOS R5",
    orientation: int = 1,
    iso: int = 400,
    f_number: tuple[int, int] = (18, 10),
    exposure: tuple[int, int] = (1, 250),
    width: int = 6000,
    height: int = 4000,
) -> bytes:
    """Blok TIFF/EXIF (little-endian) z typowym zestawem tagow aparatu."""
    exif_entries: list[tuple[int, int, int, bytes]] = [
        (TAG_ISO, SHORT, 1, struct.pack("<H", iso)),
        (TAG_FNUMBER, RATIONAL, 1, _rational(*f_number)),
        (TAG_EXPOSURE, RATIONAL, 1, _rational(*exposure)),
        (TAG_PIXEL_X, LONG, 1, struct.pack("<I", width)),
        (TAG_PIXEL_Y, LONG, 1, struct.pack("<I", height)),
    ]
    if datetime_original:
        raw = _ascii(datetime_original)
        exif_entries.append((TAG_DATETIME_ORIGINAL, ASCII, len(raw), raw))
    if sub_sec:
        raw = _ascii(sub_sec)
        exif_entries.append((TAG_SUBSEC, ASCII, len(raw), raw))

    ifd0_entries: list[tuple[int, int, int, bytes]] = [
        (TAG_ORIENTATION, SHORT, 1, struct.pack("<H", orientation)),
    ]
    if make:
        raw = _ascii(make)
        ifd0_entries.append((TAG_MAKE, ASCII, len(raw), raw))
    if model:
        raw = _ascii(model)
        ifd0_entries.append((TAG_MODEL, ASCII, len(raw), raw))
    # Wskaznik na ExifIFD wypelnimy po policzeniu rozmiarow.
    ifd0_entries.append((TAG_EXIF_IFD, LONG, 1, b"\x00\x00\x00\x00"))

    ifd0_offset = 8
    ifd0_bytes, ifd0_values, after_ifd0 = _layout_ifd(ifd0_entries, ifd0_offset)
    exif_offset = after_ifd0
    exif_bytes, exif_values, _ = _layout_ifd(exif_entries, exif_offset)

    # Podmieniamy payload wpisu ExifIFD na policzony offset.
    sorted_tags = sorted(e[0] for e in ifd0_entries)
    slot = 2 + 12 * sorted_tags.index(TAG_EXIF_IFD) + 8
    ifd0_bytes = (
        ifd0_bytes[:slot] + struct.pack("<I", exif_offset) + ifd0_bytes[slot + 4 :]
    )

    header = b"II" + struct.pack("<HI", 42, ifd0_offset)
    return header + ifd0_bytes + ifd0_values + exif_bytes + exif_values


def build_jpeg(**kwargs) -> bytes:
    """Minimalny plik JPEG z segmentem APP1/Exif. Pikseli nie zawiera."""
    padding = kwargs.pop("padding", 0)
    tiff = build_exif_tiff(**kwargs)
    payload = b"Exif\x00\x00" + tiff
    app1 = b"\xff\xe1" + struct.pack(">H", len(payload) + 2) + payload
    return b"\xff\xd8" + app1 + b"\x00" * padding + b"\xff\xd9"


def write_jpeg(path: Path, **kwargs) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(build_jpeg(**kwargs))
    return path


def write_raw(path: Path, **kwargs) -> Path:
    """Plik "RAW" jako goly TIFF -- tak wygladaja CR2/NEF/ARW od strony EXIF."""
    path.parent.mkdir(parents=True, exist_ok=True)
    padding = kwargs.pop("padding", 0)
    with open(path, "wb") as fh:
        fh.write(build_exif_tiff(**kwargs) + b"\x00" * padding)
    return path
