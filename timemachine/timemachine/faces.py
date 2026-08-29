"""Detekcja twarzy i embeddingi -- insightface, lokalnie i offline.

Model (domyslnie buffalo_l) pobiera sie JEDEN RAZ przy pierwszym uruchomieniu do
~/.insightface/models. Potem calosc dziala bez sieci. Zdjecia nigdy nie opuszczaja
maszyny -- nie ma tu zadnego wywolania sieciowego poza tym jednorazowym pobraniem
modelu.

Import insightface jest leniwy i zamkniety w tej klasie, zeby reszta pakietu
(scoring, selekcja, generator HTML) dzialala i testowala sie bez niego.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Sequence

from . import caps

__all__ = ["DetectedFace", "FaceEngine"]


@dataclass
class DetectedFace:
    bbox: tuple[int, int, int, int]  # x, y, szerokosc, wysokosc
    det_score: float
    embedding: list[float]
    keypoints: list[tuple[float, float]] = field(default_factory=list)  # 5 punktow
    landmarks_106: list[tuple[float, float]] | None = None
    yaw: float | None = None
    pitch: float | None = None

    @property
    def area(self) -> int:
        return self.bbox[2] * self.bbox[3]


class FaceEngine:
    """Cienka otoczka na insightface.FaceAnalysis, ladowana leniwie."""

    def __init__(
        self,
        model: str = "buffalo_l",
        *,
        det_size: int = 640,
        providers: Sequence[str] | None = None,
        max_faces: int = 12,
    ):
        self.model = model
        self.det_size = det_size
        self.providers = list(providers or ["CPUExecutionProvider"])
        self.max_faces = max_faces
        self._app: Any = None

    # ── ladowanie ─────────────────────────────────────────────────────────────

    def _available_providers(self) -> list[str]:
        import onnxruntime  # noqa: PLC0415

        supported = set(onnxruntime.get_available_providers())
        chosen = [p for p in self.providers if p in supported]
        if "CPUExecutionProvider" not in chosen:
            chosen.append("CPUExecutionProvider")
        return chosen

    def load(self) -> Any:
        """Laduje model. Pierwsze wywolanie moze pobrac wagi (jednorazowo)."""
        if self._app is not None:
            return self._app
        caps.require("insightface", "onnxruntime", "numpy", purpose="Rozpoznawanie twarzy")
        from insightface.app import FaceAnalysis  # noqa: PLC0415

        app = FaceAnalysis(name=self.model, providers=self._available_providers())
        app.prepare(ctx_id=0, det_size=(self.det_size, self.det_size))
        self._app = app
        return app

    @property
    def embed_model(self) -> str:
        return self.model

    # ── detekcja ──────────────────────────────────────────────────────────────

    def detect(self, rgb: Any) -> list[DetectedFace]:
        """Znajduje twarze na obrazie RGB (uint8, HxWx3). Zwraca od najwiekszej."""
        app = self.load()
        from .images import to_bgr  # noqa: PLC0415 - unikamy cyklu importow

        raw_faces = app.get(to_bgr(rgb))
        height, width = rgb.shape[:2]

        found: list[DetectedFace] = []
        for face in raw_faces:
            x1, y1, x2, y2 = (int(round(v)) for v in face.bbox[:4])
            x1, y1 = max(x1, 0), max(y1, 0)
            x2, y2 = min(x2, width), min(y2, height)
            if x2 <= x1 or y2 <= y1:
                continue
            embedding = getattr(face, "normed_embedding", None)
            if embedding is None:
                embedding = getattr(face, "embedding", None)
            found.append(
                DetectedFace(
                    bbox=(x1, y1, x2 - x1, y2 - y1),
                    det_score=float(getattr(face, "det_score", 0.0)),
                    embedding=[float(v) for v in embedding] if embedding is not None else [],
                    keypoints=[(float(p[0]), float(p[1])) for p in getattr(face, "kps", [])],
                    landmarks_106=_landmarks_106(face),
                    yaw=_pose_component(face, 1),
                    pitch=_pose_component(face, 0),
                )
            )

        found.sort(key=lambda f: f.area, reverse=True)
        return found[: self.max_faces]


def _landmarks_106(face: Any) -> list[tuple[float, float]] | None:
    points = getattr(face, "landmark_2d_106", None)
    if points is None:
        return None
    return [(float(p[0]), float(p[1])) for p in points]


def _pose_component(face: Any, index: int) -> float | None:
    pose = getattr(face, "pose", None)
    if pose is None or len(pose) <= index:
        return None
    return float(pose[index])
