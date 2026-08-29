# timemachine

Lokalne narzedzie CLI, ktore co miesiac wybiera najlepsze zdjecia dziecka z Twojego
archiwum fotograficznego i buduje rosnaca os czasu jako statyczny HTML.

**Wszystko dziala w 100% lokalnie.** Zadnej chmury, zadnego API, zadnej telemetrii.
Jedyne polaczenie z siecia w calym cyklu zycia narzedzia to jednorazowe pobranie
modelu rozpoznawania twarzy przy pierwszym uruchomieniu; potem mozesz odciac sie
od internetu na stale.

**Archiwum jest tylko do odczytu.** Narzedzie nigdy nie zapisuje, nie przenosi,
nie zmienia nazw ani nie kasuje niczego w Twoich katalogach ze zdjeciami. Ta
gwarancja jest pilnowana testem, ktory analizuje kod zrodlowy (`tests/test_readonly.py`).

## Stan prac

| Etap | Zakres | Stan |
|---|---|---|
| 1 | skaner + baza SQLite + kalibracja twarzy | **gotowe** |
| 2 | scoring + deduplikacja serii + selekcja miesiaca | w planie |
| 3 | `review` -- lokalny serwer do zatwierdzania | w planie |
| 4 | generator `timeline.html` | w planie |

Komendy `pick`, `review` i `build` istnieja w CLI, ale na razie odpowiadaja
komunikatem, ze naleza do kolejnego etapu.

## Instalacja (macOS, Apple Silicon)

```bash
cd timemachine
python3 -m venv .venv && source .venv/bin/activate

pip install -e .                    # sam rdzen: skan, EXIF, baza (bez zaleznosci)
pip install -e ".[faces]"           # + rozpoznawanie twarzy (insightface, onnxruntime)
pip install -e ".[raw]"             # + podglady z plikow RAW (rawpy)
brew install exiftool               # zapasowe czytanie CR3/HEIC
```

Bez `[faces]` dziala wszystko poza szukaniem twarzy -- skan, EXIF, parowanie
RAW+JPG, baza. `timemachine doctor` pokazuje, co jest zainstalowane i co przez
brak czego nie zadziala.

## Pierwsze uruchomienie

```bash
timemachine init                    # tworzy ~/.timemachine/config.toml
$EDITOR ~/.timemachine/config.toml  # WAZNE: wpisz [child].birth_date
timemachine doctor                  # sprawdzenie zaleznosci i sciezek

timemachine index /Volumes/Foto/2025        # skan archiwum
timemachine calibrate add ~/ref/*.jpg       # 10-20 zdjec referencyjnych
timemachine calibrate --status              # rozklad referencji po okresach zycia
timemachine status                          # co jest w bibliotece
```

Drugie uruchomienie `index` na tym samym katalogu przechodzi w kilka sekund --
pliki o niezmienionym rozmiarze i czasie modyfikacji nie sa nawet otwierane.

## Wielookresowy wzorzec twarzy

To najwazniejsza decyzja projektowa w calym narzedziu. Twarz dziecka zmienia sie
z wiekiem tak bardzo, ze pojedynczy wzorzec przestaje dzialac po kilku miesiacach.
Dlatego:

* pula referencyjna jest **podzielona na okresy zycia** (kwartalnie do 3. roku,
  potem co pol roku, potem rocznie -- generowane z daty urodzenia);
* kazdy embedding referencyjny **zyje w niej osobno**; nie ma zadnego usredniania
  do jednego prototypu;
* dopasowanie zdjecia z chwili `t` siega po referencje z okresu `p(t)` i okresow
  sasiednich, z lagodna premia za bliskosc w czasie -- bliskosc premiuje, ale nigdy
  nie dyskwalifikuje;
* gdy w okresie brakuje referencji, **prog jest podnoszony**, a klatka oznaczana
  jako niepewna: przy niepewnosci wolimy przeoczyc wlasne zdjecie niz wpuscic obce
  dziecko;
