"""Metryki jakosci liczone NA CROPIE TWARZY, nie na calym kadrze.

To rozroznienie jest calym sensem tego modulu. Zdjecie z ostrym tlem i miekka
twarza ma swietna ostrosc "globalna" i jest bezuzyteczne. Tak samo ekspozycja:
liczy sie histogram twarzy, a nie sredni jasnosc kadru z niebem.

Crop jest przed pomiarem skalowany do kanonicznych 128x128. Bez tego zdjecie z
aparatu 45 Mpix wygrywaloby z 24 Mpix samym rozmiarem wycinka, a nie ostroscia.

Kazda metryka ma dwie implementacje: referencyjna w czystym Pythonie (uzywana w
testach, dziala bez zadnych zaleznosci) i szybka na numpy (uzywana w praktyce).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

__all__ = [
    "CROP_SIZE",
    "ExposureStats",
    "to_gray",
    "crop_face",
    "resize_gray",
    "laplacian_variance",
    "exposure_stats",
    "eye_aspect_ratio",
    "eye_openness_from_pixels",
    "smile_ratio",
]

CROP_SIZE = 128

Gray = Sequence[Sequence[float]]  # wartosci w <0, 1>


def _is_ndarray(value: Any) -> bool:
    return type(value).__module__.startswith("numpy") and hasattr(value, "shape")


# ── konwersje ────────────────────────────────────────────────────────────────


def to_gray(rgb: Any) -> Any:
    """RGB uint8 -> szarosc w <0, 1>. Wagi luminancji ITU-R BT.601."""
    if _is_ndarray(rgb):
        import numpy as np

        arr = rgb.astype(np.float32)
        return (0.299 * arr[..., 0] + 0.587 * arr[..., 1] + 0.114 * arr[..., 2]) / 255.0
    return [
        [(0.299 * px[0] + 0.587 * px[1] + 0.114 * px[2]) / 255.0 for px in row] for row in rgb
    ]


def crop_face(gray: Any, bbox: tuple[int, int, int, int], *, margin: float = 0.15) -> Any:
    """Wycina twarz z marginesem, przycinajac do granic obrazu."""
    x, y, w, h = bbox
    pad_x, pad_y = int(w * margin), int(h * margin)
    if _is_ndarray(gray):
        height, width = gray.shape[:2]
    else:
        height, width = len(gray), len(gray[0]) if gray else 0
    x0 = max(x - pad_x, 0)
    y0 = max(y - pad_y, 0)
    x1 = min(x + w + pad_x, width)
    y1 = min(y + h + pad_y, height)
    if x1 <= x0 or y1 <= y0:
        return gray[0:0] if _is_ndarray(gray) else []
    if _is_ndarray(gray):
        return gray[y0:y1, x0:x1]
    return [row[x0:x1] for row in gray[y0:y1]]


def resize_gray(gray: Any, size: int = CROP_SIZE) -> Any:
    """Skalowanie najblizszym sasiadem do kwadratu `size` x `size`.

    Najblizszy sasiad jest tu celowy: interpolacja dwuliniowa sama w sobie
    rozmywa obraz i zanizalaby wariancje Laplasjanu, czyli dokladnie to, co
    mierzymy.
    """
    if _is_ndarray(gray):
        import numpy as np

        height, width = gray.shape[:2]
        if height == 0 or width == 0:
            return np.zeros((size, size), dtype=np.float32)
        rows = (np.arange(size) * height // size).clip(0, height - 1)
        cols = (np.arange(size) * width // size).clip(0, width - 1)
        return gray[rows][:, cols]

    height = len(gray)
    width = len(gray[0]) if height else 0
    if height == 0 or width == 0:
        return [[0.0] * size for _ in range(size)]
    return [
        [gray[min(r * height // size, height - 1)][min(c * width // size, width - 1)]
         for c in range(size)]
        for r in range(size)
    ]


# ── ostrosc ──────────────────────────────────────────────────────────────────


def laplacian_variance(gray: Any) -> float:
    """Wariancja odpowiedzi Laplasjanu 3x3 -- klasyczna miara ostrosci."""
    if _is_ndarray(gray):
        import numpy as np

        if gray.shape[0] < 3 or gray.shape[1] < 3:
            return 0.0
        center = gray[1:-1, 1:-1]
        response = (
            gray[:-2, 1:-1] + gray[2:, 1:-1] + gray[1:-1, :-2] + gray[1:-1, 2:] - 4.0 * center
        )
        return float(response.var())

    height = len(gray)
    width = len(gray[0]) if height else 0
    if height < 3 or width < 3:
        return 0.0
    values = []
    for y in range(1, height - 1):
        for x in range(1, width - 1):
            values.append(
                gray[y - 1][x] + gray[y + 1][x] + gray[y][x - 1] + gray[y][x + 1]
                - 4.0 * gray[y][x]
            )
    mean = sum(values) / len(values)
    return sum((v - mean) ** 2 for v in values) / len(values)


# ── ekspozycja ───────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ExposureStats:
    mean: float
    clip_low: float   # udzial pikseli <= 0.02 (zatkane cienie)
    clip_high: float  # udzial pikseli >= 0.98 (przepalenia)

    @property
    def clipping(self) -> float:
        return self.clip_low + self.clip_high


def exposure_stats(gray: Any) -> ExposureStats:
    """Histogram cropu twarzy: jasnosc srednia i udzial skrajnosci."""
    if _is_ndarray(gray):
        import numpy as np

        if gray.size == 0:
            return ExposureStats(0.0, 0.0, 0.0)
        return ExposureStats(
            float(gray.mean()),
            float(np.count_nonzero(gray <= 0.02) / gray.size),
            float(np.count_nonzero(gray >= 0.98) / gray.size),
        )

    flat = [value for row in gray for value in row]
    if not flat:
        return ExposureStats(0.0, 0.0, 0.0)
    total = len(flat)
    return ExposureStats(
        sum(flat) / total,
        sum(1 for v in flat if v <= 0.02) / total,
        sum(1 for v in flat if v >= 0.98) / total,
    )


# ── oczy i usmiech ───────────────────────────────────────────────────────────


def eye_aspect_ratio(points: Sequence[Sequence[float]]) -> float:
    """EAR dla konturu oka: (wysokosc) / (szerokosc). Otwarte oko ~0.25-0.35.

    Punkty w kolejnosci: zewnetrzny kacik, gora-przod, gora-tyl, wewnetrzny
    kacik, dol-tyl, dol-przod (konwencja 6-punktowa).
    """
    if len(points) < 6:
        return 0.0
    def dist(a, b):
        return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5

    width = dist(points[0], points[3])
    if width <= 0:
        return 0.0
    height = (dist(points[1], points[5]) + dist(points[2], points[4])) / 2.0
    return height / width


def eye_openness_from_pixels(gray: Any, center: Sequence[float], radius: float) -> float:
    """Zapasowa ocena otwarcia oka, gdy mamy tylko srodek oka (5 landmarkow).

    Otwarte oko to ciemna zrenica otoczona jasnym bialkiem -- czyli duzy rozrzut
    jasnosci w malym okienku. Oko zamkniete jest plaskie jasnosciowo. Wynik jest
    heurystyka znormalizowana do <0, 1>, nie miara fizyczna.
    """
    radius = max(int(radius), 2)
    cx, cy = int(center[0]), int(center[1])
    if _is_ndarray(gray):
        height, width = gray.shape[:2]
    else:
        height, width = len(gray), len(gray[0]) if gray else 0
    x0, x1 = max(cx - radius, 0), min(cx + radius, width)
    y0, y1 = max(cy - radius, 0), min(cy + radius, height)
    if x1 <= x0 or y1 <= y0:
        return 0.0
    if _is_ndarray(gray):
        window = gray[y0:y1, x0:x1]
        spread = float(window.std())
    else:
        flat = [v for row in gray[y0:y1] for v in row[x0:x1]]
        mean = sum(flat) / len(flat)
        spread = (sum((v - mean) ** 2 for v in flat) / len(flat)) ** 0.5
    # 0.18 odchylenia standardowego to w praktyce wyraznie otwarte oko.
    return max(0.0, min(spread / 0.18, 1.0))


def smile_ratio(mouth_points: Sequence[Sequence[float]]) -> float:
    """Usmiech: uniesienie kacikow ust wzgledem srodka gornej wargi.

    Zwraca 0..1. To PREMIA -- brak usmiechu nigdy nie dyskwalifikuje zdjecia.
    Punkty: lewy kacik, prawy kacik, srodek gornej wargi, srodek dolnej wargi.
    """
    if len(mouth_points) < 4:
        return 0.0
    left, right, top, bottom = mouth_points[:4]
    width = ((left[0] - right[0]) ** 2 + (left[1] - right[1]) ** 2) ** 0.5
    if width <= 0:
        return 0.0
    corners_y = (left[1] + right[1]) / 2.0
    center_y = (top[1] + bottom[1]) / 2.0
    # W ukladzie obrazu os Y rosnie w dol, wiec uniesione kaciki maja mniejsze Y.
    lift = (center_y - corners_y) / width
    return max(0.0, min(lift / 0.12, 1.0))
