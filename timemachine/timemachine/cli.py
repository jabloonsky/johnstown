"""Interfejs wiersza polecen. Jedyne miejsce w pakiecie, ktore pisze na ekran."""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from . import __version__, analyze, calibrate, caps, config, db as db_module, safety, scanner

EXIT_OK = 0
EXIT_ERROR = 2
EXIT_INTERRUPTED = 130

_NOT_YET = {
    "pick": "Etap 2 (scoring i selekcja)",
    "review": "Etap 3 (lokalny przeglad)",
    "build": "Etap 4 (generator HTML)",
}


# ── pomocnicze ───────────────────────────────────────────────────────────────


def _open_library() -> tuple[config.Config, db_module.Database]:
    cfg = config.load()
    return cfg, db_module.connect()


def _resolve_roots(cfg: config.Config, given: list[str]) -> list[Path]:
    if given:
        return [safety.resolve(p) for p in given]
    roots = cfg.root_paths()
    if not roots:
        raise config.ConfigError(
            "Nie podano katalogu i [archive].roots jest puste. "
            "Uzyj `timemachine index /sciezka/do/archiwum` albo uzupelnij config."
        )
    return roots


def _print_stats(title: str, body: str) -> None:
    print(f"\n{title}\n{'-' * len(title)}\n{body}\n")


# ── komendy ──────────────────────────────────────────────────────────────────


def cmd_init(args: argparse.Namespace) -> int:
    home = config.home_dir()
    target = config.config_path()
    home.mkdir(parents=True, exist_ok=True)
    if target.exists() and not args.force:
        print(f"Konfiguracja juz istnieje: {target}")
        print("Uzyj --force, zeby nadpisac ja szablonem.")
        return EXIT_OK
    with open(target, "w", encoding="utf-8") as fh:
        fh.write(config.default_toml())
    database = db_module.connect()
    database.close()
    print(f"Utworzono {target}")
    print(f"Utworzono {config.db_path()}")
    print("\nNastepny krok: wpisz date urodzenia w [child].birth_date, potem:")
    print("  timemachine doctor")
    print("  timemachine index /sciezka/do/archiwum")
    return EXIT_OK


def cmd_doctor(args: argparse.Namespace) -> int:
    print("Zaleznosci:\n")
    print(caps.format_report())
    print("\nSciezki:")
    print(f"  katalog domowy : {config.home_dir()}")
    print(f"  konfiguracja   : {config.config_path()}")
    print(f"  baza           : {config.db_path()}")
    try:
        cfg = config.load()
    except config.ConfigError as exc:
        print(f"\nKonfiguracja: {exc}")
        return EXIT_OK
    print("\nKonfiguracja: OK")
    try:
        birth = cfg.birth_date
        print(f"  data urodzenia : {birth.isoformat()}")
    except config.ConfigError as exc:
        print(f"  UWAGA: {exc}")
    try:
        out = safety.assert_outside(cfg.output_dir(), cfg.root_paths())
        print(f"  katalog wyjsciowy: {out} (poza archiwum)")
    except safety.UnsafePathError as exc:
        print(f"  BLAD: {exc}")
        return EXIT_ERROR
    if config.db_path().exists():
        with db_module.connect() as database:
            counts = database.counts()
        print("\nBiblioteka: " + "  ".join(f"{k}={v}" for k, v in counts.items()))
    return EXIT_OK


