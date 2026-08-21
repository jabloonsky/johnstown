# Biblioteka Kamila — kompletna baza książek

> Zbiorcza lista **wszystkich** książek z naszych rozmów: Twoja biblioteka Kindle (przeczytane / w trakcie / kolejka) + wszystkie rekomendacje pogrupowane tematycznie. Zdeduplikowana. Każda pozycja ma krótki opis bez spoilerów. Docelowo pod interaktywną bibliotekę (Claude Coding).

## Legenda statusów
- `READ` — przeczytane (Twoja biblioteka)
- `READING` — w trakcie (z % ukończenia)
- `QUEUE` — w bibliotece, nierozpoczęte
- `REC` — rekomendacja (nie masz jeszcze w bibliotece)
- ⭐ — najmocniejsze dopasowanie do Twojego gustu

## Sugerowany schemat danych (dla aplikacji)
```json
{
  "title": "string",
  "author": "string",
  "category": "string",
  "series": "string|null",
  "seriesIndex": "number|null",
  "status": "read|reading|queue|rec",
  "progress": "number|null",   // % dla 'reading'
  "star": "boolean",
  "blurb": "string"
}
```

---

# CZĘŚĆ I — TWOJA BIBLIOTEKA

## Przeczytane — serie

### Gray Man — Mark Greaney *(thriller / zabójca)* — 12/15
- `READ` **The Gray Man** — Mark Greaney — debiut; zdradzony przez CIA Court Gentry ucieka przez Europę.
- `READ` **Dead Eye** — Mark Greaney — Gentry ścigany przez dawnego lustrzanego zabójcę.
- `READ` **Back Blast** — Mark Greaney — Gentry wraca do Waszyngtonu, by dowiedzieć się, kto go spalił.
- `READ` **Gunmetal Gray** — Mark Greaney — pościg za chińskim hakerem w Hongkongu.
- `READ` **Agent in Place** — Mark Greaney — misja w Syrii i Paryżu.
- `READ` **Mission Critical** — Mark Greaney — łańcuch zdrady w obrębie CIA.
- `READ` **One Minute Out** — Mark Greaney — Gentry rozbija siatkę handlu ludźmi.
- `READ` **Relentless** — Mark Greaney — globalny pościg za znikającymi agentami.
- `READ` **Sierra Six** — Mark Greaney — wątek z przeszłości Gentry'ego w oddziale Sierra.
- `READ` **Burner** — Mark Greaney — rosyjskie brudne pieniądze i uciekinier.
- `READ` **The Chaos Agent** — Mark Greaney — AI i wojna technologiczna.
- `READ` **Midnight Black** — Mark Greaney — Gentry ratuje ukochaną z rosyjskiego łagru.
- `QUEUE` **On Target** — Mark Greaney *(luka #2 w serii)* — Gentry zmuszony do zabójstwa prezydenta Sudanu.
- `QUEUE` **Ballistic** — Mark Greaney *(luka #3)* — Gentry kontra kartel w Meksyku.
- `QUEUE` **The Hard Line** — Mark Greaney *(najnowszy, 2026)* — kolejna misja Court Gentry'ego.

### Victor the Assassin — Tom Wood *(thriller / zabójca)* — 4/12
- `READ` **The Hunter (The Killer)** — Tom Wood — Victor wpada w zasadzkę po rutynowym zleceniu w Paryżu.
- `READ` **The Enemy** — Tom Wood — Victor jako kontraktor CIA śledzi zwiadowcę bossa.
- `READ` **The Game** — Tom Wood — trzy cele w dwa dni, spisek się zaciska.
- `READ` **Better Off Dead** — Tom Wood — Victor spłaca dług, chroniąc kogoś, komu zawdzięcza życie.
- `READ` **Bad Luck in Berlin** — Tom Wood *(nowela)* — krótkie zlecenie w Berlinie.
- `READING` **Gone by Dawn** — Tom Wood *(nowela, 74%)* — Victor w pułapce jednej nocy.
- `QUEUE` **The Darkest Day** ⭐ — Tom Wood *(następny w serii, #5)* — nieudany zamach w Malmö, Victor ranny i ścigany.
- `QUEUE` **A Time to Die** — Tom Wood — kolejne zlecenie i kolejna zdrada.
- `QUEUE` **The Final Hour** — Tom Wood.
- `QUEUE` **Kill For Me** — Tom Wood.
- `QUEUE` **A Quiet Man** — Tom Wood.
- `QUEUE` **Traitor** — Tom Wood.
- `QUEUE` **Firefight** — Tom Wood.
- `QUEUE` **Unlucky for Some** — Tom Wood *(najnowszy, 2025)*.

### Red Rising — Pierce Brown *(SF / space opera)* — 4/6
- `READ` **Red Rising** — Pierce Brown — górnik z Marsa infiltruje kastę władców.
- `READ` **Golden Son** — Pierce Brown — wojna domowa w społeczeństwie Kolorów.
- `READING` **Morning Star** — Pierce Brown *(1%)* — finał pierwszej trylogii.
- `READING` **Iron Gold** — Pierce Brown *(1%)* — dekadę później, cena rewolucji.
- `READ` **Dark Age** — Pierce Brown — najbrutalniejszy tom sagi.
- `READ` **Light Bringer** — Pierce Brown — powrót do formy, przygotowanie finału.
- *(Red God — tom 7, zapowiedziany)*

### Silos (Wool) — Hugh Howey *(SF / dystopia)* — 3/3 ✓ KOMPLET
- `READ` **Wool / Kokon** — Hugh Howey — ludzkość w podziemnym silosie, zakaz mówienia o świecie zewnętrznym.
- `READ` **Shift / Zmiana** — Hugh Howey — jak powstały silosy.
- `READ` **Dust / Pył** — Hugh Howey — finał trylogii.

### Orphan X — Gregg Hurwitz *(thriller / zabójca)* — 1/10
- `READ` **Orphan X (Człowiek znikąd)** — Gregg Hurwitz — wyszkolony zabójca pomaga bezbronnym jako „Nowhere Man".
- `QUEUE` **The Nowhere Man** — Gregg Hurwitz — Evan Smoak sam staje się celem.
- *(pozostałe: Hellbent, Out of the Dark, Into the Fire, Prodigal Son, Dark Horse, The Last Orphan, Lone Wolf, Nemesis)*

### 4MK / Czwarta Małpa — J.D. Barker *(thriller / seryjny morderca)* — 3/3 ✓ KOMPLET
- `READ` **Czwarta Małpa** — J.D. Barker — detektyw ściga wyrafinowanego seryjnego mordercę.
- `READ` **Piąta Ofiara** — J.D. Barker — kontynuacja śledztwa.
- `READ` **The Sixth Wicked Child** — J.D. Barker — finał trylogii.

### Robert Hunter — Chris Carter *(thriller / seryjny morderca)* — 4/~13
- `READ` **Dziennik śmierci** — Chris Carter — detektyw z LA i wyjątkowo okrutny morderca.
- `READ` **Obserwator śmierci** — Chris Carter.
- `READ` **Genesis** — Chris Carter.
- `READ` **Krucyfiks** — Chris Carter.
- *(seria liczy ok. 13 tomów; pozostałych brak w bibliotece)*

### After (One Second After) — William R. Forstchen *(postapo / katastrofa)* — 1/4
- `READ` **One Second After** — William R. Forstchen — atak EMP wyłącza prąd, upadek małego miasta.
- `READING` **One Year After** — William R. Forstchen *(5%)* — rok po katastrofie.
- `QUEUE` **The Final Day** — William R. Forstchen — finał serii.
- `QUEUE` **Five Years After** — William R. Forstchen.
- `QUEUE` **48 Hours** — William R. Forstchen *(osobna)* — Ziemię czeka rozbłysk słoneczny.

## Przeczytane — pojedyncze tytuły
- `READ` **Demony Rosji** — Witold Jurasz — analiza rosyjskiej polityki i mentalności.
- `READ` **The Raqqa Diaries** — relacja z życia pod ISIS z pierwszej ręki.
- `READ` **Aurora** — David Koepp — globalny blackout po burzy słonecznej.
- `READ` **Hrabia Monte Christo** — Aleksander Dumas — klasyczna opowieść o zemście.
- `READ` **Into the Raging Sea** — Rachel Slade — zatonięcie kontenerowca El Faro.

## W trakcie czytania (wg %)
- `READING 86%` **Wszystko za Everest** — Jon Krakauer — katastrofa na Evereście 1996 oczami świadka.
- `READING 81%` **Imperium bólu** — Patrick Radden Keefe — rodzina Sacklerów i epidemia opioidów.
- `READING 41%` **Cokolwiek powiesz, nic nie mów (Say Nothing)** — Patrick Radden Keefe — IRA i konflikt w Irlandii Płn.
- `READING 31%` **Podróż Sir Ernesta (Endurance)** — Alfred Lansing — przetrwanie wyprawy Shackletona.
- `READING 29%` **Pierwszych piętnaście żywotów Harry'ego Augusta** — Claire North — bohater przeżywa życie wielokrotnie.
- `READING 28%` **Uwolniona (Educated)** — Tara Westover — od survivalistów-mormonów do Cambridge.
- `READING 25%` **The Great Mortality** — John Kelly — czarna śmierć w średniowiecznej Europie.
- `READING 25%` **The Back Channel** — William J. Burns — pamiętnik dyplomaty/dyrektora CIA.
- `READING 12%` **The Aquariums of Pyongyang** — Kang Chol-Hwan — 10 lat w północnokoreańskim łagrze.
- `READING 12%` **Midnight in Chernobyl** — Adam Higginbotham — rekonstrukcja katastrofy w Czarnobylu.
- `READING 10%` **Steve Jobs** — Walter Isaacson — biografia założyciela Apple.
- `READING 9%` **The Black Death** — John Hatcher — dżuma widziana przez jedną angielską wioskę.
- `READING 8%` **Dark Territory** — Fred Kaplan — historia cyberwojny.
- `READING 3%` **Dekameron** — Giovanni Boccaccio — opowieści uciekinierów przed dżumą.
- `READING 2%` **Miracle in the Andes** — Nando Parrado — przetrwanie katastrofy w Andach (relacja ocalałego).
- `READING 2%` **A Journal of the Plague Year** — Daniel Defoe — dżuma w Londynie 1665.
- `READING 2%` **Dżuma** — Albert Camus — epidemia jako metafora kondycji ludzkiej.
- `READING 2%` **Dziewczyna o siedmiu imionach** — Hyeonseo Lee — ucieczka z Korei Północnej.
- `READING 1%` **Doomsday Book** — Connie Willis — historyczka przenosi się w czas dżumy.
- `READING 1%` **Dark Psychology** — James Williams — mechanizmy manipulacji.
- `READING 1%` **K2** — Ed Viesturs — najniebezpieczniejszy ośmiotysięcznik.
- `READING 1%` **102 Minutes** — Jim Dwyer & Kevin Flynn — 11 września minuta po minucie, relacje świadków.

## Kolejka — oznaczone „NEW"
- `QUEUE` **Daemon** — Daniel Suarez — program sterroryzuje świat po śmierci twórcy.
- `QUEUE` **A Spy Among Friends** — Ben Macintyre — Kim Philby i zdrada w MI6.
- `QUEUE` **One Rough Man** — Brad Taylor — pierwszy tom serii Pike Logan (spec-ops).
- `QUEUE` **Blindsight** — Peter Watts — pierwszy kontakt z inteligencją bez świadomości.
- `QUEUE` **Elon Musk** — Walter Isaacson — biografia z pełnym dostępem.

## Kolejka — pozostałe
- `QUEUE` **Nielegalni** — Vincent V. Severski — polski thriller szpiegowski.
- `QUEUE` **Dzieci Czasu (Children of Time)** — Adrian Tchaikovsky — pająki ewoluują w cywilizację.
- `QUEUE` **Rozmowy z katem** — Kazimierz Moczarski — rozmowy z gen. Stroopem w celi.
- `QUEUE` **Hell's Angels** — Hunter S. Thompson — rok wśród gangu motocyklowego.
- `QUEUE` **Dzienniki Kołymskie** — Jacek Hugo-Bader — podróż przez Syberię.
- `QUEUE` **Invisible Child** — Andrea Elliott — bieda jednej rodziny w Nowym Jorku.
- `QUEUE` **Dreamland** — Sam Quinones — epidemia opioidów w USA.
- `QUEUE` **Five Days at Memorial** — Sheri Fink — szpital podczas Katriny, dylematy eutanazji.

---

# CZĘŚĆ II — REKOMENDACJE WG KATEGORII

## Thriller — zabójcy / spec-ops / szpiegowskie
- `REC` ⭐ **Rain Fall (John Rain)** — Barry Eisler — półjapoński zawodowy zabójca, Tokio, stylowo (idealne po Victorze).
- `REC` ⭐ **Terminal List (James Reece)** — Jack Carr — były SEAL, zemsta, autentyzm weterana.
- `REC` ⭐ **Tier One (John Dempsey)** — Andrews & Wilson — najświeższa seria spec-ops do bingowania.
- `REC` **The Kill Artist (Gabriel Allon)** — Daniel Silva — izraelski zabójca i konserwator obrazów, ~25 tomów.
- `REC` **The Perfect Assassin (David Slaton)** — Ward Larsen — zabójca-Mossad w klimacie Toma Wooda.
- `REC` **Point of Impact (Bob Lee Swagger)** — Stephen Hunter — klasyk snajperskiego thrillera.
- `REC` **American Assassin (Mitch Rapp)** — Vince Flynn — fundament gatunku, historia początku.
- `REC` **The Lions of Lucerne (Scot Harvath)** — Brad Thor — kolejna wielka seria spec-ops.
- `REC` **The Cleaner (John Milton)** — Mark Dawson — brytyjski zabójca z sumieniem.
- `REC` **Freedom™** — Daniel Suarez — sequel Daemona.
- `REC` **The Day of the Jackal (Dzień szakala)** — Frederick Forsyth — zawodowiec ma zabić de Gaulle'a; wiesz jak się skończy, i tak wciąga.
- `REC` **The Bourne Identity (Tożsamość Bourne'a)** — Robert Ludlum — mężczyzna bez pamięci, który umie zabijać.
- `REC` ⭐ **Slow Horses / Kulawe konie (Slough House)** — Mick Herron — wyrzuceni agenci MI5, cięty humor + intryga.

## Kryminał — psychologiczny / domestic thriller
- `REC` **The Silent Patient (Pacjentka)** — Alex Michaelides — malarka strzela do męża i milknie.
- `REC` **The Maidens** — Alex Michaelides — Cambridge, profesor klasyki, grupa „Dziewic".
- `REC` **Gone Girl (Zaginiona dziewczyna)** — Gillian Flynn — żona znika w rocznicę ślubu.
- `REC` ⭐ **Sharp Objects (Ostre przedmioty)** — Gillian Flynn — reporterka wraca do rodzinnego miasta pełnego mroku.
- `REC` **Dark Places (Mroczne zakątki)** — Gillian Flynn — ocalała z rodzinnej masakry wraca do sprawy.
- `REC` **The Girl on the Train (Dziewczyna z pociągu)** — Paula Hawkins — świadek z pociągu widzi zbyt wiele.
- `REC` **Behind Her Eyes** — Sarah Pinborough — sekretarka, jej szef i jego żona; finał nie do zapomnienia.
- `REC` **The Wife Between Us** — Greer Hendricks & Sarah Pekkanen — była żona obserwuje nową narzeczoną.
- `REC` **An Anonymous Girl** — Hendricks & Pekkanen — badanie psychologiczne robi się bardzo osobiste.
- `REC` **The Couple Next Door** — Shari Lapena — para wraca z kolacji, dziecko zniknęło.
- `REC` **A Stranger in the House** — Shari Lapena — żona po wypadku, bez pamięci, obca krew w aucie.
- `REC` **An Unwanted Guest** — Shari Lapena — dziesięcioro gości odciętych śnieżycą, pierwsze ciało rano.
- `REC` **The Last Mrs. Parrish** — Liv Constantine — kobieta planuje zająć miejsce idealnej żony.
- `REC` **Sometimes I Lie** — Alice Feeney — kobieta w śpiączce słyszy wszystko, niewiarygodna narratorka.
- `REC` **His & Hers** — Alice Feeney — dziennikarka i jej były mąż-detektyw, oboje kłamią.
- `REC` **Rock Paper Scissors** — Alice Feeney — rocznicowy weekend pary pełen kłamstw.
- `REC` **The Family Upstairs** — Lisa Jewell — niemowlę znalezione w domu z trzema ciałami.
- `REC` **Then She Was Gone** — Lisa Jewell — matka spotyka kogoś łudząco podobnego do zaginionej córki.
- `REC` **The Push** — Ashley Audrain — matka czuje, że z córką jest coś nie tak.
- `REC` **The It Girl** — Ruth Ware — śmierć przyjaciółki z Oxfordu wraca po latach.
- `REC` **The Turn of the Key** — Ruth Ware — niania w szkockim smart-domie, który żyje własnym życiem.
- `REC` **The Death of Mrs Westaway** — Ruth Ware — spadek od rodziny, której się nie zna.
- `REC` **The Lying Game** — Ruth Ware — cztery przyjaciółki i wspólny sekret ze szkoły.
- `REC` **The It Girl / The Wife** — Alafair Burke — mąż oskarżony o napaść, żona zna jego tajemnice.
- `REC` **The Last Flight** — Julie Clark — dwie kobiety zamieniają się biletami; jeden samolot się rozbija.
- `REC` **Verity** — Colleen Hoover — pisarka znajduje autobiografię autorki, którą zastępuje *(ostrzeżenie: mocne)*.
- `REC` **The Maid (Pokojówka)** — Freida McFadden — pomoc domowa w domu, gdzie wszystko jest nie tak.
- `REC` **The Guest List (Lista gości)** — Lucy Foley — wesele na irlandzkiej wyspie, ktoś ginie.
- `REC` **The Hunting Party (Polowanie)** — Lucy Foley — przyjaciele w szkockiej rezydencji, rano jedno ciało.
- `REC` **The Silent Companions / Sometimes I Lie** — patrz wyżej.

## Kryminał — seryjni mordercy / profilerzy
- `REC` ⭐ **The Mermaids Singing (Tony Hill)** — Val McDermid — profiler kontra seryjny morderca (serial „Wire in the Blood").
- `REC` ⭐ **The Bone Collector (Kolekcjoner kości; Lincoln Rhyme)** — Jeffery Deaver — sparaliżowany kryminolog, forensyka, zwroty.
- `REC` **Heartsick (Gretchen Lowell)** — Chelsea Cain — detektyw i piękna seryjna morderczyni.
- `REC` **Red Dragon (Czerwony Smok)** — Thomas Harris — pierwszy Hannibal Lecter.
- `REC` **The Silence of the Lambs (Milczenie owiec)** — Thomas Harris — agentka FBI prosi Lectera o pomoc.
- `REC` **Triptych (Will Trent)** — Karin Slaughter — mroczny, dobrze napisany dark crime.
- `REC` **Birdman (Jack Caffery)** — Mo Hayder — brutalny, w klimacie Chrisa Cartera.
- `REC` **The Alienist (Alienista)** — Caleb Carr — Nowy Jork 1896, polowanie na mordercę dzieci.
- `REC` **Whisper Man** — Alex North — miasteczko, lokalna legenda szepcząca do dzieci.
- `REC` **The Shadow Friend** — Alex North — morderstwo z przeszłości powraca.
- `REC` **The Chestnut Man** — Søren Sveistrup — duński thriller, kasztanowe figurki na miejscach zbrodni.
- `REC` **The Coast-to-Coast Murders** — James Patterson & J.D. Barker — dwóch braci oskarżonych o serię zabójstw.

## Kryminał — noir / hardboiled / klasyka gatunku
- `REC` ⭐ **The Big Sleep (Wielki sen; Philip Marlowe)** — Raymond Chandler — fundament hard-boiled.
- `REC` **The Maltese Falcon (Sokół maltański)** — Dashiell Hammett — drugi filar amerykańskiego noir.
- `REC` **L.A. Confidential (Tajemnice Los Angeles)** — James Ellroy — brutalny, gęsty noir lat 50. *(styl wymagający)*.
- `REC` **And Then There Were None (I nie było już nikogo)** — Agatha Christie — 10 osób na wyspie, giną po kolei.
- `REC` **Rebecca (Rebeka)** — Daphne du Maurier — młoda żona w cieniu poprzedniczki.

## Kryminał skandynawski (Nordic noir)
- `REC` ⭐ **Pantera (The Leopard; Harry Hole #8)** — Jo Nesbø — bezpośrednia kontynuacja Bałwana, najbrutalniejszy tom.
- `REC` **Czerwone gardło (The Redbreast; Hole #3)** — Jo Nesbø — początek „trylogii Oslo", często uznawany za najlepszy.
- `REC` **Upiór (Phantom; Hole #9)** — Jo Nesbø — najbardziej osobista sprawa Harry'ego.
- `REC` **Policja (Police; Hole #10)** — Jo Nesbø — mordowani są policjanci.
- `REC` **Syn (The Son)** — Jo Nesbø — narkoman odsiadujący cudze wyroki ucieka, by się zemścić.
- `REC` **Krew na śniegu (Blood on Snow)** — Jo Nesbø — płatny zabójca zakochuje się w celu.
- `REC` **Łowcy głów (Headhunters)** — Jo Nesbø — łowca talentów i złodziej obrazów we własnej pułapce.
- `REC` **Królestwo (The Kingdom)** + **Krew z krwi (Blood Ties)** — Jo Nesbø — dwaj bracia i mroczny sekret.
- `REC` ⭐⭐ **Hipnotyzer (Joona Linna)** — Lars Kepler — najbliższy odpowiednik Nesbø, mroczny i wartki.
- `REC` ⭐ **Wędruję sama (I'm Travelling Alone)** — Samuel Bjørk — norweski, bardzo nesbø-podobny.
- `REC` ⭐ **Kobieta w klatce (Departament Q)** — Jussi Adler-Olsen — duński, mrok + czarny humor, 10 tomów.
- `REC` ⭐ **Roseanna (Martin Beck)** — Maj Sjöwall & Per Wahlöö — duet z lat 60., który wymyślił gatunek.
- `REC` ⭐ **Mordercy bez twarzy (Wallander)** — Henning Mankell — ojciec chrzestny Nordic noir.
- `REC` ⭐ **Mężczyźni, którzy nienawidzą kobiet (Millennium)** — Stieg Larsson — Lisbeth Salander *(tomy 4-6 słabsze)*.
- `REC` ⭐ **Jar City (komisarz Erlendur)** — Arnaldur Indriðason — najlepszy islandzki kryminał.
- `REC` **Snowblind (Mroczna Islandia)** — Ragnar Jónasson — atmosferyczny, odcięte miasteczko.
- `REC` **Yrsa Sigurðardóttir** — islandzka, mroczniejsza, z domieszką horroru.
- `REC` **Księżniczka z lodu (Fjällbacka)** — Camilla Läckberg — bardziej obyczajowa odmiana *(bywa schematyczna)*.
- `REC` **Karin Fossum (komisarz Sejer)** — cichy, psychologiczny norweski kryminał.

## Kryminał — międzynarodowy i literacki
- `REC` ⭐ **Poświęcenie podejrzanego X** — Keigo Higashino — od początku wiesz, kto zabił, a i tak nie odłożysz (Japonia).
- `REC` ⭐ **Alex (trylogia Verhœvena)** — Pierre Lemaitre — ekstremalnie mroczny francuski thriller.
- `REC` ⭐ **Niewidzialny strażnik (trylogia Baztán)** — Dolores Redondo — hiszpański Nordic noir, dolina Basków.
- `REC` **Kształt wody (komisarz Montalbano)** — Andrea Camilleri — Sycylia, lżejsze, urokliwe (Włochy).
- `REC` ⭐ **Mystic River (Rzeka tajemnic)** — Dennis Lehane — najlepszy współczesny amerykański kryminał literacki.
- `REC` **Shutter Island (Wyspa skazańców)** — Dennis Lehane — śledztwo w zamkniętym zakładzie.
- `REC` ⭐ **The Power of the Dog (Potęga psa)** — Don Winslow — epicka wojna narkotykowa *(brutalne)*.
- `REC` **No Country for Old Men (To nie jest kraj dla starych ludzi)** — Cormac McCarthy — pościg, zabójca-psychopata.
- `REC` ⭐ **Black Echo (Harry Bosch)** — Michael Connelly — detektyw z LA, ~24 tomy do bingowania.
- `REC` **Knots and Crosses (Rebus)** — Ian Rankin — Edynburg, zgryźliwy inspektor.
- `REC` ⭐ **In the Woods (W lesie; Dublin Murder Squad)** — Tana French — literacki, psychologiczny slow-burn.
- `REC` **The Likeness / Broken Harbour / The Witch Elm** — Tana French — kolejne tomy/standalone.
- `REC` **The Talented Mr Ripley (Utalentowany pan Ripley)** — Patricia Highsmith — uroczy psychopata we Włoszech.
- `REC` **Razorblade Tears** — S.A. Cosby — dwóch ojców-byłych zeków mści śmierć synów.
- `REC` **Blacktop Wasteland** — S.A. Cosby — czarny mechanik wciągnięty z powrotem w przestępczość.
- `REC` **The Firm (Firma)** — John Grisham — kancelaria pierze pieniądze mafii.
- `REC` **The Client (Klient)** — John Grisham — chłopiec poznaje śmiertelny sekret.
- `REC` **The Innocent Man** — John Grisham *(non-fiction)* — niesłusznie skazany na śmierć.
- `REC` **The Da Vinci Code (Kod Leonarda da Vinci)** — Dan Brown — symbolog, Luwr, pogoń przez Europę.
- `REC` **The Name of the Rose (Imię róży)** — Umberto Eco — klasztor 1327, cykl morderstw mnichów.

## Science fiction — hard / koncept / czas
- `REC` ⭐ **Projekt Hail Mary** — Andy Weir — samotny astronauta bez pamięci ratuje Ziemię (najlepsze hard-SF ostatnich lat).
- `REC` **Marsjanin (The Martian)** — Andy Weir — astronauta sam na Marsie musi przetrwać.
- `REC` ⭐ **Dark Matter** — Blake Crouch — fizyk budzi się w innej wersji własnego życia.
- `REC` **Rekursja (Recursion)** — Blake Crouch — ludzie pamiętają życia, których nie przeżyli.
- `REC` **Upgrade** — Blake Crouch — edycja genów, szybkie tempo.
- `REC` ⭐ **Problem trzech ciał** — Liu Cixin — chińska rewolucja kulturalna i pierwszy kontakt.
- `REC` **Ciemny las (The Dark Forest)** — Liu Cixin — teoria „ciemnego lasu" wszechświata.
- `REC` **Koniec śmierci (Death's End)** — Liu Cixin — finał w skali kosmologicznej.
- `REC` **Echopraxia** — Peter Watts — kontynuacja Blindsight, brutalna intelektualnie.
- `REC` **Kwiaty dla Algernona** — Daniel Keyes — eksperyment podnosi IQ, dziennik ewoluuje.
- `REC` **Nie opuszczaj mnie (Never Let Me Go)** — Kazuo Ishiguro — z tym światem coś jest fundamentalnie nie tak.
- `REC` **Klara i słońce** — Kazuo Ishiguro — robot-towarzyszka opowiada o świecie.
- `REC` ⭐ **Modyfikowany węgiel (Altered Carbon)** — Richard K. Morgan — najemnik, noir, cyberpunk (most thriller↔SF).
- `REC` **Anihilacja (Annihilation)** — Jeff VanderMeer — cztery kobiety w Obszarze X.
- `REC` **Borne** — Jeff VanderMeer — postapokaliptyczne miasto, organizm, który mówi.

## Science fiction — space opera / epicki
- `REC` ⭐ **Przebudzenie Lewiatana (The Expanse)** — James S.A. Corey — skala Red Rising, 9 tomów.
- `REC` **Diuna (Dune)** — Frank Herbert — pustynna planeta, polityka, mesjanizm.
- `REC` **Hyperion** + **Fall of Hyperion** — Dan Simmons — siedmioro pielgrzymów, galaktyka na krawędzi.
- `REC` **Ilium** — Dan Simmons — Troja na Marsie, posthumanie, erudycyjny epos.
- `REC` **Dzieci Ruiny (Children of Ruin)** — Adrian Tchaikovsky — kontynuacja „Dzieci Czasu", tym razem ośmiornice.
- `REC` **Shards of Earth** — Adrian Tchaikovsky — inna epicka space opera.
- `REC` **A Memory Called Empire** — Arkady Martine — ambasadorka w sercu ogromnego imperium (Hugo).
- `REC` **The Long Way to a Small, Angry Planet** — Becky Chambers — ciepła załoga statku, mało akcji.
- `REC` **Seveneves** — Neal Stephenson — Księżyc eksploduje, ludzkość ma dwa lata.
- `REC` **Anathem** — Neal Stephenson — filozoficzni mnisi i coś z kosmosu.
- `REC` **The Abyss Beyond Dreams** — Peter F. Hamilton — galaktyka uwięziona w Pustoce.

## Postapokalipsa / katastrofa / dystopia (fikcja)
- `REC` ⭐ **Droga (The Road)** — Cormac McCarthy — ojciec i syn przez spalone USA (Pulitzer).
- `REC` ⭐ **Bastion (The Stand)** — Stephen King — wirus zabija 99%, epicki finał dobra i zła.
- `REC` **Swan Song** — Robert McCammon — nuklearna apokalipsa, często stawiany wyżej od Bastionu.
- `REC` ⭐ **Lucifer's Hammer** — Niven & Pournelle — kometa uderza w Ziemię (dla fana One Second After).
- `REC` **Alas, Babylon** — Pat Frank — nuklearny atak, mała społeczność na Florydzie.
- `REC` **A Canticle for Leibowitz** — Walter M. Miller Jr. — zakonnicy chronią wiedzę przez 1800 lat po wojnie.
- `REC` **On the Beach** — Nevil Shute — Australia czeka na radioaktywną chmurę.
- `REC` **Level 7** — Mordecai Roshwald — oficer nuklearny w bunkrze 4500 m pod ziemią.
- `REC` **The Passage** + **The Twelve** — Justin Cronin — rządowy eksperyment tworzy wampiry.
- `REC` ⭐ **Ślepy (Blindness)** — José Saramago — epidemia ślepoty (Nobel).
- `REC` **Widzący (Seeing)** — José Saramago — kontynuacja, ostrzejsza politycznie.
- `REC` **Opowieść podręcznej (The Handmaid's Tale)** — Margaret Atwood — teokratyczny Gilead.
- `REC` **Oryx and Crake** + **Rok potopu** + **MaddAddam** — Margaret Atwood — trylogia biokatastrofy.
- `REC` ⭐ **Stacja jedenaście (Station Eleven)** — Emily St. John Mandel — po pandemii wędrowni aktorzy grają Szekspira.
- `REC` **Sea of Tranquility** + **The Glass Hotel** — Emily St. John Mandel — powiązany świat, gra czasem.
- `REC` ⭐ **Parable of the Sower** + **Parable of the Talents** — Octavia Butler — dystopia, która wygląda jak prognoza.
- `REC` **Kindred** — Octavia Butler — współczesna kobieta wciągnięta w czas plantacji.
- `REC` **The Children of Men** — P.D. James — ludzkość przestała się rozmnażać.
- `REC` **The Power** — Naomi Alderman — kobiety zyskują moc rażenia prądem (Booker).
- `REC` **The Water Knife** — Paolo Bacigalupi — wojna o wodę na zachodzie USA.
- `REC` **The Windup Girl** — Paolo Bacigalupi — biopunk, Tajlandia przyszłości (Hugo/Nebula).
- `REC` **Ministerstwo dla Przyszłości** — Kim Stanley Robinson — klimat, forma dokumentalna.
- `REC` **Nowy Jork 2140** — Kim Stanley Robinson — półzatopione miasto, wciąż żywe.
- `REC` **The Drowned World** / **The Burning World** — J.G. Ballard — katastrofa jako regresja psychiczna.
- `REC` **World War Z** — Max Brooks — apokalipsa zombie jako oral history.
- `REC` **I Am Legend** — Richard Matheson — jeden człowiek po epidemii wampiryzmu.
- `REC` **One Second After** — patrz biblioteka; **The Forever War** — Joe Haldeman — żołnierz wraca po dekadach relatywistycznych.
- `REC` **Roadside Picnic** — bracia Strugaccy — strefy po „pikniku" obcych.
- `REC` **Solaris** — Stanisław Lem — psycholog nad oceanem-organizmem (polski klasyk).
- `REC` **Nowy wspaniały świat (Brave New World)** — Aldous Huxley — dystopia komfortu.
- `REC` **Rok 1984 (1984)** — George Orwell — totalitaryzm jako instrukcja, nie ostrzeżenie.
- `REC` **Folwark zwierzęcy (Animal Farm)** — George Orwell — satyra na rewolucję.
- `REC` **Mechaniczna pomarańcza (A Clockwork Orange)** — Anthony Burgess — resocjalizacja i wolna wola.

## Fantasy
- `REC` **Imię wiatru (The Name of the Wind)** — Patrick Rothfuss — legendarny bohater opowiada swą historię.
- `REC` **Szóstka wron (Six of Crows)** — Leigh Bardugo — ekipa złodziei i niemożliwy skok.
- `REC` **Mistborn** — Brandon Sanderson — najlepszy magic system; plan obalenia boga-cesarza.
- `REC` **The Priory of the Orange Tree** — Samantha Shannon — smoki, polityka, 800 stron.
- `REC` **The Poppy War** — R.F. Kuang — wojna z magią, brutalna trylogia.
- `REC` **Babel** — R.F. Kuang — Oxford XIX w., magia oparta na tłumaczeniu, o kolonializmie.
- `REC` **Jonathan Strange & Mr Norrell** — Susanna Clarke — dwaj magowie wskrzeszają magię w Anglii.
- `REC` **American Gods** — Neil Gaiman — stare bogi kontra nowe w Ameryce.
- `REC` **The Ocean at the End of the Lane** — Neil Gaiman — mężczyzna odkrywa ukrytą pamięć dzieciństwa.
- `REC` **The Goblin Emperor** — Katherine Addison — pogardzany syn zostaje cesarzem.
- `REC` **The Atlas Six** — Olivie Blake — sześcioro magów, po roku zostanie pięcioro.
- `REC` **The Library at Mount Char** — Scott Hawkins — biblioteka boga, który zaginął.
- `REC` **Piranesi** — Susanna Clarke — mężczyzna w niekończącym się Domu pełnym posągów i mórz.
- `REC` **Władca Pierścieni (LOTR)** — J.R.R. Tolkien — klasyk; kto wjedzie, nie wyjedzie.
- `REC` **The Princess Bride (Narzeczona księcia)** — William Goldman — piraci, olbrzymi, prawdziwa miłość + metafikcja.

## Fikcja literacka — współczesna
- `REC` **Tam, gdzie śpiewają raki (Where the Crawdads Sing)** — Delia Owens — dziewczyna z bagien, morderstwo, proces.
- `REC` **Cień wiatru (The Shadow of the Wind)** — Carlos Ruiz Zafón — powojenna Barcelona, Cmentarz Zapomnianych Książek.
- `REC` **Tajemna historia (The Secret History)** — Donna Tartt — studenci greki popełniają morderstwo.
- `REC` **Szczygieł (The Goldfinch)** — Donna Tartt — chłopiec kradnie obraz po zamachu w muzeum (Pulitzer).
- `REC` **The Little Friend** — Donna Tartt — dziewczynka bada śmierć brata sprzed lat.
- `REC` **Łowca latawców (The Kite Runner)** — Khaled Hosseini — Afganistan, dwóch chłopców, zdrada.
- `REC` **Złodziejka książek (The Book Thief)** — Markus Zusak — Niemcy 1939, narratorem Śmierć.
- `REC` **Życie Pi (Life of Pi)** — Yann Martel — chłopiec na tratwie z tygrysem.
- `REC` **Szantaram (Shantaram)** — Gregory David Roberts — uciekinier w slumsach Bombaju.
- `REC` **A Little Life (Małe życie)** — Hanya Yanagihara — czterech przyjaciół, jeden z sekretem *(niszczy)*.
- `REC` **To Paradise** + **The People in the Trees** — Hanya Yanagihara — ambitne, niewygodne.
- `REC` **Biblioteka o północy (The Midnight Library)** — Matt Haig — biblioteka alternatywnych żyć.
- `REC` **Dżentelmen w Moskwie (A Gentleman in Moscow)** — Amor Towles — arystokrata skazany na hotel Metropol.
- `REC` **Hamnet** — Maggie O'Farrell — historia zmarłego syna Szekspira.
- `REC` **Całe to światło, którego nie widzimy (All the Light We Cannot See)** — Anthony Doerr — okupowane Saint-Malo (Pulitzer).
- `REC` **Siedmiu mężów Evelyn Hugo** — Taylor Jenkins Reid — legendarna aktorka i jej małżeństwa.
- `REC` **Daisy Jones & The Six** — Taylor Jenkins Reid — rockowa kapela lat 70. w formie wywiadów.
- `REC` **Jutro, jutro i znów jutro** — Gabrielle Zevin — troje twórców gier, miłość bez romansu.
- `REC` **Lekcje chemii (Lessons in Chemistry)** — Bonnie Garmus — chemiczka zostaje gwiazdą programu kulinarnego.
- `REC` **Eleanor Oliphant ma się całkiem dobrze** — Gail Honeyman — samotność przechodząca w czułość.
- `REC` **Mniej (Less)** + **Less is Lost** — Andrew Sean Greer — nieudany pisarz w podróży dookoła świata (Pulitzer).
- `REC` **A Man Called Ove (Mężczyzna imieniem Ove)** — Fredrik Backman — zgryźliwy wdowiec i sąsiedzi.
- `REC` **Anxious People** — Fredrik Backman — nieudane porwanie, same kryzysy życiowe.
- `REC` **Beartown** — Fredrik Backman — hokej, małe miasto, trudny wybór społeczności.
- `REC` **Pachinko** — Min Jin Lee — koreańska rodzina przez cztery pokolenia w Japonii.
- `REC` **The Vanishing Half** — Brit Bennett — bliźniaczki, jedna żyje jako biała, druga jako czarna.
- `REC` **Homegoing** — Yaa Gyasi — dwie siostry i ich potomkowie przez 7 pokoleń.
- `REC` **Americanah** — Chimamanda Ngozi Adichie — Nigeryjka w USA i Anglii, o rasie i powrocie.
- `REC` **Half of a Yellow Sun** — Chimamanda Ngozi Adichie — wojna w Biafrze oczami trojga bliskich.
- `REC` **Demon Copperhead** — Barbara Kingsolver — Dickens w Appalachach, epidemia opioidów (Pulitzer).
- `REC` **The Overstory (Overstory)** — Richard Powers — dziewięcioro ludzi i drzewa (Pulitzer).
- `REC` **Trust** — Hernán Diaz — historia małżeństwa miliarderów opowiedziana cztery razy (Pulitzer).
- `REC` **Lincoln in the Bardo** — George Saunders — duchy w limbo przy zmarłym synu Lincolna (Booker).
- `REC` **The Seven Moons of Maali Almeida** — Shehan Karunatilaka — fotograf ma 7 dni w zaświatach (Booker).

## Fikcja literacka — klasyka i Nobliści
- `REC` **Sto lat samotności** — Gabriel García Márquez — siedem pokoleń rodziny Buendía.
- `REC` **Dom duchów (The House of the Spirits)** — Isabel Allende — cztery pokolenia chilijskiej rodziny.
- `REC` **Zbrodnia i kara** — Fiodor Dostojewski — student morduje lichwiarkę, głowa się rozpada.
- `REC` **Notes from Underground (Notatki z podziemia)** — Dostojewski — monolog petersburskiego paranoika.
- `REC` **Anna Karenina** — Lew Tołstoj — wciąga od dworca w Petersburgu.
- `REC` **Mistrz i Małgorzata** — Michaił Bułhakow — diabeł w stalinowskiej Moskwie, kot pije wódkę.
- `REC` **The Stranger (Obcy)** — Albert Camus — „Dzisiaj zmarła mama. A może wczoraj".
- `REC` **The Plague (Dżuma)** — patrz biblioteka.
- `REC` **The Bell Jar (Szklany klosz)** — Sylvia Plath — autobiograficzna powieść o depresji.
- `REC` **Lolita** — Vladimir Nabokov — jedno z najsłynniejszych i najbardziej niepokojących otwarć.
- `REC` **Beloved (Umiłowana)** — Toni Morrison — zbiegła niewolnica nawiedzana przez ducha córki (Nobel).
- `REC` **Song of Solomon** — Toni Morrison — najprzystępniejsza Morrison.
- `REC` **Atonement (Pokuta)** — Ian McEwan — kłamstwo dziecka niszczy życia.
- `REC` **On Chesil Beach** / **The Comfort of Strangers** / **The Children Act** — Ian McEwan — krótkie, precyzyjne, niepokojące.
- `REC` **The Sense of an Ending** / **The Only Story** — Julian Barnes — pamięć i miłość (Booker).
- `REC` **Stoner** — John Williams — życie zwyczajnego profesora, jedna z najpiękniejszych powieści XX w.
- `REC` **Augustus** / **Butcher's Crossing** — John Williams — równie dobre.
- `REC` **Cancer Ward** / **One Day in the Life of Ivan Denisovich** — Aleksander Sołżenicyn — sowiecki system od środka.
- `REC` **Doktor Żywago** — Borys Pasternak — lekarz-poeta w rewolucji (Nobel).
- `REC` **Disgrace (Hańba)** / **Waiting for the Barbarians** — J.M. Coetzee — RPA, imperium, wina (Booker/Nobel).
- `REC` **Slaughterhouse-Five (Rzeźnia numer pięć)** — Kurt Vonnegut — bombardowanie Drezna i podróże w czasie.
- `REC` **Cat's Cradle (Kocia kołyska)** — Kurt Vonnegut — lód-9 i religia Bokononizmu.
- `REC` **The Master and Margarita** — patrz wyżej.
- `REC` **Middlesex** / **The Virgin Suicides** / **The Marriage Plot** — Jeffrey Eugenides — rodzina, dorastanie, ironia.
- `REC` **The Plot Against America** / **American Pastoral** — Philip Roth — alternatywna Ameryka / bomba córki.
- `REC` **Nie mów nikomu / literatura** — patrz thriller.

## Realizm magiczny / dziwne / eksperymentalne
- `REC` **Kronika ptaka nakręcacza** — Haruki Murakami — mężczyzna, studnia, zaginiona żona.
- `REC` **Norwegian Wood** — Haruki Murakami — studenckie Tokio, miłość, strata.
- `REC` **1Q84** — Haruki Murakami — równoległy świat, najambitniejszy Murakami.
- `REC` **Kafka on the Shore** / **Hard-Boiled Wonderland** — Haruki Murakami — dwie splatające się historie.
- `REC` **Cloud Atlas (Atlas chmur)** — David Mitchell — sześć historii w matrioszce.
- `REC` **Życie po życiu (Life After Life)** — Kate Atkinson — kobieta umiera i rodzi się wciąż na nowo.
- `REC` **House of Leaves** — Mark Z. Danielewski — dom większy w środku, tekst łamie zasady druku.
- `REC` **Pachnidło (Perfume)** — Patrick Süskind — człowiek bez zapachu morduje dla perfum.
- `REC` **Zanim wystygnie kawa** — Toshikazu Kawaguchi — kawiarnia, w której można cofnąć czas.
- `REC` **The Night Circus** / **The Starless Sea** — Erin Morgenstern — magiczny cyrk / podziemne morze opowieści.
- `REC` **The Snow Child** — Eowyn Ivey — para na Alasce lepi dziecko ze śniegu.
- `REC` **Trzynasta opowieść (The Thirteenth Tale)** — Diane Setterfield — umierająca pisarka wyznaje prawdę.
- `REC` **Siedem śmierci Evelyn Hardcastle** — Stuart Turton — bohater budzi się w innym ciele, 8 prób.
- `REC` **Mexican Gothic** — Silvia Moreno-Garcia — Meksyk lat 50., dziwny ród w górach.
- `REC` **We Have Always Lived in the Castle** / **The Haunting of Hill House** — Shirley Jackson — mistrzyni niepokoju.
- `REC` **The Last House on Needless Street** — Catriona Ward — niewiarygodny narrator: „jestem mordercą".
- `REC` **The Cabin at the End of the World** — Paul Tremblay — rodzina i cena ratowania świata.
- `REC` **Bird Box** — Josh Malerman — coś, na co nie wolno spojrzeć.

## Japońska proza (osobno — wyraźny nurt)
- `REC` **Convenience Store Woman** — Sayaka Murata — kobieta, którą rozumie tylko sklep 24/7.
- `REC` **Earthlings** — Sayaka Murata — ekstremalnie niewygodna, niezapomniana.
- `REC` **The Memory Police** / **Hotel Iris** / **The Housekeeper and the Professor** — Yoko Ogawa — ciche, hipnotyczne.
- `REC` **Snow Country** — Yasunari Kawabata — gejsza w górach, cisza, śnieg (Nobel).
- `REC` **The Travelling Cat Chronicles** — Hiro Arikawa — podróż z kotem-narratorem.
- `REC` **The Cat Who Saved Books** — Sosuke Natsukawa — mówiący kot i uwięzione książki.
- `REC` **Sweet Bean Paste** — Durian Sukegawa — 76-latka i budka z bułkami.
- `REC` **The Vegetarian** / **Greek Lessons** — Han Kang — koreańska noblistka, niepokojące i ciche.

## Proza polska
- `REC` ⭐ **Król** — Szczepan Twardoch — przedwojenna Warszawa, żydowski gangster.
- `REC` **Morfina** — Szczepan Twardoch — wrzesień 1939, uwodziciel wbrew sobie zostaje szpiegiem.
- `REC` **Drach** — Szczepan Twardoch — saga śląska z perspektywy ziemi.
- `REC` ⭐ **Ziarno prawdy** — Zygmunt Miłoszewski — prokurator Szacki w Sandomierzu (najlepszy polski kryminał XXI w.).
- `REC` **Lód** — Jacek Dukaj — alternatywna historia, zima trzyma Europę od 1908.
- `REC` **Prowadź swój pług przez kości umarłych** — Olga Tokarczuk — emerytka w Sudetach, zwierzęta się mszczą (Nobel).
- `REC` **Bieguni** / **Prawiek i inne czasy** / **Księgi Jakubowe** — Olga Tokarczuk.
- `REC` **Ferdydurke** — Witold Gombrowicz — groteska o „formie".
- `REC` **Lalka** — Bolesław Prus — Wokulski, Łęcka, kapitalistyczna Warszawa (wróć po liceum).
- `REC` **Spis cudzołożnic** — Jerzy Pilch — oprowadzanie szwedzkiego profesora po Krakowie.

## Humor / satyra
- `REC` ⭐ **Paragraf 22 (Catch-22)** — Joseph Heller — najlepsza satyra antywojenna.
- `REC` ⭐ **Autostopem przez Galaktykę** — Douglas Adams — Ziemia zburzona pod obwodnicę; odpowiedź to 42.
- `REC` ⭐ **Dobry omen (Good Omens)** — Terry Pratchett & Neil Gaiman — anioł i demon zapobiegają Apokalipsie.
- `REC` **Kolor magii / Straż! Straż! (Świat Dysku)** — Terry Pratchett — satyra na rzeczywistość na płaskim świecie.
- `REC` **Jeeves (np. The Code of the Woosters)** — P.G. Wodehouse — idiota i genialny kamerdyner, czysta radość.
- `REC` **Trzech panów w łódce** — Jerome K. Jerome — drobne katastrofy nad Tamizą, humor sprzed 135 lat.
- `REC` **Cold Comfort Farm** — Stella Gibbons — parodia literatury wiejskiej.
- `REC` **Lucky Jim** — Kingsley Amis — komedia akademicka, legendarny pijacki wykład.
- `REC` **A Confederacy of Dunces** — John Kennedy Toole — Ignatius Reilly, jedna z najlepszych komicznych postaci (Pulitzer).
- `REC` **The Sellout** — Paul Beatty — satyra na rasizm w USA (Booker).
- `REC` **Rzeźnia numer pięć / Śniadanie mistrzów** — Kurt Vonnegut — humor czarny i głęboki.
- `REC` **Scoop** / **A Handful of Dust** — Evelyn Waugh — brytyjska ironia (dziennikarstwo / arystokracja).
- `REC` **Money** — Martin Amis — ekscesy lat 80., proza jak haj.
- `REC` **Portnoy's Complaint (Kompleks Portnoya)** — Philip Roth — neurotyczny monolog u psychoanalityka.
- `REC` **Lamb** / **Noir** — Christopher Moore — ewangelia wg Biffa / parodia noir.
- `REC` **Dobry wojak Szwejk** — Jaroslav Hašek — czeski żołnierz rozkłada machinę wojenną absurdem.
- `REC` **Zorba Grek** — Nikos Kazantzakis — filozofia radości istnienia.
- `REC` **My Family and Other Animals** — Gerald Durrell — ekscentryczna rodzina na Korfu.
- `REC` **Where'd You Go, Bernadette** — Maria Semple — geniuszka znika przed podróżą na Antarktydę.
- `REC` **The Rosie Project** — Graeme Simsion — profesor tworzy kwestionariusz na żonę.
- `REC` **Klub morderców z czwartków** — Richard Osman — czworo emerytów rozwiązuje morderstwa.
- `REC` **Candide (Kandyd)** — Voltaire — satyra na optymizm, 150 stron, wciąż cięta.
- `REC` **Duma i uprzedzenie / Emma** — Jane Austen — najostrzejsza ironia XIX w.

## YA / romantasy / BookTok *(bardzo wysokie oceny, ale często wtórne — z ostrzeżeniem)*
- `REC` **Skrzydła krwi (Fourth Wing)** — Rebecca Yarros — akademia jeźdźców smoków, romans, wysokie stawki.
- `REC` **Szóstka wron** — patrz fantasy.
- `REC` **Dobra dziewczyna, dobre morderstwo** — Holly Jackson — nastolatka odkopuje sprawę sprzed 5 lat.
- `REC` **Outlander** — Diana Gabaldon — pielęgniarka cofa się do XVIII-wiecznej Szkocji.

---

# CZĘŚĆ III — LITERATURA FAKTU

## True crime / dziennikarstwo śledcze
- `REC` ⭐ **Z zimną krwią (In Cold Blood)** — Truman Capote — czterech zabitych Clutterów; wynalazek nowoczesnego true crime.
- `REC` ⭐ **Zabójcy księżycowego kwiatu (Killers of the Flower Moon)** — David Grann — mordy na Osagach i narodziny FBI.
- `REC` ⭐ **Bad Blood** — John Carreyrou — Theranos i Elizabeth Holmes.
- `REC` **The Five** — Hallie Rubenhold — pięć ofiar Kuby Rozpruwacza jako ludzie, nie tło.
- `REC` **The Poisoner's Handbook** — Deborah Blum — narodziny medycyny sądowej.
- `REC` **Hidden Valley Road** — Robert Kolker — rodzina z sześciorgiem dzieci ze schizofrenią.
- `REC` **Stranger in the Woods** — Michael Finkel — pustelnik żyjący 27 lat sam w lesie.
- `REC` **The Stranger Beside Me** — (true crime klasyka) — profil seryjnego mordercy z bliska.
- `REC` **American Kingpin** — Nick Bilton — Silk Road i „Dread Pirate Roberts".
- `REC` **The Spider Network** — David Enrich — manipulacja LIBOR.
- `REC` **Helter Skelter** — Vincent Bugliosi — sprawa Mansona oczami prokuratora.
- `REC` **Catch and Kill** — Ronan Farrow — śledztwo ws. Weinsteina.
- `REC` **She Said** — Kantor & Twohey — dziennikarki NYT łamią sprawę Weinsteina.
- `REC` **Rogues** — Patrick Radden Keefe — 12 reporterskich portretów skomplikowanych postaci.

## Katastrofy i przetrwanie — z pierwszej ręki
- `REC` ⭐ **Dotknięcie pustki (Touching the Void)** — Joe Simpson — złamana noga 6000 m n.p.m., wyjście ze szczeliny.
- `REC` **The Beckoning Silence** — Joe Simpson — Eiger, głębszy emocjonalnie.
- `REC` ⭐ **Left for Dead** — Beck Weathers — zostawiony na Evereście '96, wstał i zszedł.
- `REC` **The Climb** — Anatolij Bukrejew — druga perspektywa katastrofy z 1996.
- `REC` **Korona Himalajów** / **Mój pionowy świat** — Jerzy Kukuczka — polski himalaista, 14 ośmiotysięczników.
- `REC` **Annapurna** — Maurice Herzog — pierwsze zdobycie ośmiotysięcznika, amputacje na śniegu.
- `REC` **Białe pajęcze (The White Spider)** — Heinrich Harrer — pierwsze przejście północnej ściany Eigeru.
- `REC` **Seven Years in Tibet** — Heinrich Harrer — ucieczka z obozu do Tybetu, przyjaźń z Dalajlamą.
- `REC` **Adrift: 76 Days Lost at Sea** — Steven Callahan — 76 dni na tratwie na Atlantyku.
- `REC` **438 Days** — Jonathan Franklin — 438 dni dryfu przez Pacyfik.
- `REC` ⭐ **Miracle in the Andes** — patrz biblioteka (relacja Parrado).
- `REC` **Alive** — Piers Paul Read — ta sama katastrofa Andów oczami wszystkich 16 ocalałych.
- `REC` **Lost in the Jungle** — Yossi Ghinsberg — trzy tygodnie sam w amazońskiej dżungli.
- `REC` **When I Fell from the Sky** — Juliane Koepcke — spadła z 3000 m i przeżyła, 11 dni w dżungli.
- `REC` **South** — Ernest Shackleton — pamiętnik lidera wyprawy „Endurance".
- `REC` **Najgorsza podróż świata** — Apsley Cherry-Garrard — Antarktyda Scotta, świadectwo ocalałego.
- `REC` **Mawson's Will** — Lennard Bickel — samotny powrót 160 km przez lód.
- `REC` **Miracle / K2: The Savage Mountain** — Houston & Bates — katastrofa na K2 1953.
- `REC` **No Picnic on Mount Kenya** — Felice Benuzzi — jeniec ucieka, by wejść na górę, i wraca.
- `REC` **Between a Rock and a Hard Place (127 godzin)** — Aron Ralston — odcina sobie rękę, by przeżyć.
- `REC` **Highest Duty** — Chesley „Sully" Sullenberger — 208 sekund lądowania na Hudson.
- `REC` **Lost Moon (Apollo 13)** — Jim Lovell — 6 dni walki o powrót oczami kapitana.
- `REC` **Carrying the Fire** — Michael Collins — najlepsza autobiografia astronauty.
- `REC` **Adrift / Two Years Before the Mast** — Richard Henry Dana — brutalne życie marynarza XIX w.

## Katastrofy — rekonstrukcje (dziennikarskie / historyczne)
- `REC` **Isaac's Storm** — Erik Larson — huragan w Galveston 1900.
- `REC` **The Perfect Storm (Sztorm doskonały)** — Sebastian Junger — kuter ginie na Atlantyku.
- `REC` **In the Heart of the Sea (W sercu morza)** — Nathaniel Philbrick — Essex staranowany przez wieloryba (Pulitzer).
- `REC` **In Harm's Way** — Doug Stanton — USS Indianapolis, rekiny, 5 dni w wodzie.
- `REC` **A Night to Remember** — Walter Lord — Titanic minuta po minucie z relacji 63 ocalałych.
- `REC` **The Wager** — David Grann — rozbicie okrętu i bunt na bezludnej wyspie.
- `REC` **The Great Halifax Explosion** — John U. Bacon — największa eksplozja przed Hiroszimą (1917).
- `REC` **Dark Tide** — Stephen Puleo — eksplozja zbiornika melasy w Bostonie 1919.
- `REC` **The Johnstown Flood** — David McCullough — pęknięta tama i 2200 ofiar (1889).
- `REC` **Rising Tide** — John M. Barry — wielka powódź Missisipi 1927.
- `REC` **The Great Deluge** — Douglas Brinkley — huragan Katrina, pełna rekonstrukcja.
- `REC` **Zeitoun** — Dave Eggers — Katrina oczami jednego człowieka.
- `REC` **Triangle: The Fire That Changed America** — David von Drehle — pożar fabryki 1911, 146 ofiar.
- `REC` **The Big Burn** / **The Worst Hard Time** — Timothy Egan — pożar lasów 1910 / Dust Bowl.
- `REC` **Young Men and Fire** — Norman Maclean — pożar Mann Gulch, 13 pożarników.
- `REC` **Fire Weather** — John Vaillant — pożar Fort McMurray, klimat i ropa.
- `REC` **Paradise** — Lizzie Johnson — pożar Camp Fire 2018 godzina po godzinie.
- `REC` **Five Past Midnight in Bhopal** — Lapierre & Moro — największa katastrofa przemysłowa (1984).
- `REC` **Command and Control** — Eric Schlosser — arsenał jądrowy USA i niemal-katastrofy.
- `REC` **Atomic Accidents** — James Mahaffey — historia katastrof jądrowych jak antologia thrillerów.
- `REC` **Midnight in Chernobyl** — patrz biblioteka.
- `REC` **Czarnobylska modlitwa (Voices from Chernobyl)** — Swietłana Aleksijewicz — głosy ocalałych (Nobel).
- `REC` **Deep Down Dark** — Héctor Tobar — 33 górników uwięzionych w Chile.
- `REC` **The Terrible Hours** — Peter Maas — ratunek załogi okrętu podwodnego USS Squalus.
- `REC` **Blind Man's Bluff** — Sontag & Drew — tajna wojna podwodna zimnej wojny.
- `REC` **Kursk** — Robert Moore / Peter Truscott — zatonięcie rosyjskiego atomowego okrętu.
- `REC` **The Hindenburg** — Michael M. Mooney — eksplozja sterowca 1937.
- `REC` **Ship of Gold in the Deep Blue Sea** — statek złota zatopiony i odnaleziony.
- `REC` **Krakatoa** / **A Crack in the Edge of the World** — Simon Winchester — wulkan / trzęsienie San Francisco.
- `REC` **The Children's Blizzard** — David Laskin — burza śnieżna 1888, dzieci ze szkół.
- `REC` **Under a Flaming Sky** — Daniel James Brown — pożar Hinckley 1894 (zginął jego pradziadek).
- `REC` **The Boys in the Boat** — Daniel James Brown — wioślarze na igrzyskach 1936.
- `REC` **Unbroken (Niezłomny)** — Laura Hillenbrand — rozbitek i jeniec obozów japońskich.
- `REC` **Seabiscuit** — Laura Hillenbrand — koń wyścigowy w czasie kryzysu.
- `REC` **Erebus** — Michael Palin — statek zaginiony w wyprawie Franklina.
- `REC` **Skeletons on the Zahara** — Dean King — rozbitkowie w saharyjskiej niewoli.
- `REC` **Hiroshima** — John Hersey — sześcioro ocalałych rok po bombie.
- `REC` **The Wreck of the Medusa** — Jonathan Miles — tratwa Meduzy, kanibalizm.

## Pandemie i zarazy
- `REC` **The Great Influenza** — John M. Barry — grypa hiszpanka 1918.
- `REC` **The Hot Zone (Strefa skażenia)** — Richard Preston — Ebola, czyta się jak horror.
- `REC` **Spillover** — David Quammen — choroby przenoszące się ze zwierząt na ludzi.
- `REC` **Pale Rider** — Laura Spinney — hiszpanka w skali globalnej.
- `REC` **The Great Mortality** — patrz biblioteka.
- `REC` **Pox Americana** — Elizabeth Fenn — ospa w czasie amerykańskiej wojny o niepodległość.
- `REC` **The Premonition** — Michael Lewis — COVID i amerykańskie zdrowie publiczne.

## Korea Północna / autorytaryzm — od środka
- `REC` **Passcode to the Third Floor** — Thae Yong-ho — najwyżej rangą dyplomata, który zbiegł.
- `REC` **The Tears of My Soul** — Kim Hyun-hee — agentka, która wysadziła samolot KAL 858.
- `REC` **A Kim Jong-Il Production** — Paul Fischer — reżyser i aktorka porwani przez Kim Jong-ila.
- `REC` **Eyes of the Tailless Animals** — Soon Ok Lee — urzędniczka partii trafia do łagru.
- `REC` **The Invitation-Only Zone** — Robert S. Boynton — Japończycy porywani przez wywiad KRLD.
- `REC` ⭐ **Nothing to Envy** — Barbara Demick — codzienność KRLD oczami sześciorga uciekinierów.
- `REC` **Escape from Camp 14** — Blaine Harden — jedyny znany człowiek urodzony w obozie *(z korektami)*.
- `REC` **In Order to Live** — Yeonmi Park — ucieczka przez Mongolię *(czytać krytycznie)*.
- `REC` **The Aquariums of Pyongyang** — patrz biblioteka.
- `REC` **The Impossible State** — Victor Cha — jak KRLD funkcjonuje jako państwo.
- `REC` **Under the Loving Care of the Fatherly Leader** — Bradley Martin — obszerna biografia dynastii Kimów.

## Polityka / władza / insiderzy
- `REC` **The Room Where It Happened** — John Bolton — z Gabinetu Owalnego Trumpa.
- `REC` **A Higher Loyalty** — James Comey — dyrektor FBI i śledztwo ws. Rosji.
- `REC` **The World As It Is** — Ben Rhodes — 8 lat u boku Obamy.
- `REC` ⭐ **Present at the Creation** — Dean Acheson — jak tworzono powojenny porządek (Pulitzer).
- `REC` **On the Brink** — Henry Paulson — kryzys 2008 od strony Skarbu.
- `REC` **Stress Test** — Timothy Geithner — kryzys 2008 z innej perspektywy.
- `REC` **Against All Enemies** — Richard Clarke — ostrzeżenia przed 11 września.
- `REC` **Duty** — Robert Gates — jedyny sekretarz obrony dwóch prezydentów z różnych partii.
- `REC` **The Gatekeepers** — Chris Whipple — każdy żyjący szef gabinetu Białego Domu.
- `REC` **The Haldeman Diaries** — H.R. Haldeman — codzienny dziennik szefa gabinetu Nixona.
- `REC` **All the President's Men** — Woodward & Bernstein — śledztwo Watergate.
- `REC` **Fear** / **Rage** — Bob Woodward — administracja Trumpa od środka.
- `REC` **A Journey** — Tony Blair — 10 lat premierostwa, przyznaje się do błędów.
- `REC` **The Downing Street Years** / **The Path to Power** — Margaret Thatcher.
- `REC` **Khrushchev Remembers** — Nikita Chruszczow — wspomnienia przemycone na Zachód.
- `REC` ⭐ **The Man Without a Face** — Masha Gessen — najlepsza biografia Putina.
- `REC` ⭐ **Putin's People (Ludzie Putina)** — Catherine Belton — jak KGB przejęło Rosję.
- `REC` **Blowing Up Russia** — Aleksander Litwinienko — teza o zamachach FSB.
- `REC` ⭐ **Red Notice** — Bill Browder — inwestor kontra Kreml.
- `REC` **Long Walk to Freedom** — Nelson Mandela — 27 lat więzienia, prezydentura.
- `REC` **Inside the Third Reich** / **Spandau** — Albert Speer — dwór Hitlera od środka.
- `REC` **Berlin Diary** — William Shirer — korespondent w Berlinie 1934–40.
- `REC` **The Private Life of Chairman Mao** — Li Zhisui — Mao oczami osobistego lekarza.
- `REC` **My Life** — Bill Clinton / **A Promised Land** — Barack Obama — dobre literacko autobiografie prezydentów.
- `REC` **Rok 1989** — M.F. Rakowski / **Alfabet Kiszczaka** — polska transformacja od środka *(czytać krytycznie)*.

## Wywiad / służby / szpiegostwo (non-fiction)
- `REC` **Argo** / **The Master of Disguise** — Antonio Méndez — mistrz przebrań CIA, ewakuacja z Teheranu.
- `REC` **A Look Over My Shoulder** — Richard Helms — jedyna autobiografia dyrektora CIA.
- `REC` **First In** / **Jawbreaker** — Schroen / Berntsen — CIA w Afganistanie po 11 września.
- `REC` **My Silent War** — Kim Philby — autobiografia zdrajcy bez żalu.
- `REC` ⭐ **The Spy and the Traitor** — Ben Macintyre — Oleg Gordiewski, agent MI6 w KGB.
- `REC` **A Spy Among Friends** — patrz biblioteka.
- `REC` **Spy Catcher** — Peter Wright — MI5 od środka.
- `REC` **The Sword and the Shield** — Andrew & Mitrokhin — największy wyciek z KGB.
- `REC` **Aquarium** / **Inside the Soviet Army** — Wiktor Suworow — dezerter GRU.
- `REC` **Gideon's Spies** / **Every Spy a Prince** — historia Mossadu.
- `REC` **The Angel** — Uri Bar-Joseph — zięć Nassera jako szpieg Mossadu.
- `REC` **Permanent Record** — Edward Snowden — system inwigilacji od środka.
- `REC` **No Place to Hide** — Glenn Greenwald — publikacja dokumentów Snowdena.
- `REC` **The Looming Tower** — Lawrence Wright — Al-Kaida do 11 września (Pulitzer).
- `REC` **Ghost Wars** / **Directorate S** — Steve Coll — CIA w Afganistanie i Pakistanie.
- `REC` **Black Hawk Down** — Mark Bowden — bitwa w Mogadiszu minuta po minucie.
- `REC` ⭐ **Sandworm** — Andy Greenberg — rosyjskie cyberataki (domyka Twój Dark Territory).
- `REC` **This Is How They Tell Me the World Ends** — Nicole Perlroth — rynek cyberbroni.
- `REC` **The Back Channel** — patrz biblioteka.
- `REC` **Our Man** — George Packer — biografia dyplomaty Richarda Holbrooke'a.

## 0,01% — bogactwo / dynastie / oligarchowie / Wall Street
- `REC` **The Medici** — Paul Strathern — bankierska rodzina renesansu.
- `REC` **The House of Morgan** / ⭐ **Titan (Rockefeller)** — Ron Chernow — dynastie finansowe (Pulitzer).
- `REC` **The Patriarch** — David Nasaw — Joseph P. Kennedy, ojciec klanu.
- `REC` **The Romanovs** — Simon Sebag Montefiore — 300 lat carskiej dynastii.
- `REC` **Nazi Billionaires** — David de Jong — Porsche, Quandt, Flick i praca niewolnicza III Rzeszy.
- `REC` **Sam Walton: Made in America** — autobiografia twórcy Walmartu.
- `REC` **Elon Musk** — patrz biblioteka.
- `REC` **The Everything Store** / **Amazon Unbound** — Brad Stone — Bezos i Amazon.
- `REC` **No Filter** — Sarah Frier — Instagram i przejęcie przez Zuckerberga.
- `REC` **Super Pumped** — Mike Isaac — Kalanick i Uber.
- `REC` **Chaos Monkeys** — A.G. Martínez — Dolina Krzemowa od środka.
- `REC` ⭐ **Moneyland** / **Butler to the World** — Oliver Bullough — globalna kleptokracja i pranie pieniędzy.
- `REC` **Sale of the Century** — Chrystia Freeland — narodziny rosyjskiej oligarchii.
- `REC` **Londongrad** / **Kleptopia** — jak oligarchowie skolonizowali Londyn.
- `REC` **Den of Thieves** — James B. Stewart — insider trading lat 80. (Pulitzer).
- `REC` **When Genius Failed** — Roger Lowenstein — upadek funduszu LTCM.
- `REC` **More Money Than God** — Sebastian Mallaby — historia funduszy hedgingowych.
- `REC` **The Fund** — Rob Copeland — Ray Dalio i Bridgewater jako kult.
- `REC` **Black Edge** — Sheelah Kolhatkar — Steve Cohen i SAC Capital.
- `REC` **Liar's Poker** / **The Big Short** / **Flash Boys** / **The Undoing Project** — Michael Lewis — Wall Street i decyzje.
- `REC` **Winners Take All** — Anand Giridharadas — filantropia miliarderów jako zasłona.
- `REC` **Davos Man** — Peter Goodman — ludzie stojący za nierównościami.
- `REC` **Dark Money** — Jane Mayer — bracia Koch i pieniądze w polityce.
- `REC` **Richistan** — Robert Frank — reportaż wśród nowo bogatych.
- `REC` **The Millionaire Next Door** — Thomas Stanley — prawdziwi milionerzy żyją skromnie.
- `REC` **The First Tycoon** — T.J. Stiles — Cornelius Vanderbilt (Pulitzer).

## Historia / geopolityka / wojna
- `REC` ⭐ **Sapiens** — Yuval Noah Harari — historia Homo sapiens od sawanny po Dolinę Krzemową.
- `REC` **Stalingrad** / **Berlin 1945** / **D-Day** — Antony Beevor — mistrz historii wojennej.
- `REC` ⭐ **Skrwawione ziemie (Bloodlands)** — Timothy Snyder — co działo się między Berlinem a Moskwą.
- `REC` **O tyranii** — Timothy Snyder — 20 lekcji z XX wieku, 130 stron.
- `REC` ⭐ **Postwar** — Tony Judt — historia Europy 1945–2005.
- `REC` **The Guns of August** / **A Distant Mirror** — Barbara Tuchman — I wojna / XIV wiek (Pulitzer).
- `REC` **Hitler** — Ian Kershaw — najlepsza biografia dwutomowa.
- `REC` **Stalin: dwór czerwonego cara** / **Młody Stalin** / **Jerozolima** — Simon Sebag Montefiore.
- `REC` **The Best and the Brightest** — David Halberstam — jak najmądrzejsi wciągnęli USA w Wietnam.
- `REC` **Dispatches** — Michael Herr — halucynacyjny reportaż z Wietnamu.
- `REC` **The Things They Carried** — Tim O'Brien — Wietnam, hybryda fikcji i faktu.
- `REC` **A Bright Shining Lie** — Neil Sheehan — Wietnam przez jednego oficera (Pulitzer).
- `REC` **Why Nations Fail** — Acemoglu & Robinson — dlaczego kraje są bogate lub biedne.
- `REC` **The Rape of Nanking** — Iris Chang — mało znane ludobójstwo 1937.
- `REC` **Wild Swans** — Jung Chang — Chiny XX w. przez trzy pokolenia kobiet.
- `REC` **Świat z drugiej ręki** / **Wojna nie ma w sobie nic z kobiety** / **Cynkowi chłopcy** — Swietłana Aleksijewicz (Nobel).
- `REC` **The Sixth Extinction** / **Under a White Sky** — Elizabeth Kolbert — wymierania i geoinżynieria (Pulitzer).

## Nauka / medycyna / mózg / natura
- `REC` **The Emperor of All Maladies** / **The Song of the Cell** — Siddhartha Mukherjee — rak / komórka (Pulitzer).
- `REC` ⭐ **An Immense World** — Ed Yong — jak zwierzęta odbierają świat.
- `REC` **I Contain Multitudes** — Ed Yong — mikrobiom.
- `REC` **The Immortal Life of Henrietta Lacks** — Rebecca Skloot — komórki HeLa i etyka.
- `REC` **Stiff** / **Spook** / **Packing for Mars** / **Gulp** — Mary Roach — nauka o ciele, śmierci, kosmosie, jedzeniu.
- `REC` **Fermat's Last Theorem** / **The Code Book** — Simon Singh — matematyka jak thriller / historia szyfrów.
- `REC` **Surely You're Joking, Mr. Feynman!** — Richard Feynman — anegdoty fizyka noblisty.
- `REC` **American Prometheus** — Bird & Sherwin — biografia Oppenheimera (Pulitzer, podstawa filmu).
- `REC` **Silent Spring** — Rachel Carson — książka, która zapoczątkowała ekologię.
- `REC` **The Body Keeps the Score (Strach ucieleśniony)** — Bessel van der Kolk — trauma jest w ciele.

## Biznes / ekonomia / finanse / technologia
- `REC` **The Psychology of Money** — Morgan Housel — dlaczego podejmujemy irracjonalne decyzje finansowe.
- `REC` **Chip War** — Chris Miller — półprzewodniki i geopolityka.
- `REC` **Going Infinite** — Michael Lewis — Sam Bankman-Fried i FTX *(autor za bardzo lubi SBF)*.
- `REC` **The Cult of We** — Brown & Farrell — WeWork.
- `REC` **Flying Blind** — Peter Robison — Boeing 737 MAX.
- `REC` **Too Big to Fail** — Andrew Ross Sorkin — krach 2008 dzień po dniu.
- `REC` **Bottle of Lies** — Katherine Eban — fałszowane generyki farmaceutyczne.
- `REC` **Empire of Pain** — patrz biblioteka.

## Psychologia / rozwój / stoicyzm / terapia schematów
- `REC` ⭐ **Człowiek w poszukiwaniu sensu** — Viktor Frankl — 120 stron o wolności wyboru postawy.
- `REC` ⭐ **Thinking, Fast and Slow (Pułapki myślenia)** — Daniel Kahneman — jak mózg nas oszukuje.
- `REC` ⭐ **Influence (Wywieranie wpływu)** — Robert Cialdini — sześć zasad perswazji.
- `REC` **Atomic Habits (Atomowe nawyki)** — James Clear — najpraktyczniejsza o zmianie siebie.
- `REC` ⭐ **Medytacje** — Marek Aureliusz — notatki cesarza, najlepszy podręcznik życia.
- `REC` **A Guide to the Good Life** — William Irvine — najlepsze wprowadzenie do stoicyzmu.
- `REC` **Quiet (Ciszej, proszę)** — Susan Cain — siła introwertyków.
- `REC` **Mistakes Were Made (But Not by Me)** — Tavris & Aronson — psychologia samousprawiedliwiania.
- `REC` **Reinventing Your Life (Program zmian)** — Jeffrey Young & Janet Klosko — klasyk terapii schematów.
- `REC` **Emocjonalne pułapki przeszłości** — Jacob, van Genderen, Seebauer — najdostępniejsza po polsku, z ćwiczeniami.
- *(uwaga: książki o terapii schematów nie zastępują pracy z terapeutą)*

## Reportaż / podróże / społeczeństwo
- `REC` **Evicted** / **Poverty, by America** — Matthew Desmond — eksmisje i bieda w USA (Pulitzer).
- `REC` **Nickel and Dimed** — Barbara Ehrenreich — dziennikarka udaje minimalniarkę.
- `REC` **Random Family** — Adrian Nicole LeBlanc — 11 lat w życiu rodziny z Bronxu.
- `REC` **Behind the Beautiful Forevers** — Katherine Boo — slumsy Mumbaju.
- `REC` **Maximum City** — Suketu Mehta — Bombaj jako miasto.
- `REC` **The New Jim Crow** — Michelle Alexander — system karny jako nowa segregacja.
- `REC` **Just Mercy** — Bryan Stevenson — obrona niesłusznie skazanych na śmierć.
- `REC` **The Warmth of Other Suns** — Isabel Wilkerson — wielka migracja czarnych Amerykanów.
- `REC` **Born to Run** — Christopher McDougall — plemię biegaczy Tarahumara.
- `REC` **A Walk in the Woods** / **Notes from a Small Island** — Bill Bryson — komedia podróżnicza.
- `REC` **The Snow Leopard** — Peter Matthiessen — Himalaje, żałoba, buddyzm.
- `REC` **In Patagonia** / **The Songlines** — Bruce Chatwin — nowe pisarstwo podróżnicze.
- `REC` **Reading Lolita in Tehran** — Azar Nafisi — tajne czytanie zachodnich powieści w Iranie.
- `REC` **Nothing to Envy** — patrz Korea.
- `REC` **Between the World and Me** — Ta-Nehisi Coates — list ojca do syna o byciu czarnym w USA.
- `REC` **The Year of Magical Thinking** / **The White Album** — Joan Didion — żałoba / eseje o Kalifornii.
- `REC` **Crying in H Mart** — Michelle Zauner — śmierć matki i jedzenie jako pamięć.
- `REC` **Stay True** — Hua Hsu — przyjaźń z college'u i strata (Pulitzer).

## Polski reportaż
- `REC` ⭐ **Heban** — Ryszard Kapuściński — 40 lat reportażu z Afryki.
- `REC` ⭐ **Inny świat** — Gustaw Herling-Grudziński — sowiecki łagier 1940–42.
- `REC` ⭐ **Jak nakarmić dyktatora** — Witold Szabłowski — osobiści kucharze dyktatorów.
- `REC` **Zdążyć przed Panem Bogiem** — Hanna Krall — rozmowa z Markiem Edelmanem.
- `REC` **Gottland** — Mariusz Szczygieł — czeskie historie XX wieku.
- `REC` **Miedzianka** — Filip Springer — historia znikającego miasta.
- `REC` **Ucieczka z Sobiboru** — Tomasz Blatt — świadectwo ocalałego z buntu.
- `REC` **Dzienniki Kołymskie** — patrz biblioteka.
- `REC` **Rozmowy z katem** — patrz biblioteka.

## Memuary / biografie / autobiografie
- `REC` **Kiedy oddech staje się powietrzem (When Breath Becomes Air)** — Paul Kalanithi — neurochirurg z rakiem płuc.
- `REC` **Educated (Uwolniona)** — patrz biblioteka.
- `REC` **The Glass Castle (Zamek ze szkła)** — Jeannette Walls — dzieciństwo w skrajnej biedzie.
- `REC` **Angela's Ashes** / **'Tis** — Frank McCourt — irlandzkie dzieciństwo (Pulitzer).
- `REC` **This Boy's Life** — Tobias Wolff — chłopiec z toksycznym ojczymem.
- `REC` **The Liars' Club** — Mary Karr — teksańskie dzieciństwo, klasyk memuaru.
- `REC` **Running with Scissors** — Augusten Burroughs — czarna komedia autobiograficzna.
- `REC` **I Know Why the Caged Bird Sings** — Maya Angelou — dziewczyna w segregacyjnym Arkansas.
- `REC` **The Autobiography of Malcolm X** — Malcolm X & Alex Haley.
- `REC` **Speak, Memory** — Vladimir Nabokov — literacka autobiografia.
- `REC` **The Diving Bell and the Butterfly** — Jean-Dominique Bauby — napisana mrugnięciami oka.
- `REC` **If This Is a Man** / **The Periodic Table** / **The Drowned and the Saved** — Primo Levi — Auschwitz językiem chemika.
- `REC` **Down and Out in Paris and London** / **Homage to Catalonia** / **The Road to Wigan Pier** — George Orwell.
- `REC` **Surely You're Joking** — patrz nauka.
- `REC` **The Autobiography of Andrew Carnegie** / **Benjamin Franklin** — samodzielne autobiografie potentatów.
- `REC` **Tuesdays with Morrie** / **The Last Lecture** — Albom / Pausch — lekcje życia od umierających.

## O pisaniu i kreatywności
- `REC` **On Writing** — Stephen King — pół autobiografii, pół podręcznik rzemiosła.
- `REC` **Bird by Bird** — Anne Lamott — o pisaniu od strony psychologicznej.
- `REC` **The War of Art** — Steven Pressfield — o wewnętrznym oporze przed tworzeniem.
- `REC` **The Elements of Style** — Strunk & White — 100 stron o dobrym pisaniu.
- `REC` **Letters to a Young Poet** — Rainer Maria Rilke — o samotności, miłości, sensie.

---

## Top „na już" (moje najmocniejsze typy pod Twój gust)
1. ⭐ **Dotknięcie pustki** — Joe Simpson *(po Evereście i K2)*
2. ⭐ **Pantera** — Jo Nesbø *(dokończ Harry'ego Hole)*
3. ⭐ **Rain Fall / John Rain** — Barry Eisler *(po Victorze)*
4. ⭐ **Hipnotyzer** — Lars Kepler *(najbliżej Bałwana)*
5. ⭐ **Bastion** — Stephen King *(Twój Forstchen + klaster zarazy)*
6. ⭐ **Sandworm** — Andy Greenberg *(domyka Dark Territory)*
7. ⭐ **Modyfikowany węgiel** — Richard K. Morgan *(most thriller↔SF)*
8. ⭐ **Departament Q** — Jussi Adler-Olsen *(seria na długie miesiące)*
9. ⭐ **Poświęcenie podejrzanego X** — Keigo Higashino *(arcydzieło konstrukcji)*
10. ⭐ **Jak nakarmić dyktatora** — Witold Szabłowski *(polski + władza absolutna)*

*Uwaga o kompletności: liczby tomów dla serii w toku (Gray Man, Victor, Orphan X, Robert Hunter) wg list wydawniczych z poł. 2026. Kilka pozycji pojawiało się w kilku listach — zostały scalone. Statusy „READ/READING/QUEUE" pochodzą z eksportu Twojej biblioteki Kindle.*
