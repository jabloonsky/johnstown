# Biblioteka Kamila — interaktywna tablica

Interaktywna biblioteka zbudowana z `bibliotekakamila.md`. Kolumny odpowiadają
tagom statusu z pliku źródłowego (`READ` / `READING` / `QUEUE` / `REC`), a model
danych to schemat JSON z nagłówka tego pliku:

```json
{
  "title": "string",
  "author": "string",
  "category": "string",
  "series": "string|null",
  "seriesIndex": "number|null",
  "status": "read|reading|queue|rec",
  "progress": "number|null",
  "star": "boolean",
  "blurb": "string"
}
```

(aplikacja dodaje pomocniczo `id` oraz `topPick` — ranking z listy „Top na już").

## Pliki

- `bibliotekakamila.md` — źródło (eksport rozmów / biblioteki Kindle)
- `parse_library.py` — parser md → `books.json` (628 pozycji)
- `books.json` — dane w modelu ze schematu
- `template.html` — aplikacja (HTML/CSS/JS, bez zależności)
- `build.py` — wstrzykuje `books.json` do szablonu → `index.html`
- `index.html` — gotowa, samodzielna aplikacja (otwórz w przeglądarce)

## Odświeżenie po zmianie źródła

```sh
python3 parse_library.py && python3 build.py
```

## Funkcje

- kolumny wg statusu; w READ/QUEUE grupowanie po seriach, w READING sortowanie
  po % postępu z paskami, w REC zwijane grupy kategorii
- filtry: statusy (chips), kategoria, ⭐ najlepsze dopasowania, wyszukiwarka
  odporna na znaki diakrytyczne (nesbo → Nesbø)
- półka „Top na już" — 10 najmocniejszych typów, klik przenosi do karty
- motyw jasny/ciemny wg ustawień systemu, stan filtrów zapamiętywany lokalnie