def cmd_index(args: argparse.Namespace) -> int:
    cfg, database = _open_library()
    with database:
        roots = _resolve_roots(cfg, args.paths)
        safety.assert_outside(cfg.output_dir(), roots)
        stats = scanner.index_paths(
            database, cfg, roots,
            full_hash=args.full_hash,
            show_progress=not args.no_progress,
        )
        _print_stats("Skanowanie", stats.summary())
        if stats.interrupted:
            print("Przerwano. Uruchom te sama komende ponownie -- praca zostanie wznowiona.")
            return EXIT_INTERRUPTED

        calibrate.ensure_periods(database, cfg)

        if args.no_analyze:
            pending = database.scalar("SELECT count(*) FROM frames WHERE analyzed_at IS NULL")
            print(f"Pominieto analize twarzy. Klatek czekajacych: {pending}")
            print("Uruchom `timemachine analyze`, gdy bedziesz gotowy.")
            return EXIT_OK

        if not caps.have("insightface"):
            print("Pomijam analize twarzy -- brak insightface.")
            print('  pip install "timemachine[faces]"   a potem: timemachine analyze')
            return EXIT_OK

        result = analyze.analyze_pending(
            database, cfg, limit=args.limit, show_progress=not args.no_progress
        )
        _print_stats("Analiza twarzy", result.summary())
        if result.interrupted:
            print("Przerwano. `timemachine analyze` podejmie prace od tego miejsca.")
            return EXIT_INTERRUPTED
    return EXIT_OK


def cmd_analyze(args: argparse.Namespace) -> int:
    cfg, database = _open_library()
    with database:
        calibrate.ensure_periods(database, cfg)
        result = analyze.analyze_pending(
            database, cfg,
            limit=args.limit,
            reanalyze=args.reanalyze,
            show_progress=not args.no_progress,
        )
        _print_stats("Analiza twarzy", result.summary())
        return EXIT_INTERRUPTED if result.interrupted else EXIT_OK


def cmd_calibrate(args: argparse.Namespace) -> int:
    cfg, database = _open_library()
    with database:
        action = args.action or "status"

        if action == "add":
            paths = [safety.resolve(p) for p in _expand(args.paths)]
            if not paths:
                print("Podaj zdjecia referencyjne: timemachine calibrate add ~/ref/*.jpg")
                return EXIT_ERROR
            when = date.fromisoformat(args.date) if args.date else None
            result = calibrate.add_references(
                database, cfg, paths,
                face_index=args.face, largest=args.largest, when=when,
            )
            for message in result.messages:
                print(message)
            print(
                f"\nDodano: {result.added}  pominietych: {result.skipped}  "
                f"bledow: {result.errors}  wylaczonych przy przycinaniu: {result.deactivated}"
            )
            _print_pool(database, cfg)
            return EXIT_OK if result.errors == 0 else EXIT_ERROR

        if action == "list":
            rows = calibrate.list_references(database, include_inactive=args.all)
            if not rows:
                print("Pula referencyjna jest pusta.")
                return EXIT_OK
            for row in rows:
                period = row["period_label"] or "bez okresu"
                state = "" if row["active"] else "  (wylaczona)"
                print(
                    f"  [{row['id']:>4}] {period:<24} {row['origin']:<17} "
                    f"{row['capture_ts'] or '?':<12} {row['source_path']}{state}"
                )
            return EXIT_OK

        if action == "remove":
            if args.ref_id is None:
                print("Podaj numer referencji: timemachine calibrate remove --id 12")
                return EXIT_ERROR
            if calibrate.remove_reference(database, args.ref_id):
                print(f"Wylaczono referencje {args.ref_id}.")
                return EXIT_OK
            print(f"Nie ma referencji o numerze {args.ref_id}.")
            return EXIT_ERROR

        if action == "prune":
            removed = calibrate.prune_pool(database, cfg, cfg.faces.model)
            print(f"Wylaczono {removed} nadmiarowych referencji.")
            _print_pool(database, cfg)
            return EXIT_OK

        _print_pool(database, cfg)
        return EXIT_OK


def _expand(patterns: list[str]) -> list[str]:
    """Rozwija wzorce, gdy powloka ich nie rozwinela (np. cudzyslowy)."""
    expanded: list[str] = []
    for pattern in patterns:
        if any(ch in pattern for ch in "*?["):
            matches = sorted(str(p) for p in Path().glob(pattern))
            expanded.extend(matches or [pattern])
        else:
            path = Path(pattern).expanduser()
            if path.is_dir():
                expanded.extend(
                    sorted(str(p) for p in path.iterdir() if p.is_file() and not p.name.startswith("."))
                )
            else:
                expanded.append(pattern)
    return expanded


