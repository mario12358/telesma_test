# telesma/state/QUESTIONS.md - Project clarification

## Status

- **State**: done
- **Total questions**: 5
- **Answered**: 5
- **Assumptions**: 20
- **Contradictions**: 1
- **Generated on**: 2026-10-22

## Analyzed documents

- telesma/spec/TECHNICAL_GUIDELINES.md (30 linii)
- telesma/spec/lista-lektur.md (135 linii)
- telesma/spec/ux_ui/ — katalog pusty (brak makiet)

## Contradictions in the documentation

### S1: Ocena dozwolona tylko przy statusie `przeczytana` vs wstępna ocena w statusie `czytam`
- **Source A**: lista-lektur.md:31, 38, 120-121 — pole `ocena`: „dozwolona wyłącznie gdy status = `przeczytana`”; R2: „zmiana statusu na inny niż `przeczytana` kasuje ocenę”; A2: „ocenę da się zapisać tylko w sytuacjach dozwolonych przez model (3.1)”
- **Source B**: lista-lektur.md:103-104 — ekran „Szczegóły”: „Użytkownik może wystawić wstępną ocenę już w statusie `czytam`; po zmianie statusu na `przeczytana` ocena zostaje.”
- **Proposed resolution**: Model (3.1 + R2 + A2) jest nadrzędny — trzy miejsca vs jedno, a kryterium A2 wprost odsyła do 3.1. Ocena dozwolona wyłącznie przy `przeczytana`; na ekranie „Szczegóły” gwiazdki są nieaktywne przy innym statusie, z podpowiedzią „Ocenę można wystawić po przeczytaniu”. Alternatywa (jeśli intencją jest wstępna ocena): ocena dozwolona przy `czytam` i `przeczytana`, R2 kasuje ją tylko przy zmianie na `do przeczytania` — wtedy trzeba poprawić 3.1, R2 i A2.
- **Resolution**: Alternatywa
- **Status**: ✅

## Assumptions

### A1: Układ repozytorium: pakiet `app/` (main, db, models, schemas, services, routers, templates, static), katalog `alembic/`, `tests/`, `requirements.txt` i `requirements-dev.txt`
- **Category**: architecture
- **Source**: TECHNICAL_GUIDELINES.md:5-10, 29 | stack convention
- **Rationale**: Standardowy układ FastAPI dla małej aplikacji; oddzielny plik dev-deps trzyma pytest, Playwright i ruff poza zależnościami produkcyjnymi. Wersje w `requirements*.txt` przypięte (`==`), co pełni rolę lockfile.
- **Status**: ✅

### A2: Jedna komenda startu to `uvicorn app.main:app --port 8000`; migracje Alembic uruchamiane automatycznie w lifespan aplikacji (`alembic upgrade head`), co tworzy `data/lektury.db` przy starcie
- **Category**: architecture
- **Source**: TECHNICAL_GUIDELINES.md:8-9, 15, 29
- **Rationale**: Spec wymaga zarówno Alembica, jak i tworzenia bazy „przy starcie” po jednej komendzie — automatyczne `upgrade head` godzi oba wymagania bez dodatkowego kroku dla użytkownika. Katalog `data/` tworzony, gdy go nie ma.
- **Status**: ✅

### A3: Ścieżka bazy ze zmiennej `LEKTURY_DB_PATH` z domyślną wartością `data/lektury.db`; testy używają tymczasowego pliku SQLite per test, `PRAGMA foreign_keys=ON` włączone na każdym połączeniu
- **Category**: technology
- **Source**: TECHNICAL_GUIDELINES.md:8, 18 | stack convention
- **Rationale**: SQLite domyślnie nie egzekwuje kluczy obcych — bez PRAGMA kaskada z R3 nie zadziała na poziomie bazy. Plik tymczasowy w testach izoluje przypadki i omija ograniczenia `:memory:` przy wielu połączeniach.
- **Status**: ✅

### A4: Relacja książka–półka przez tabelę łączącą `book_shelves` (book_id, shelf_id, PK złożony); R3 egzekwowane kaskadą `ON DELETE CASCADE` na notatkach i tabeli łączącej, dodatkowo w warstwie serwisu
- **Category**: architecture
- **Source**: lista-lektur.md:15-16, 39 | stack convention
- **Rationale**: Klasyczne M:N; kaskada w bazie zabezpiecza spójność także przy operacjach poza serwisem.
- **Status**: ✅