* pula rosnie **wylacznie** z kalibracji i z zatwierdzen w `review`. Automatyczne
  dopasowanie nigdy nie dokłada referencji -- inaczej jeden falszywy pozytyw
  przyciagnalby kolejne i po kilku miesiacach wzorzec opisywalby cudze dziecko.

`timemachine calibrate --status` pokazuje dziury w pokryciu -- okresy oznaczone
`!` to te, dla ktorych warto wskazac kilka zdjec referencyjnych.

## Komendy

| Komenda | Opis |
|---|---|
| `timemachine init` | tworzy konfiguracje i pusta baze |
| `timemachine doctor` | zaleznosci, sciezki, stan konfiguracji |
| `timemachine index <sciezka>` | przyrostowy skan archiwum |
| `timemachine analyze` | szukanie twarzy w zaindeksowanych klatkach |
| `timemachine calibrate add <pliki>` | dodanie zdjec referencyjnych |
| `timemachine calibrate --status` | rozklad referencji po okresach zycia |
| `timemachine calibrate list \| remove --id N \| prune` | zarzadzanie pula |
| `timemachine note 2026-08 "tekst"` | notatka do miesiaca |
| `timemachine status` | podsumowanie biblioteki |
| `timemachine log --skipped` | pominiete pliki i bledy |

Bez instalacji: `python3 -m timemachine <komenda>`.

## Jak to dziala

Indeksowanie jest **dwufazowe**, bo dwie polowy pracy maja zupelnie inny koszt:

1. **Faza A (tania)** -- obchod katalogow, porownanie `(rozmiar, mtime)` z baza,
   dla nowych i zmienionych plikow skrot tresci i EXIF. Plik niezmieniony nie jest
   otwierany w ogole.
2. **Faza B (kosztowna)** -- dekodowanie pikseli, detekcja twarzy, embeddingi i
   metryki jakosci. Kazda klatka jest dekodowana dokladnie raz; ponowne czytanie
   dziesiatek tysiecy RAW-ow z dysku zewnetrznego jest tym, czego unikamy.

**Wznawialnosc**: praca idzie paczkami, kazda w osobnej transakcji, baza w trybie
WAL. Ctrl-C kosztuje najwyzej biezaca paczke -- ta sama komenda uruchomiona
ponownie podejmie prace od tego samego miejsca.

**RAW + JPG** tej samej klatki (ten sam katalog, ta sama nazwa, ten sam czas EXIF)
to jedno zdjecie w bazie. Do analizy uzywany jest JPG. Dla RAW bez pary czytany
jest **podglad wbudowany** w plik (rawpy, a jak sie nie da -- exiftool); pelnego
demozaikowania nie robimy nigdy. Plik bez podgladu jest pomijany i logowany
(`timemachine log --skipped`).

**Przeniesione pliki** sa rozpoznawane po skrocie tresci, wiec reorganizacja
katalogow nie gubi decyzji z review. Pliki, ktore znikly, sa oznaczane jako
`missing`, a nie kasowane z bazy.

## Konfiguracja

`~/.timemachine/config.toml` (sciezke mozna zmienic zmienna `TIMEMACHINE_HOME`).
Najwazniejsze: `[child].birth_date`. Reszta ma sensowne wartosci domyslne --
progi dopasowania, wagi scoringu, limity selekcji, parametry eksportu.

## Testy

```bash
pip install -e ".[dev]"
pytest
```

Caly zestaw testow dziala na **golym Pythonie** -- bez numpy, Pillow i insightface.
Logika, ktora decyduje o wyborze zdjec (dopasowanie tozsamosci, arytmetyka wieku,
w kolejnych etapach scoring i deduplikacja) jest celowo napisana bez ciezkich
zaleznosci, zeby dalo sie ja testowac szybko i wszedzie.