def _print_pool(database: db_module.Database, cfg: config.Config) -> None:
    rows = calibrate.pool_status(database, cfg)
    print("\nPula referencyjna wg okresow zycia:")
    print("  (wielookresowy wzorzec -- twarz dziecka zmienia sie z wiekiem)\n")
    total = 0
    for row in rows:
        total += row["count"]
        marker = "!" if row["thin"] and row["idx"] is not None else " "
        origins = ("  <- " + ", ".join(row["origins"])) if row["origins"] else ""
        print(f"  {marker} {row['label']:<32} {row['count']:>3} ref.{origins}")
    print(f"\n  razem: {total} referencji")
    thin = [r for r in rows if r["thin"] and r["idx"] is not None and r["count"] == 0]
    if thin:
        print(
            f"  ! {len(thin)} okresow bez referencji -- zdjecia z tych miesiecy beda "
            "dopasowywane ostrozniej (podniesiony prog) i oznaczane jako niepewne."
        )


def cmd_note(args: argparse.Namespace) -> int:
    cfg, database = _open_library()
    with database:
        if args.text is None:
            row = database.one("SELECT text, updated_at FROM notes WHERE month = ?", (args.month,))
            if row:
                print(f"{args.month} ({row['updated_at']}):\n{row['text']}")
            else:
                print(f"Brak notatki dla {args.month}.")
            return EXIT_OK
        with database.transaction():
            database.execute(
                "INSERT INTO notes (month, text, updated_at) VALUES (?, ?, ?) "
                "ON CONFLICT(month) DO UPDATE SET text = excluded.text, "
                "updated_at = excluded.updated_at",
                (args.month, args.text, db_module.utc_now()),
            )
        print(f"Zapisano notatke do {args.month}.")
        return EXIT_OK


def cmd_log(args: argparse.Namespace) -> int:
    _, database = _open_library()
    with database:
        clauses, params = [], []
        if args.skipped:
            clauses.append("event IN ('skipped_no_preview', 'no_exif_date')")
        if args.errors:
            clauses.append("level = 'error'")
        where = f"WHERE {' OR '.join(clauses)}" if clauses else ""
        rows = database.query(
            f"SELECT ts, level, event, path, detail FROM log {where} "
            f"ORDER BY id DESC LIMIT {int(args.limit)}"
        )
        if not rows:
            print("Log jest pusty.")
            return EXIT_OK
        for row in reversed(rows):
            print(f"  {row['ts']}  {row['level']:<5} {row['event']:<20} {row['path'] or ''}")
            if row["detail"]:
                print(f"      {row['detail']}")
        return EXIT_OK


def cmd_status(args: argparse.Namespace) -> int:
    cfg, database = _open_library()
    with database:
        counts = database.counts()
        print("Biblioteka:")
        for key, value in counts.items():
            print(f"  {key:<12} {value}")
        pending = database.scalar("SELECT count(*) FROM frames WHERE analyzed_at IS NULL") or 0
        skipped = database.scalar("SELECT count(*) FROM files WHERE status = 'skipped'") or 0
        subjects = database.scalar("SELECT count(*) FROM faces WHERE is_subject = 1") or 0
        print(f"\n  czekajacych na analize: {pending}")
        print(f"  pominietych plikow    : {skipped}")
        print(f"  twarzy uznanych za corke: {subjects}")
        months = database.query(
            "SELECT month, count(*) AS n FROM frames WHERE month IS NOT NULL "
            "GROUP BY month ORDER BY month"
        )
        if months:
            print("\n  klatki wg miesiecy:")
            for row in months[-24:]:
                print(f"    {row['month']}  {row['n']}")
        return EXIT_OK


def cmd_not_yet(args: argparse.Namespace) -> int:
    stage = _NOT_YET.get(args.command, "kolejny etap")
    print(f"`timemachine {args.command}` bedzie dostepne po realizacji: {stage}.")
    print("Etap 1 obejmuje: index, analyze, calibrate, note, log, status, doctor.")
    return EXIT_ERROR


