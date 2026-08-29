"""Jedyne wejscie do plikow archiwum -- wylacznie do odczytu.

Kazdy dostep do pliku uzytkownika przechodzi przez ten modul. Dzieki temu
gwarancja "archiwum jest nietykalne" jest sprawdzalna w jednym miejscu, a test
`tests/test_readonly.py` skanuje AST calego pakietu i pilnuje, ze nikt poza tym
plikiem nie otwiera niczego do zapisu ani nie wola przenoszenia/usuwania.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import BinaryIO, Iterable

__all__ = [
    "UnsafePathError",
    "open_readonly",
    "read_head_tail",
    "resolve",
    "is_within",
    "assert_outside",
]


class UnsafePathError(Exception):
    """Podniesiony, gdy operacja groziaby zapisem w obrebie archiwum."""


def resolve(path: str | os.PathLike[str]) -> Path:
    """Znormalizowana, absolutna sciezka (bez podazania za dowiazaniami do konca)."""
    return Path(path).expanduser().absolute()


def open_readonly(path: str | os.PathLike[str]) -> BinaryIO:
    """Otwiera plik archiwum w trybie binarnym do odczytu.

    Celowo nie ma tu zadnego parametru trybu -- to jedyny sposob, w jaki reszta
    pakietu dotyka plikow uzytkownika.
    """
    return open(resolve(path), "rb")


def read_head_tail(path: str | os.PathLike[str], chunk: int) -> tuple[bytes, bytes, int]:
    """Zwraca (poczatek, koniec, rozmiar) -- do szybkiego hashowania duzych plikow.

    Dla plikow mniejszych niz 2*chunk koniec jest pusty, bo poczatek pokrywa calosc.
    """
    with open_readonly(path) as fh:
        fh.seek(0, os.SEEK_END)
        size = fh.tell()
        fh.seek(0)
        head = fh.read(chunk)
        if size > 2 * chunk:
            fh.seek(-chunk, os.SEEK_END)
            tail = fh.read(chunk)
        else:
            tail = b""
    return head, tail, size


def is_within(child: str | os.PathLike[str], parent: str | os.PathLike[str]) -> bool:
    """Czy `child` lezy wewnatrz `parent` (lub nim jest)."""
    c = resolve(child)
    p = resolve(parent)
    return c == p or p in c.parents


def assert_outside(target: str | os.PathLike[str], roots: Iterable[str | os.PathLike[str]]) -> Path:
    """Pilnuje, ze katalog docelowy zapisu nie lezy w zadnym rootcie archiwum.

    Chroni przed najgorszym mozliwym bledem konfiguracji: ustawieniem katalogu
    wyjsciowego wewnatrz archiwum i zasypaniem go wygenerowanymi JPG-ami.
    """
    t = resolve(target)
    for root in roots:
        if is_within(t, root) or is_within(root, t):
            raise UnsafePathError(
                f"Katalog wyjsciowy {t} koliduje z archiwum {resolve(root)}. "
                "Archiwum jest tylko do odczytu -- wskaz katalog poza nim."
            )
    return t
