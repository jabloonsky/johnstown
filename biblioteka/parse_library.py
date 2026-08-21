"""Parser: bibliotekakamila.md -> books.json

Model danych (ze schematu w nagłówku pliku .md):
  title, author, category, series, seriesIndex, status, progress, star, blurb
Dodatkowe pola aplikacji: id, topPick (ranking z listy "Top na już").
"""
import json
import re
import sys
from pathlib import Path

MD = Path(__file__).parent / "bibliotekakamila.md"
OUT = Path(__file__).parent / "books.json"

# --- mapowanie kategorii ---

# kategoria z nagłówka serii (część I) -> taksonomia z części II/III
SERIES_CAT = {
    "thriller / zabójca": "Thriller — zabójcy / spec-ops / szpiegowskie",
    "SF / space opera": "Science fiction — space opera / epicki",
    "SF / dystopia": "Postapokalipsa / katastrofa / dystopia",
    "thriller / seryjny morderca": "Kryminał — seryjni mordercy / profilerzy",
    "postapo / katastrofa": "Postapokalipsa / katastrofa / dystopia",
}

# skrócone etykiety dla długich nagłówków części II/III
H2_CLEAN = {
    "Japońska proza (osobno — wyraźny nurt)": "Japońska proza",
    "Katastrofy — rekonstrukcje (dziennikarskie / historyczne)": "Katastrofy — rekonstrukcje",
    "Korea Północna / autorytaryzm — od środka": "Korea Północna / autorytaryzm",
    "Polityka / władza / insiderzy": "Polityka / władza / insiderzy",
    "Wywiad / służby / szpiegostwo (non-fiction)": "Wywiad / służby / szpiegostwo",
    "0,01% — bogactwo / dynastie / oligarchowie / Wall Street": "Bogactwo / dynastie / Wall Street",
    "Postapokalipsa / katastrofa / dystopia (fikcja)": "Postapokalipsa / katastrofa / dystopia",
    "Kryminał — noir / hardboiled / klasyka gatunku": "Kryminał — noir / klasyka",
    "Psychologia / rozwój / stoicyzm / terapia schematów": "Psychologia / rozwój / stoicyzm",
    "Biznes / ekonomia / finanse / technologia": "Biznes / finanse / technologia",
    "Nauka / medycyna / mózg / natura": "Nauka / medycyna / natura",
    "Fikcja literacka — klasyka i Nobliści": "Fikcja literacka — klasyka",
    "Realizm magiczny / dziwne / eksperymentalne": "Realizm magiczny / eksperymentalne",
    "Memuary / biografie / autobiografie": "Memuary / biografie",
    "Katastrofy i przetrwanie — z pierwszej ręki": "Katastrofy i przetrwanie — relacje",
}

