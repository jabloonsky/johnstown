"""Testy wlasnego parsera EXIF -- na prawdziwych bajtach, bez zaleznosci."""
from datetime import datetime

import pytest

from timemachine.exif import parse_exif_bytes, parse_exif_datetime

from .helpers import build_exif_tiff, build_jpeg


# ── parse_exif_datetime ──────────────────────────────────────────────────────

def test_parses_canonical_exif_datetime():
    assert parse_exif_datetime("2025:08:14 10:11:12") == datetime(2025, 8, 14, 10, 11, 12)


def test_applies_sub_seconds():
    parsed = parse_exif_datetime("2025:08:14 10:11:12", "25")
    assert parsed.microsecond == 250000


@pytest.mark.parametrize("value", [None, "", "   ", "0000:00:00 00:00:00", "nonsens"])
def test_rejects_empty_and_zero_dates(value):
    assert parse_exif_datetime(value) is None


# ── JPEG ─────────────────────────────────────────────────────────────────────

def test_reads_full_exif_from_jpeg():
    data = parse_exif_bytes(build_jpeg())

    assert data.capture == datetime(2025, 8, 14, 10, 11, 12, 250000)
    assert data.camera_make == "Canon"
    assert data.camera_model == "Canon EOS R5"
    assert data.iso == 400
    assert data.f_number == pytest.approx(1.8)
    assert data.exposure_time == pytest.approx(1 / 250)
    assert data.orientation == 1
    assert data.width == 6000
    assert data.height == 4000
    assert data.source == "jpeg"


def test_camera_property_avoids_duplicating_manufacturer():
    data = parse_exif_bytes(build_jpeg(make="NIKON", model="NIKON Z 6"))
    assert data.camera == "NIKON Z 6"

    data = parse_exif_bytes(build_jpeg(make="Canon", model="EOS R5"))
    assert data.camera == "Canon EOS R5"


def test_jpeg_without_date_returns_none_capture():
    data = parse_exif_bytes(build_jpeg(datetime_original=None, sub_sec=None))
    assert data.capture is None
    assert data.camera_make == "Canon"  # reszta metadanych nadal sie czyta


def test_survives_padding_before_end_marker():
    data = parse_exif_bytes(build_jpeg(padding=5000))
    assert data.capture == datetime(2025, 8, 14, 10, 11, 12, 250000)


# ── RAW oparty o TIFF ────────────────────────────────────────────────────────

def test_reads_exif_from_bare_tiff_like_raw():
    data = parse_exif_bytes(build_exif_tiff(make="SONY", model="ILCE-7RM4"))
    assert data.capture == datetime(2025, 8, 14, 10, 11, 12, 250000)
    assert data.camera == "SONY ILCE-7RM4"
    assert data.source == "tiff"


# ── odpornosc ────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "data",
    [b"", b"\xff\xd8", b"\xff\xd8\xff\xd9", b"nie jest to zdjecie", b"II\x2a\x00"],
)
def test_garbage_input_never_raises(data):
    result = parse_exif_bytes(data)
    assert result.capture is None


def test_truncated_jpeg_exif_is_handled():
    truncated = build_jpeg()[:40]
    assert parse_exif_bytes(truncated).capture is None
