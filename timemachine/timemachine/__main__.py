"""Pozwala uruchomic narzedzie bez instalacji: `python -m timemachine ...`."""
from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