# ręczne kategorie dla pozycji z części I bez nagłówka kategorii
MANUAL_CAT = {
    "Demony Rosji": "Polityka / władza / insiderzy",
    "The Raqqa Diaries": "Reportaż / podróże / społeczeństwo",
    "Aurora": "Postapokalipsa / katastrofa / dystopia",
    "Hrabia Monte Christo": "Fikcja literacka — klasyka",
    "Into the Raging Sea": "Katastrofy — rekonstrukcje",
    "Wszystko za Everest": "Katastrofy i przetrwanie — relacje",
    "Imperium bólu": "True crime / dziennikarstwo śledcze",
    "Cokolwiek powiesz, nic nie mów (Say Nothing)": "True crime / dziennikarstwo śledcze",
    "Podróż Sir Ernesta (Endurance)": "Katastrofy i przetrwanie — relacje",
    "Pierwszych piętnaście żywotów Harry'ego Augusta": "Science fiction — hard / koncept / czas",
    "Uwolniona (Educated)": "Memuary / biografie",
    "The Great Mortality": "Pandemie i zarazy",
    "The Back Channel": "Polityka / władza / insiderzy",
    "The Aquariums of Pyongyang": "Korea Północna / autorytaryzm",
    "Midnight in Chernobyl": "Katastrofy — rekonstrukcje",
    "Steve Jobs": "Biznes / finanse / technologia",
    "The Black Death": "Pandemie i zarazy",
    "Dark Territory": "Wywiad / służby / szpiegostwo",
    "Dekameron": "Fikcja literacka — klasyka",
    "Miracle in the Andes": "Katastrofy i przetrwanie — relacje",
    "A Journal of the Plague Year": "Pandemie i zarazy",
    "Dżuma": "Fikcja literacka — klasyka",
    "Dziewczyna o siedmiu imionach": "Korea Północna / autorytaryzm",
    "Doomsday Book": "Science fiction — hard / koncept / czas",
    "Dark Psychology": "Psychologia / rozwój / stoicyzm",
    "K2": "Katastrofy i przetrwanie — relacje",
    "102 Minutes": "Katastrofy — rekonstrukcje",
    "Daemon": "Thriller — zabójcy / spec-ops / szpiegowskie",
    "A Spy Among Friends": "Wywiad / służby / szpiegostwo",
    "One Rough Man": "Thriller — zabójcy / spec-ops / szpiegowskie",
    "Blindsight": "Science fiction — hard / koncept / czas",
    "Elon Musk": "Biznes / finanse / technologia",
    "Nielegalni": "Thriller — zabójcy / spec-ops / szpiegowskie",
    "Dzieci Czasu (Children of Time)": "Science fiction — space opera / epicki",
    "Rozmowy z katem": "Polski reportaż",
    "Hell's Angels": "Reportaż / podróże / społeczeństwo",
    "Dzienniki Kołymskie": "Polski reportaż",
    "Invisible Child": "Reportaż / podróże / społeczeństwo",
    "Dreamland": "True crime / dziennikarstwo śledcze",
    "Five Days at Memorial": "Katastrofy — rekonstrukcje",
}

TOP_PICKS = [
    "Dotknięcie pustki",
    "Pantera",
    "Rain Fall",
    "Hipnotyzer",
    "Bastion",
    "Sandworm",
    "Modyfikowany węgiel",
    "Kobieta w klatce",
    "Poświęcenie podejrzanego X",
    "Jak nakarmić dyktatora",
]

ITEM_RE = re.compile(r"^- `(READ|READING|QUEUE|REC)(?: (\d+)%)?`\s*(.*)$")
BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
H3_RE = re.compile(r"^### (.+?) — (.+?) \*\((.+?)\)\*")


def clean(text: str) -> str:
    text = text.replace("**", "").replace("*", "").replace("`", "")
    text = re.sub(r"\s+", " ", text).strip()
    return text.strip("—— ").strip()


def looks_like_author(seg: str) -> bool:
    seg = seg.strip()
    if not seg or seg.startswith("patrz") or seg.startswith("("):
        return False
    if seg.startswith("bracia "):  # bracia Strugaccy
        return True
    first = seg.lstrip("*(„\"'")
    if not first or not first[0].isupper():
        return False
    # autor to krótki segment; kropka na końcu dopuszczalna przy nazwiskach
    if len(seg) > 60:
        return False
    return not seg.endswith(".") or len(seg.split()) <= 7