### A5: Normalizacja z R1 i unikalność nazwy półki realizowane przez kolumny `title_norm`, `author_norm`, `name_norm` (casefold, przycięcie, pojedyncze spacje) z unikalnymi indeksami; duplikat zwraca `422` z komunikatem przy polu `title` (książka) lub `name` (półka)
- **Category**: requirements
- **Source**: lista-lektur.md:36-37, 46, 65-66
- **Rationale**: Spec definiuje tylko kody 422 i 404; duplikat to błąd walidacji „z czytelnym komunikatem”, więc 422 jest spójne z resztą API. Indeks unikalny chroni przed wyścigiem.
- **Status**: ✅

### A6: Kolejność alfabetyczna półek (R5): `ORDER BY name COLLATE NOCASE` — bez wielkości liter, polskie znaki według kodów Unicode (ą po z)
- **Category**: requirements
- **Source**: lista-lektur.md:49 | stack convention
- **Rationale**: SQLite nie ma wbudowanej polskiej kolacji; pełne sortowanie lokalizowane wymagałoby ICU albo sortowania po stronie Pythona. Dla kilku–kilkunastu półek różnica jest pomijalna.
- **Status**: ✅

### A7: Klucze JSON w API po angielsku: `id, title, author, year, status, rating, created_at, updated_at, shelves, notes` (notatka: `id, book_id, content, created_at`; półka: `id, name, book_count`); daty jako ISO 8601 w UTC z sufiksem `Z`
- **Category**: technology
- **Source**: TECHNICAL_GUIDELINES.md:23 | lista-lektur.md:24-32
- **Rationale**: „Kod i komentarze po angielsku” obejmuje kontrakt API; polskie nazwy pól ze spec są etykietami UI.
- **Status**: ✅

### A8: `PATCH /api/books/{id}` to aktualizacja częściowa: pola nieobecne bez zmian, `null` czyści `year`/`rating`; podanie `rating` przy statusie innym niż dozwolony zwraca `422`; R2 stosowane po stronie serwera także gdy w tym samym żądaniu przychodzi nowy status
- **Category**: requirements
- **Source**: lista-lektur.md:31, 38, 73
- **Rationale**: Standardowa semantyka PATCH; reguła modelu musi być egzekwowana w serwisie, nie w UI, bo A2 wymaga odrzucenia przez API.
- **Status**: ✅

### A9: `PUT /api/books/{id}/shelves` przyjmuje `{"shelf_ids": [int, ...]}` i zastępuje całą listę; nieistniejące id półki zwraca `422` przy polu `shelf_ids`; usunięcie półki tylko odpina ją od książek, książki zostają
- **Category**: requirements
- **Source**: lista-lektur.md:77-78 | none — zachowanie przy nieznanym id nie jest opisane
- **Rationale**: 404 zarezerwowane dla zasobu ze ścieżki (książka); błędne id w ciele to błąd walidacji. Spec nie mówi, że usunięcie półki ma kasować książki, a R3 opisuje tylko kierunek odwrotny.
- **Status**: ✅

### A10: Eksport CSV: separator kolumn przecinek, półki w jednej kolumnie rozdzielone `;`, kodowanie UTF-8 z BOM, nagłówek po polsku (`tytuł,autor,rok,status,ocena,półki`), nagłówek `Content-Disposition: attachment; filename="lektury.csv"`
- **Category**: requirements
- **Source**: lista-lektur.md:81, 125-126
- **Rationale**: Spec rezerwuje `;` na rozdzielanie półek, więc separatorem kolumn musi być przecinek; BOM sprawia, że Excel i Numbers poprawnie rozpoznają UTF-8 i polskie znaki (A6).
- **Status**: ✅

### A11: `GET /api/stats` zwraca `{"to_read": n, "reading": n, "read": n, "average_rating": x|null}`; średnia liczona tylko z książek ze statusem `przeczytana` i oceną, zaokrąglona do 0,1, `null` gdy brak ocen
- **Category**: requirements
- **Source**: lista-lektur.md:82 | none — przypadek braku ocen nie jest opisany
- **Rationale**: `null` jest jednoznaczny; 0,0 sugerowałoby realną ocenę. Klucze statusów zależą od odpowiedzi na Q1.
- **Status**: ✅

### A12: Widoki HTML pod `/` (Lista) i `/books/{id}` (Szczegóły); fragmenty HTMX serwowane przez te same routery widoków (rozpoznanie nagłówka `HX-Request`), nie przez `/api`; widoki i `/api` korzystają ze wspólnej warstwy serwisów
- **Category**: architecture
- **Source**: TECHNICAL_GUIDELINES.md:6-7 | lista-lektur.md:66, 86-87
- **Rationale**: HTMX wymienia fragmenty HTML, a `/api` zwraca JSON — potrzebne są dwa zestawy endpointów nad jedną logiką, inaczej reguły R1–R3 rozjadą się między API a UI (A1, A3 wymagają zgodności).
- **Status**: ✅

