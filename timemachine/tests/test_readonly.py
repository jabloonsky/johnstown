"""Strazniki gwarancji "archiwum jest tylko do odczytu".

Test analizuje drzewo skladniowe calego pakietu i pilnuje, ze moduly dotykajace
plikow uzytkownika nie zawieraja ANI JEDNEJ operacji zapisu, zmiany nazwy czy
usuwania. To jest gwarancja strukturalna, nie obietnica w dokumentacji: jesli
ktos kiedys doda `os.rename` do skanera, ten test zapali sie na czerwono.
"""
import ast
from pathlib import Path

import pytest

from timemachine import safety

PACKAGE = Path(safety.__file__).parent

# Moduly, ktore czytaja archiwum. Tu nie wolno zapisywac niczego.
ARCHIVE_READERS = {
    "scanner.py", "exif.py", "images.py", "faces.py", "analyze.py",
    "calibrate.py", "exiftool.py", "safety.py", "quality.py", "identity.py",
}

# Moduly, ktorym wolno pisac -- i tylko poza archiwum (config, cache, wyjscie).
# Ta lista ma pozostac krotka; kazde dopisanie to swiadoma decyzja.
ALLOWED_WRITERS = {"cli.py"}

MUTATING_CALLS = {
    ("os", "remove"), ("os", "unlink"), ("os", "rename"), ("os", "replace"),
    ("os", "rmdir"), ("os", "removedirs"), ("os", "truncate"), ("os", "chmod"),
    ("os", "utime"), ("os", "link"), ("os", "symlink"),
    ("shutil", "move"), ("shutil", "copy"), ("shutil", "copy2"),
    ("shutil", "rmtree"), ("shutil", "copytree"), ("shutil", "copyfile"),
}

# Nazwy metod jednoznacznie modyfikujace pliki. Celowo NIE ma tu `replace`:
# str.replace jest wszedzie, a odpowiednik na plikach lapiemy przez os.replace.
MUTATING_METHODS = {
    "write_text", "write_bytes", "unlink", "rmdir", "touch", "rename", "mkdir",
}


def modules() -> list[Path]:
    return sorted(p for p in PACKAGE.glob("*.py") if p.name != "__init__.py")


def _write_mode_opens(tree: ast.AST) -> list[int]:
    """Numery linii z open() w trybie innym niz odczyt binarny."""
    lines = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)):
            continue
        if node.func.id != "open":
            continue
        mode = None
        if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
            mode = node.args[1].value
        for keyword in node.keywords:
            if keyword.arg == "mode" and isinstance(keyword.value, ast.Constant):
                mode = keyword.value.value
        if mode is None:
            mode = "r"
        if any(flag in str(mode) for flag in ("w", "a", "x", "+")):
            lines.append(node.lineno)
    return lines


def _mutating_calls(tree: ast.AST) -> list[tuple[int, str]]:
    found = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
            continue
        attribute = node.func
        owner = attribute.value.id if isinstance(attribute.value, ast.Name) else None
        if owner and (owner, attribute.attr) in MUTATING_CALLS:
            found.append((node.lineno, f"{owner}.{attribute.attr}"))
        elif attribute.attr in MUTATING_METHODS:
            found.append((node.lineno, attribute.attr))
    return found


@pytest.mark.parametrize("module", modules(), ids=lambda p: p.name)
def test_archive_readers_never_write(module):
    if module.name not in ARCHIVE_READERS:
        pytest.skip("modul nie czyta archiwum")
    tree = ast.parse(module.read_text(encoding="utf-8"))

    assert _write_mode_opens(tree) == [], (
        f"{module.name}: open() w trybie zapisu -- archiwum jest tylko do odczytu"
    )
    assert _mutating_calls(tree) == [], (
        f"{module.name}: operacja modyfikujaca pliki -- archiwum jest tylko do odczytu"
    )


@pytest.mark.parametrize("module", modules(), ids=lambda p: p.name)
def test_only_allowed_modules_open_files_for_writing(module):
    tree = ast.parse(module.read_text(encoding="utf-8"))
    lines = _write_mode_opens(tree)
    if module.name in ALLOWED_WRITERS:
        return
    assert lines == [], (
        f"{module.name}: zapis do pliku w linii {lines}. Jesli to celowe, dopisz modul "
        "do ALLOWED_WRITERS i upewnij sie, ze cel lezy poza archiwum."
    )


def test_open_readonly_is_the_only_archive_entry_point():
    """Moduly czytajace archiwum nie wolaja gologo open() -- tylko safety.open_readonly."""
    offenders = []
    for module in modules():
        if module.name == "safety.py" or module.name not in ARCHIVE_READERS:
            continue
        tree = ast.parse(module.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                    and node.func.id == "open":
                offenders.append(f"{module.name}:{node.lineno}")
    assert offenders == [], (
        "Pliki archiwum otwieramy wylacznie przez safety.open_readonly(): " + ", ".join(offenders)
    )


# ── zachowanie safety.py ─────────────────────────────────────────────────────

def test_open_readonly_cannot_write(tmp_path):
    path = tmp_path / "a.bin"
    path.write_bytes(b"dane")
    with safety.open_readonly(path) as fh:
        assert fh.read() == b"dane"
        assert not fh.writable()


def test_read_head_tail_returns_edges_of_large_file(tmp_path):
    path = tmp_path / "duzy.bin"
    path.write_bytes(b"A" * 100 + b"B" * 100 + b"C" * 100)
    head, tail, size = safety.read_head_tail(path, 50)
    assert size == 300
    assert head == b"A" * 50
    assert tail == b"C" * 50


def test_read_head_tail_of_small_file_has_no_tail(tmp_path):
    path = tmp_path / "maly.bin"
    path.write_bytes(b"XYZ")
    head, tail, size = safety.read_head_tail(path, 1024)
    assert (head, tail, size) == (b"XYZ", b"", 3)


def test_output_dir_inside_archive_is_refused(tmp_path):
    archive = tmp_path / "archiwum"
    archive.mkdir()
    with pytest.raises(safety.UnsafePathError):
        safety.assert_outside(archive / "os-czasu", [archive])


def test_archive_inside_output_dir_is_refused(tmp_path):
    output = tmp_path / "wyjscie"
    output.mkdir()
    with pytest.raises(safety.UnsafePathError):
        safety.assert_outside(output, [output / "archiwum"])


def test_separate_directories_are_accepted(tmp_path):
    archive = tmp_path / "archiwum"
    output = tmp_path / "os-czasu"
    assert safety.assert_outside(output, [archive]) == output.absolute()


def test_is_within():
    assert safety.is_within("/a/b/c", "/a/b")
    assert safety.is_within("/a/b", "/a/b")
    assert not safety.is_within("/a/bc", "/a/b")