# ── parser ───────────────────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="timemachine",
        description="Lokalna os czasu zdjec dziecka. Wszystko dziala offline; "
                    "archiwum jest czytane wylacznie do odczytu.",
    )
    parser.add_argument("--version", action="version", version=f"timemachine {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="tworzy config i pusta baze")
    init.add_argument("--force", action="store_true", help="nadpisz istniejacy config")
    init.set_defaults(handler=cmd_init)

    doctor = subparsers.add_parser("doctor", help="sprawdza zaleznosci i konfiguracje")
    doctor.set_defaults(handler=cmd_doctor)

    index = subparsers.add_parser("index", help="skanuje archiwum (przyrostowo)")
    index.add_argument("paths", nargs="*", help="katalogi do przeskanowania")
    index.add_argument("--full-hash", action="store_true",
                       help="liczy skrot z calego pliku zamiast z poczatku i konca")
    index.add_argument("--no-analyze", action="store_true",
                       help="tylko skan metadanych, bez szukania twarzy")
    index.add_argument("--limit", type=int, default=None, help="analizuj najwyzej N klatek")
    index.add_argument("--no-progress", action="store_true")
    index.set_defaults(handler=cmd_index)

    analyze_cmd = subparsers.add_parser("analyze", help="szuka twarzy w zaindeksowanych klatkach")
    analyze_cmd.add_argument("--limit", type=int, default=None)
    analyze_cmd.add_argument("--reanalyze", action="store_true",
                             help="policz od nowa takze juz przeanalizowane klatki")
    analyze_cmd.add_argument("--no-progress", action="store_true")
    analyze_cmd.set_defaults(handler=cmd_analyze)

    cal = subparsers.add_parser("calibrate", help="wielookresowa pula referencyjna twarzy")
    cal.add_argument("action", nargs="?", choices=["add", "list", "remove", "prune", "status"])
    cal.add_argument("paths", nargs="*", help="zdjecia referencyjne (dla `add`)")
    cal.add_argument("--face", type=int, default=None,
                     help="numer twarzy na zdjeciu, gdy jest ich wiecej niz jedna")
    cal.add_argument("--largest", action="store_true", help="wybierz najwieksza twarz")
    cal.add_argument("--date", default=None, help="data zdjecia YYYY-MM-DD, gdy brak EXIF")
    cal.add_argument("--id", dest="ref_id", type=int, default=None, help="numer referencji")
    cal.add_argument("--all", action="store_true", help="pokaz takze wylaczone referencje")
    cal.set_defaults(handler=cmd_calibrate)

    note = subparsers.add_parser("note", help="notatka do miesiaca")
    note.add_argument("month", help="miesiac w formacie YYYY-MM")
    note.add_argument("text", nargs="?", default=None, help="tresc; pusto = wyswietl")
    note.set_defaults(handler=cmd_note)

    log_cmd = subparsers.add_parser("log", help="dziennik zdarzen (pominiete pliki, bledy)")
    log_cmd.add_argument("--skipped", action="store_true")
    log_cmd.add_argument("--errors", action="store_true")
    log_cmd.add_argument("--limit", type=int, default=50)
    log_cmd.set_defaults(handler=cmd_log)

    status = subparsers.add_parser("status", help="podsumowanie biblioteki")
    status.set_defaults(handler=cmd_status)

    for name, stage in _NOT_YET.items():
        stub = subparsers.add_parser(name, help=f"[{stage}]")
        stub.add_argument("month", nargs="?", default=None)
        stub.set_defaults(handler=cmd_not_yet)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.handler(args)
    except KeyboardInterrupt:
        print("\nPrzerwano.", file=sys.stderr)
        return EXIT_INTERRUPTED
    except (config.ConfigError, caps.MissingDependency, safety.UnsafePathError) as exc:
        print(f"\n{exc}", file=sys.stderr)
        return EXIT_ERROR
    except (FileNotFoundError, NotADirectoryError) as exc:
        print(f"\n{exc}", file=sys.stderr)
        return EXIT_ERROR


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