### A13: Daty w UI w formacie dd.MM.yyyy w lokalnej strefie czasowej komputera użytkownika (konwersja z UTC po stronie serwera); czas dodania notatki także z godziną HH:mm
- **Category**: requirements
- **Source**: TECHNICAL_GUIDELINES.md:23 | lista-lektur.md:32, 58
- **Rationale**: Aplikacja działa lokalnie, więc strefa serwera = strefa użytkownika; sama data bez godziny nie rozróżnia kilku notatek z jednego dnia.
- **Status**: ✅

### A14: Bez JavaScriptu każda operacja działa jako zwykły formularz POST z przekierowaniem (wzorzec PRG); usunięcie bez JS przez osobną stronę potwierdzenia, z JS przez `hx-confirm`; szukanie bez JS wymaga przycisku „Szukaj”, z JS działa w trakcie pisania (`hx-trigger="keyup changed delay:300ms"`)
- **Category**: architecture
- **Source**: lista-lektur.md:91-92, 108, 112
- **Rationale**: Taka jest standardowa interpretacja „progressive enhancement” w HTMX; metody DELETE/PATCH nie istnieją w formularzach HTML, więc fallback musi używać POST.
- **Status**: ✅

### A15: Lista: tabela na ekranach ≥ 640 px, ta sama treść jako karty w jednej kolumnie poniżej 640 px (CSS, bez duplikowania szablonu); ocena na liście tylko do odczytu, zmiana statusu przez przyciski/select w wierszu
- **Category**: requirements
- **Source**: lista-lektur.md:93, 96, 113
- **Rationale**: Spec dopuszcza „tabelę lub listę kart”; jeden szablon z responsywnym CSS spełnia oba warianty. Ocenę zmienia się na ekranie „Szczegóły” (5.2).
- **Status**: ✅

### A16: Statystyki wyświetlane w nagłówku wspólnego layoutu (oba ekrany) i odświeżane po każdej operacji przez HTMX out-of-band swap
- **Category**: requirements
- **Source**: lista-lektur.md:98, 127
- **Rationale**: A7 wymaga zgodności „po każdej operacji”, także tych wykonywanych na ekranie „Szczegóły” — wspólny nagłówek jest najprostszym sposobem.
- **Status**: ✅

### A17: Własny, krótki plik CSS bez frameworka; HTMX w `app/static/htmx.min.js` przypięty do konkretnej wersji; brak innych zależności frontendowych
- **Category**: technology
- **Source**: TECHNICAL_GUIDELINES.md:7, 30
- **Rationale**: Zero npm i jeden plik statyczny HTMX wprost ze spec; dwa ekrany nie uzasadniają frameworka CSS.
- **Status**: ✅

### A18: Komunikaty walidacji (w API `422` i w UI przy polu) po polsku; format błędu 422 to `{"detail": [{"field": "title", "message": "..."}]}`
- **Category**: requirements
- **Source**: lista-lektur.md:65-66, 114 | TECHNICAL_GUIDELINES.md:23
- **Rationale**: Spec wymaga „listy pól i komunikatów”; ujednolicony format pozwala tym samym komunikatom trafić do szablonów przy polu.
- **Status**: ✅

### A19: Testy: pytest + `TestClient` (httpx) dla API i widoków, każdy test na świeżej bazie; e2e Playwright (Python) uruchamia `uvicorn` w fixture na wolnym porcie z osobnym plikiem bazy; wyniki w formacie JUnit dla CI i Specky
- **Category**: technology
- **Source**: TECHNICAL_GUIDELINES.md:10, 17 | lista-lektur.md:128-129
- **Rationale**: A8 wymaga pokrycia R1–R7, każdego endpointu i e2e przez oba ekrany; JUnit jest wymagany przez integrację Specky (dowody kryteriów).
- **Status**: ✅

### A20: Plan w trzech fazach zgodnie z sekcją 7 spec; po fazie 3 tag `v0.1.0`; istniejący `.github/workflows/specky-ci.yml` dostosowany do Pythona (pip, ruff, pytest z JUnit, Playwright) w pierwszym zadaniu
- **Category**: priorities
- **Source**: lista-lektur.md:131-135 | TECHNICAL_GUIDELINES.md:17
- **Rationale**: Sugerowana kolejność prac jest spójna z zależnościami między modułami; wydanie `v0.1.0` jest wprost wymienione.
- **Status**: ✅

