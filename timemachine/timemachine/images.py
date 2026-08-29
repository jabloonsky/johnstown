"""Dekodowanie zdjec do tablicy pikseli -- zawsze tylko do odczytu.

Kolejnosc dla plikow RAW jest celowa: siegamy po PODGLAD wbudowany w plik
(rawpy.extract_thumb, a jak sie nie da -- exiftool). Pelnego demozaikowania nie
robimy nigdy: dla dziesiatek tysiecy plikow byloby to godziny pracy, a do
znalezienia i ocenienia twarzy podglad w pelni wystarcza. Plik, z ktorego nie da
sie wyciagnac podgladu, jest pomijany i logowany.
"""
from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import caps, exiftool, safety

__all__ = ["DecodedImage", "UnsupportedImage", "load_rgb", "to_bgr", "fit_within"]


class UnsupportedImage(Exception):
    """Nie da sie wyciagnac pikseli z tego pliku (np. RAW bez podgladu)."""


@dataclass
class DecodedImage:
    """Piksele RGB (uint8, HxWx3) plus informacja, skad je wzielismy."""

    pixels: Any
    source: str
    width: int
    height: int


def fit_within(width: int, height: int, max_edge: int) -> tuple[int, int]:
    """Skaluje wymiary tak, by dluzszy bok mial najwyzej `max_edge` pikseli."""
    longest = max(width, height)
    if max_edge <= 0 or longest <= max_edge:
        return width, height
    scale = max_edge / longest
    return max(int(round(width * scale)), 1), max(int(round(height * scale)), 1)


def _pil():
    caps.require("pillow", purpose="Dekodowanie zdjec")
    from PIL import Image, ImageOps  # noqa: PLC0415 - import leniwy z zalozenia

    return Image, ImageOps


def _numpy():
    caps.require("numpy", purpose="Analiza pikseli")
    import numpy  # noqa: PLC0415

    return numpy


def _from_pil(image, source: str, max_edge: int | None) -> DecodedImage:
    Image, ImageOps = _pil()
    np = _numpy()
    image = ImageOps.exif_transpose(image)
    if image.mode != "RGB":
        image = image.convert("RGB")
    if max_edge:
        width, height = fit_within(image.width, image.height, max_edge)
        if (width, height) != (image.width, image.height):
            image = image.resize((width, height), Image.LANCZOS)
    array = np.asarray(image, dtype=np.uint8)
    return DecodedImage(array, source, image.width, image.height)


def _decode_bytes(data: bytes, source: str, max_edge: int | None) -> DecodedImage:
    Image, _ = _pil()
    with Image.open(io.BytesIO(data)) as image:
        image.load()
        return _from_pil(image, source, max_edge)


def _load_jpeg(path: Path, max_edge: int | None) -> DecodedImage:
    Image, _ = _pil()
    with safety.open_readonly(path) as fh:
        with Image.open(fh) as image:
            image.load()
            return _from_pil(image, "jpg", max_edge)


def _load_raw(path: Path, max_edge: int | None) -> DecodedImage:
    if caps.have("rawpy"):
        import rawpy  # noqa: PLC0415

        try:
            with safety.open_readonly(path) as fh:
                with rawpy.imread(fh) as raw:
                    thumb = raw.extract_thumb()
            if thumb.format == rawpy.ThumbFormat.JPEG:
                return _decode_bytes(thumb.data, "raw_embedded", max_edge)
            if thumb.format == rawpy.ThumbFormat.BITMAP:
                np = _numpy()
                array = np.asarray(thumb.data, dtype=np.uint8)
                return DecodedImage(array, "raw_embedded", array.shape[1], array.shape[0])
        except Exception:  # rawpy rzuca wlasnymi wyjatkami dla plikow bez podgladu
            pass

    if exiftool.available():
        data = exiftool.extract_preview(path)
        if data:
            return _decode_bytes(data, "raw_exiftool", max_edge)

    raise UnsupportedImage(
        "Brak wbudowanego podgladu w pliku RAW "
        "(zainstaluj rawpy albo exiftool, jesli to nieoczekiwane)"
    )


def _load_heic(path: Path, max_edge: int | None) -> DecodedImage:
    try:
        import pillow_heif  # noqa: PLC0415

        pillow_heif.register_heif_opener()
        return _load_jpeg(path, max_edge)
    except ImportError:
        pass
    if exiftool.available():
        data = exiftool.extract_preview(path)
        if data:
            return _decode_bytes(data, "heic_exiftool", max_edge)
    raise UnsupportedImage("HEIC wymaga pillow-heif albo exiftool")


def load_rgb(path: str | Path, kind: str, *, max_edge: int | None = None) -> DecodedImage:
    """Wczytuje piksele RGB. Podnosi UnsupportedImage, gdy sie nie da."""
    target = Path(path)
    if kind == "jpg":
        return _load_jpeg(target, max_edge)
    if kind == "raw":
        return _load_raw(target, max_edge)
    if kind == "heic":
        return _load_heic(target, max_edge)
    raise UnsupportedImage(f"Nieznany rodzaj pliku: {kind}")


def to_bgr(pixels):
    """insightface oczekuje BGR (konwencja OpenCV)."""
    return pixels[:, :, ::-1]