def parse():
    lines = MD.read_text(encoding="utf-8").splitlines()
    books = []
    part = None
    h2 = None
    series = None
    series_author = None
    series_cat = None

    for raw in lines:
        line = raw.rstrip()
        if line.startswith("# CZĘŚĆ"):
            pm = re.search(r"CZĘŚĆ (I{1,3})\b", line)
            part = pm.group(1) if pm else part
            h2 = None
            series = series_author = series_cat = None
            continue
        if line.startswith("## "):
            h2 = clean(re.sub(r"\*\(.*?\)\*", "", line[3:]))
            series = series_author = series_cat = None
            continue
        if line.startswith("### "):
            m = H3_RE.match(line)
            if m:
                series = clean(m.group(1))
                series_author = clean(m.group(2))
                series_cat = SERIES_CAT.get(m.group(3).strip(), m.group(3).strip())
            continue

        m = ITEM_RE.match(line)
        if not m:
            continue
        status_tag, pct, rest = m.groups()

        # dedup: "patrz biblioteka / patrz wyżej" — pozycja już istnieje gdzie indziej
        if "patrz " in rest:
            # specjalny przypadek: linia łączy odsyłacz z nową pozycją (The Forever War)
            if "The Forever War" in rest:
                rest = rest.split(";", 1)[1].strip()
            else:
                continue

        star = "⭐" in rest
        rest = rest.replace("⭐", "")

        bolds = BOLD_RE.findall(rest)
        if not bolds:
            continue
        title = clean(" / ".join(bolds) if len(bolds) > 1 else bolds[0])

        after = rest
        for b in BOLD_RE.finditer(rest):
            pass
        # tekst po ostatnim pogrubieniu
        after = BOLD_RE.split(rest)[-1]
        segs = [s.strip() for s in after.split("—") if s.strip()]

        author = ""
        blurb_segs = segs
        author_note = ""
        if segs and looks_like_author(clean(segs[0])):
            author = clean(segs[0])
            blurb_segs = segs[1:]
            if author.endswith(".") and not author.endswith("Jr."):
                author = author[:-1]
            nm = re.match(r"^(.*?)\s*\(([^)]+)\)$", author)
            if nm:
                author, author_note = nm.group(1), nm.group(2)
        blurb = clean(" — ".join(blurb_segs))
        if author_note:
            blurb = f"{blurb} ({author_note})" if blurb else f"({author_note})"
        # znaczniki procentów siedzą już w polu progress
        blurb = re.sub(r",?\s*\d+%", "", blurb)
        blurb = re.sub(r"\s*\(\s*\)", "", blurb).strip(" ,")

        progress = int(pct) if pct else None
        if status_tag == "READING" and progress is None:
            pm = re.search(r"(\d+)%", rest)
            progress = int(pm.group(1)) if pm else None

        series_idx = None
        im = re.search(r"#(\d+)", rest)
        if im:
            series_idx = int(im.group(1))

        if part == "I":
            if series:
                cat = series_cat
                book_series = series
                book_author = author or series_author
            else:
                cat = MANUAL_CAT.get(title, "Inne")
                book_series = None
                book_author = author
        else:
            cat = H2_CLEAN.get(h2, h2)
            book_series = None
            book_author = author

        status = status_tag.lower()
        books.append({
            "id": len(books) + 1,
            "title": title,
            "author": book_author,
            "category": cat,
            "series": book_series,
            "seriesIndex": series_idx,
            "status": status,
            "progress": progress,
            "star": star,
            "blurb": blurb,
            "topPick": None,
        })

    for rank, key in enumerate(TOP_PICKS, 1):
        for b in books:
            if key.lower() in b["title"].lower() and b["topPick"] is None:
                b["topPick"] = rank
                break

    return books


if __name__ == "__main__":
    books = parse()
    OUT.write_text(json.dumps(books, ensure_ascii=False, indent=1), encoding="utf-8")
    from collections import Counter
    st = Counter(b["status"] for b in books)
    cats = Counter(b["category"] for b in books)
    print(f"total: {len(books)}  statusy: {dict(st)}")
    print(f"kategorie ({len(cats)}):")
    for c, n in cats.most_common():
        print(f"  {n:3d}  {c}")
    missing_author = [b["title"] for b in books if not b["author"]]
    print(f"bez autora ({len(missing_author)}): {missing_author}")
    noblurb = [b["title"] for b in books if not b["blurb"]]
    print(f"bez opisu ({len(noblurb)}): {noblurb[:20]}")
    tops = [(b['topPick'], b['title']) for b in books if b['topPick']]
    print("top picks:", sorted(tops))
    sys.exit(0)
