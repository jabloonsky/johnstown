"""Pasek postepu na samej bibliotece standardowej.

Na terminalu odswieza sie w miejscu; przy przekierowaniu do pliku degraduje do
rzadkich linii, zeby log z indeksowania 50 tys. plikow nie mial 50 tys. wierszy.
"""
from __future__ import annotations

import sys
import time
from typing import TextIO

__all__ = ["Progress"]


def _duration(seconds: float) -> str:
    seconds = int(max(seconds, 0))
    if seconds < 60:
        return f"{seconds}s"
    minutes, sec = divmod(seconds, 60)
    if minutes < 60:
        return f"{minutes}m{sec:02d}s"
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h{minutes:02d}m"


class Progress:
    """Prosty licznik z ETA. Bezpieczny do uzycia jako kontekst."""

    def __init__(
        self,
        total: int,
        label: str = "",
        *,
        stream: TextIO | None = None,
        enabled: bool = True,
        width: int = 24,
    ):
        self.total = max(total, 0)
        self.label = label
        self.stream = stream if stream is not None else sys.stderr
        self.width = width
        self.count = 0
        self.note = ""
        self._start = time.monotonic()
        self._last_render = 0.0
        self._last_line = 0
        self._tty = bool(enabled and getattr(self.stream, "isatty", lambda: False)())
        self._enabled = enabled

    def __enter__(self) -> "Progress":
        return self

    def __exit__(self, *exc) -> None:
        self.finish()

    def advance(self, step: int = 1, note: str = "") -> None:
        self.count += step
        if note:
            self.note = note
        self._maybe_render()

    def set_note(self, note: str) -> None:
        self.note = note

    def _maybe_render(self) -> None:
        if not self._enabled:
            return
        now = time.monotonic()
        interval = 0.2 if self._tty else 10.0
        if now - self._last_render < interval and self.count < self.total:
            return
        self._last_render = now
        self._render()

    def _bar(self) -> str:
        if not self.total:
            return ""
        filled = int(self.width * min(self.count / self.total, 1.0))
        return "[" + "#" * filled + "-" * (self.width - filled) + "]"

    def _eta(self) -> str:
        elapsed = time.monotonic() - self._start
        if self.count <= 0 or not self.total:
            return ""
        rate = self.count / elapsed if elapsed > 0 else 0.0
        if rate <= 0:
            return ""
        return f"  ETA {_duration((self.total - self.count) / rate)}"

    def _render(self) -> None:
        parts = [self.label, self._bar(), f"{self.count}/{self.total}", self._eta()]
        if self.note:
            parts.append(f"  {self.note}")
        line = " ".join(p for p in parts if p)
        if self._tty:
            padding = max(self._last_line - len(line), 0)
            self.stream.write("\r" + line + " " * padding)
            self._last_line = len(line)
        else:
            self.stream.write(line + "\n")
        self.stream.flush()

    def finish(self, note: str = "") -> None:
        if not self._enabled:
            return
        if note:
            self.note = note
        self._render()
        if self._tty:
            self.stream.write("\n")
        self.stream.flush()
        self._enabled = False