## Questions

### Q1: Jak reprezentować wartości statusu w bazie i w API — kody angielskie czy dosłownie polskie wartości ze spec?
- **Category**: technology
- **Source**: lista-lektur.md:18, 30, 70 | TECHNICAL_GUIDELINES.md:23
- **Proposed answer**: Kody angielskie `to_read`, `reading`, `read` w bazie, w JSON (`status`) i w filtrze `?status=`; w UI i w kolumnie `status` eksportu CSV polskie etykiety (`do przeczytania`, `czytam`, `przeczytana`) przez jedną mapę w kodzie. Uzasadnienie: „kod po angielsku” z wytycznych; wartości ze spec traktujemy jak etykiety. Alternatywa: polskie wartości wszędzie, 1:1 ze spec — prostsze w testach odbiorczych, ale mieszają język w kodzie.
- **Answer**: 
- **Status**: ✅

### Q2: Gdzie w UI zarządzać półkami (dodanie, usunięcie) i gdzie umieścić link do eksportu CSV — spec opisuje te operacje tylko w API?
- **Category**: requirements
- **Source**: lista-lektur.md:75-77, 81, 123, 125 | none — ekrany 5.1 i 5.2 nie wspominają o zarządzaniu półkami ani o eksporcie
- **Proposed answer**: Bez trzeciego ekranu. Na ekranie „Lista” obok listy rozwijanej półek sekcja „Półki” rozwijana przyciskiem: formularz dodania (nazwa) i lista półek z licznikiem i przyciskiem usunięcia (z potwierdzeniem). Link „Eksport CSV” w nagłówku obok statystyk. Uzasadnienie: spec mówi o „dwóch ekranach”, a A4 wymaga dodawania i usuwania półek — najmniejsza zmiana zakresu.
- **Answer**: 
- **Status**: ✅

### Q3: Jak ma działać „edycja w miejscu” na ekranie „Szczegóły” — zapis każdego pola osobno po zmianie czy jeden formularz z przyciskiem „Zapisz”?
- **Category**: requirements
- **Source**: lista-lektur.md:102-105
- **Proposed answer**: Zapis per pole: każde pole (tytuł, autor, rok, status, ocena) wysyła PATCH po zmianie (`hx-trigger="change"`) i podmienia swój fragment z komunikatem błędu przy polu; spójne z półkami, które „zapisują od razu” (5.2). Bez JS: jeden formularz z przyciskiem „Zapisz” obejmujący wszystkie pola. Alternatywa: zawsze jeden przycisk „Zapisz” — prostsza walidacja krzyżowa statusu i oceny.
- **Answer**: 
- **Status**: ✅

### Q4: Czy testy e2e Playwright mają biec w GitHub Actions i na jakich przeglądarkach?
- **Category**: constraints
- **Source**: TECHNICAL_GUIDELINES.md:10, 17, 24 | lista-lektur.md:128-129
- **Proposed answer**: Tak, w CI na Chromium (osobny job po testach jednostkowych, `playwright install --with-deps chromium`); WebKit dostępny lokalnie przez `pytest --browser webkit`, poza CI. Uzasadnienie: A8 traktuje e2e jako kryterium akceptacji, więc powinno być weryfikowane automatycznie; WebKit w CI wydłuża przebieg i bywa niestabilny na Linuksie, a wsparcie Safari jest deklarowane, nie krytyczne.
- **Answer**: 
- **Status**: ✅

### Q5: Czy wymagania projektu istnieją już w Specky (projekt `01M5JM100G4WW7SR1HV5PKW6C6`), czy Telesma ma je zaproponować z tej specyfikacji przed ułożeniem planu?
- **Category**: constraints
- **Source**: none — config.md wskazuje tracker Specky, spec nie wspomina o nim
- **Proposed answer**: Jeśli projekt w Specky jest pusty, Telesma proponuje wymagania (`propose_requirements`) 1:1 z sekcji 3–6 spec — jedno wymaganie na regułę R1–R7, endpoint lub ekran, z kryteriami akceptacji wyprowadzonymi z A1–A8 — a użytkownik akceptuje je w Specky przed generowaniem PLAN.md, aby zadania od razu miały kotwice `(req: …)`. Jeśli wymagania już istnieją, plan korzysta z nich bez proponowania nowych.
- **Answer**: 
- **Status**: ✅
