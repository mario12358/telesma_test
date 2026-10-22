# telesma/state/PLAN.md - Project task list

## Project information

- **Name**: Lista lektur
- **Stack**: Python 3.12, FastAPI, HTMX + Jinja2 (SSR, bez npm), SQLite (`data/lektury.db`, `LEKTURY_DB_PATH`), SQLAlchemy 2.x + Alembic, pytest + httpx TestClient, Playwright (Python) e2e, ruff, GitHub Actions, uvicorn :8000
- **Decisions from clarification**: S1 → ocena dozwolona przy `reading` i `read`, zmiana na `to_read` kasuje ocenę; Q1 → kody statusu `to_read/reading/read` w DB+API, etykiety PL w UI i CSV; Q2 → sekcja „Półki” na ekranie Lista + link „Eksport CSV” w nagłówku; Q3 → zapis per pole (HTMX), bez JS jeden formularz „Zapisz”; Q4 → e2e w CI na Chromium; Q5 → 20 wymagań w Specky zaakceptowanych 2026-10-22 (wsad `01M5JN7RQ5DQ3XEW1MB4N1V5V4`), kotwice pod zadaniami, mapa w telesma/state/SPECKY.md

## Tasks

<!-- A task line is ≤ 400 characters (the telesma.sh validator warns above that). The plan says  -->
<!-- WHAT is to be done; rationale, findings from the work and the "why this way" go to             -->
<!-- telesma/state/REPORT.md (Problem log) or telesma/state/PROJECT_CONTEXT.md (Key decisions).                      -->
<!-- Every `- [ ]` item MUST start with the word `Task` or `Test`.                                   -->

### Phase 1: Szkielet, baza, API książek, CI

- [x] Task 1.1: Architecture skeleton and conventions — mapa modułów `app/`, przypięte `requirements*.txt`, ruff w `pyproject.toml`, format błędu 422, mapa statusów EN↔PL, adaptacja `specky-ci.yml` do Pythona; wynik do PROJECT_CONTEXT.md (spec: TECHNICAL_GUIDELINES.md) (tech: python, fastapi, github-actions)
  - AC: moduły `app/`: main, config, db, models, schemas, services, routers/api, routers/views, templates, static (A1)
  - AC: po `pip install -r requirements.txt` komenda `uvicorn app.main:app --port 8000` uruchamia aplikację (TG:15, 29)
  - AC: zero zależności npm; `app/static/htmx.min.js` jako jeden plik w przypiętej wersji (TG:30)
  - AC: błędy walidacji API w formacie `{"detail": [{"field", "message"}]}`, brak zasobu `404` (A18)
  - AC: job `test` w CI: setup-python 3.12, pip, `ruff check .`, `pytest --junitxml=reports/junit.xml` z `continue-on-error`, artefakt `junit-reports`, job czerwony przy failu
  - Specky: (req: 01M5JNJBDG93QNHV5379HRXF17 v1 @fc4136e)
  - Specky: (req: 01M5JNJCXSEXSVD5D2NSP50PR6 v1 @8d7b3a8)
  - Specky: (req: 01M5JNJCTA42TVEMS952S2K1H9 v1 @cf83d75)
  - Specky criteria: (crit: 01M5JNJBEG18125FHAA7RP42K4) (crit: 01M5JNJCTX1C3MCC3C32KJQP5W)
- [x] Test: 1.1 — aplikacja startuje, `GET /` zwraca 200 (placeholder), `ruff check .` przechodzi; handler 422 zwraca ustalony format
- [x] Task 1.2: Warstwa bazy — engine SQLAlchemy z `LEKTURY_DB_PATH` (domyślnie `data/lektury.db`, katalog tworzony), `PRAGMA foreign_keys=ON` na każdym połączeniu, sesja per request (Depends), konfiguracja Alembic i `alembic upgrade head` w lifespan aplikacji (requires: 1.1) (spec: TECHNICAL_GUIDELINES.md) (tech: python, fastapi, sqlite, sql)
  - AC: start na nieistniejącej ścieżce tworzy plik bazy i tabelę `alembic_version` (TG:8-9)
  - AC: `LEKTURY_DB_PATH` przenosi bazę do wskazanego pliku (TG:18)
  - AC: fixture testowy z tymczasowym plikiem SQLite per test, migracje uruchomione (A3, A19)
  - Specky: (req: 01M5JNJBDG93QNHV5379HRXF17 v1 @fc4136e)
  - Specky criteria: (crit: 01M5JNJBEFT8T7ZS911ETD6407) (crit: 01M5JNJBEG77T6N9EA0B04YZCX)
- [x] Test: 1.2 — start tworzy bazę; FK włączone (`PRAGMA foreign_keys` = 1); fixture izoluje testy
- [x] Task 1.3: Migracja początkowa + modele ORM — `books` (w tym title_norm, author_norm z unikalnym indeksem pary), `shelves` (name_norm unikalny), `book_shelves` (PK złożony, FK ON DELETE CASCADE), `notes` (book_id FK CASCADE, content, created_at) (requires: 1.2) (spec: lista-lektur.md) (tech: python, sql, sqlite)
  - AC: `books`: id, title, author, year, status, rating, title_norm, author_norm, created_at, updated_at (lista-lektur.md:24-32)
  - AC: duplikat pary (title_norm, author_norm) odrzucany przez bazę (R1, lista-lektur.md:36)
  - AC: usunięcie wiersza `books` kaskadowo usuwa `notes` i `book_shelves` (R3, lista-lektur.md:39)
  - AC: `name_norm` unikalny bez względu na wielkość liter (lista-lektur.md:46)
  - Specky: (req: 01M5JNJBMZ3E9C155BWZ1YKEJC v1 @3cf4bd9)
  - Specky: (req: 01M5JNJCZRYDDPRYK7M3DXDE5Z v1 @ac9845e)
  - Specky: (req: 01M5JNJD466AEHW02P8DB44SDT v1 @b10e73e)
  - Specky: (req: 01M5JNJBS0EPEP3TSA6H4QD6N6 v1 @ebeb2dd)
  - Specky: (req: 01M5JNJBY1D70DBG1EJP24G9YQ v1 @e14a41b)
- [x] Test: 1.3 — migracja na pustej bazie tworzy 4 tabele; constraints unikalności i kaskady działają
- [x] Task 1.4: Schematy Pydantic + `BookService` — normalizacja (R1), create, get, list (filtry status/shelf/q, sort `updated_at` desc), update częściowy (R2 wg S1: ocena 1–5 tylko przy `reading`/`read`, zmiana na `to_read` kasuje ocenę), delete (R3); komunikaty PL (requires: 1.3) (spec: lista-lektur.md) (tech: python, fastapi)
  - AC: entry — wywołania z routera `/api/books` (1.5) i z widoków HTML (2.4, 2.6)
  - AC: tytuł 1–200 po przycięciu, autor 1–120, rok opcjonalny 1450 ≤ rok ≤ bieżący+1, status domyślnie `to_read` (lista-lektur.md:27-30)
  - AC: duplikat (tytuł, autor) po normalizacji → 422 przy polu `title` z czytelnym komunikatem (R1)
  - AC: ocena przy `to_read` lub spoza 1–5 → 422; ocena z `reading` zostaje po zmianie na `read`; zmiana na `to_read` ustawia `rating=null` (S1)
  - AC: `q` dopasowuje fragment tytułu lub autora bez wielkości liter; filtry łączą się (lista-lektur.md:70)
  - Specky: (req: 01M5JNJBMZ3E9C155BWZ1YKEJC v1 @3cf4bd9)
  - Specky: (req: 01M5JNJCZRYDDPRYK7M3DXDE5Z v1 @ac9845e)
  - Specky: (req: 01M5JNJD1TJ1MABNK0535BD9Z8 v1 @1d012e2)
  - Specky: (req: 01M5JNJD466AEHW02P8DB44SDT v1 @b10e73e)
  - Specky criteria: (crit: 01M5JNJBNHHKH0CPABRA46YMVD) (crit: 01M5JNJBNJ5FWS6X307GYV86AQ) (crit: 01M5JNJBNJ3G2PT3YYPX92YS5X) (crit: 01M5JNJD03R9G6CQ77028G996V) (crit: 01M5JNJD032FE1JGM0AFGAN4V2) (crit: 01M5JNJD26WJ3MMGENKV9M116X) (crit: 01M5JNJD26AKTJC1MJED59BPX6) (crit: 01M5JNJD265HM74ETSWG8NSMHA) (crit: 01M5JNJD26RDSKJT1RQ58DD2PR)
- [x] Test: 1.4 — jednostkowe: normalizacja, R1, R2 (wariant S1), R3, walidacja pól, filtry i sortowanie
- [x] Task 1.5: Router `/api/books` — `GET` (lista, filtry `status`, `shelf`, `q`), `POST` (201), `GET /{id}` (z `shelves` i `notes`), `PATCH /{id}`, `DELETE /{id}` (204); globalne handlery 422/404 w formacie z 1.1 (requires: 1.4) (spec: lista-lektur.md) (tech: python, fastapi, rest-api)
  - AC: entry — `GET /api/books` i pozostałe ścieżki z tabeli w lista-lektur.md:68-74
  - AC: nieistniejące id → 404; błędne pola → 422 z listą pól (lista-lektur.md:65-66)
  - AC: `?status=czytam` odrzucone (422), akceptowane tylko `to_read|reading|read` (Q1)
  - AC: `PATCH` z samym `author` zmienia tylko autora i `updated_at`
  - Specky: (req: 01M5JNJC27DX8MDJN872Q85V9J v1 @b508d0c)
  - Specky: (req: 01M5JNJCXSEXSVD5D2NSP50PR6 v1 @8d7b3a8)
  - Specky criteria: (crit: 01M5JNJC2VFM8BZCR01MZ1JCT3) (crit: 01M5JNJC2VP96Y3TNJNYETA8NT) (crit: 01M5JNJC2VZ603VSQV5K1WD17A) (crit: 01M5JNJC2VY0KCBQBY5YFCQ8DZ) (crit: 01M5JNJCY4PC9KCVD68Y592R5S)
- [x] Test: 1.5 — integracyjne przez TestClient: każdy endpoint, kombinacje filtrów (shelf przez bezpośredni wpis w `book_shelves`), kody 201/204/404/422

### Phase 2: Półki, notatki, interfejs obu ekranów

- [ ] Task 2.1: `ShelfService` + router — `GET /api/shelves` (alfabetycznie `COLLATE NOCASE`, `book_count`), `POST /api/shelves` (nazwa 1–60, duplikat bez wielkości liter → 422 przy `name`), `DELETE /api/shelves/{id}` (odpina książki), `PUT /api/books/{id}/shelves` (`{"shelf_ids": [...]}`, nieznane id → 422) (requires: 1.5) (spec: lista-lektur.md) (tech: python, fastapi, rest-api)
  - AC: entry — ścieżki `/api/shelves*` i `PUT /api/books/{id}/shelves` (lista-lektur.md:75-78)
  - AC: półka może być pusta (R4); lista alfabetyczna z licznikiem (R5, lista-lektur.md:48-49)
  - AC: `PUT` z `[1,2]` a potem `[2]` zostawia książkę tylko na półce 2; pusta lista dozwolona
  - AC: usunięcie półki z książkami → 204, książki istnieją bez tej półki (A9)
  - Specky: (req: 01M5JNJBS0EPEP3TSA6H4QD6N6 v1 @ebeb2dd)
  - Specky: (req: 01M5JNJD6Q8C65Y542JWPHAHGM v1 @d2ee33b)
  - Specky criteria: (crit: 01M5JNJBSM2GAM0PE09MT2TFYC) (crit: 01M5JNJBSN9J04WGFZXK49R5HX) (crit: 01M5JNJBSNE7VH0561MPY70YTA) (crit: 01M5JNJD70JB2J9YHXSMR9FVXS) (crit: 01M5JNJD70P6Q8WWBAS94B0PQV) (crit: 01M5JNJD70889VR4YEM4WWA3S8)
- [ ] Test: 2.1 — integracyjne: CRUD półek, unikalność, kolejność, licznik, PUT shelves, filtr `shelf` w `GET /api/books`
- [ ] Task 2.2: `NoteService` + endpointy — `POST /api/books/{id}/notes` (201, treść 1–2000, 404 dla obcej książki), `DELETE /api/notes/{id}` (204/404); notatki w `GET /api/books/{id}` od najnowszej (R7); brak endpointu edycji (R6) (requires: 1.5) (spec: lista-lektur.md) (tech: python, fastapi, rest-api)
  - AC: entry — `POST /api/books/{id}/notes`, `DELETE /api/notes/{id}` (lista-lektur.md:79-80)
  - AC: pusta treść lub 2001 znaków → 422 przy `content` (lista-lektur.md:57)
  - AC: `GET /api/books/{id}` zwraca `notes` malejąco po `created_at` (R7)
  - Specky: (req: 01M5JNJBY1D70DBG1EJP24G9YQ v1 @e14a41b)
  - Specky: (req: 01M5JNJD8Q05DPW2129ERV76HS v1 @5a0eb6f)
  - Specky: (req: 01M5JNJD466AEHW02P8DB44SDT v1 @b10e73e)
  - Specky criteria: (crit: 01M5JNJBYS280EEM43ZME7Y9AB) (crit: 01M5JNJBYSBQ2M7QNWZKYM3R0Y) (crit: 01M5JNJBYSEH0759CW3W8F234H) (crit: 01M5JNJD8ZYH50QK3K5CSQ4AWG) (crit: 01M5JNJD8ZVZA1G2XQEB30V6BA) (crit: 01M5JNJD4JQNSEDMCKPZQD7DWS)
- [ ] Test: 2.2 — integracyjne: dodanie, usunięcie, 404, walidacja długości, kolejność, brak PATCH/PUT (405)
- [ ] Task 2.3: Powłoka UI — `base.html` (nagłówek: miejsce na statystyki, link „Eksport CSV”), `style.css` (tabela ≥ 640 px, karty < 640 px), filtry Jinja2 (daty, etykiety PL statusu, gwiazdki), helper `is_htmx(request)` i render pełny/fragment (requires: 1.1) (spec: lista-lektur.md, TECHNICAL_GUIDELINES.md) (tech: htmx, fastapi, accessibility)
  - AC: entry — każdy widok HTML dziedziczy z `base.html`; `GET /` renderuje powłokę
  - AC: układ jednokolumnowy poniżej 640 px bez poziomego przewijania (lista-lektur.md:113)
  - AC: formularze z `<label for>`, obsługa klawiaturą Tab/Enter (TG:25)
  - AC: daty w UI `dd.MM.yyyy` (TG:23); etykiety statusu po polsku (Q1)
  - Specky: (req: 01M5JNJCBV01239FVTB3Q35CRD v1 @cef8c9e)
  - Specky: (req: 01M5JNJCXSEXSVD5D2NSP50PR6 v1 @8d7b3a8)
  - Specky criteria: (crit: 01M5JNJCCBXZHZ1HN80R201YG9) (crit: 01M5JNJCCBDSJ3G1P8HK42H9Z4) (crit: 01M5JNJCY4CP4ZYBZ9HR3X8S00)
- [ ] Test: 2.3 — render `base.html`, filtry dat/etykiet/gwiazdek, `is_htmx` rozpoznaje nagłówek `HX-Request`
- [ ] Task 2.4: Ekran „Lista” (`GET /`) — tabela/karty książek, formularz „Dodaj książkę” (tytuł, autor, rok) z HTMX i fallbackiem POST+PRG, zmiana statusu w wierszu jednym kliknięciem (requires: 1.5, 2.3) (spec: lista-lektur.md) (tech: htmx, fastapi, accessibility)
  - AC: wiersz: tytuł (link do `/books/{id}`), autor, rok, status, ocena w gwiazdkach, półki jako etykiety (lista-lektur.md:93)
  - AC: entry — `GET /` (strona główna); `POST /books` i `POST /books/{id}/status` z formularzy
  - AC: po dodaniu formularz się czyści, nowa pozycja na górze bez przeładowania (lista-lektur.md:94-95)
  - AC: zmiana statusu bez wchodzenia w szczegóły, odświeżony tylko wiersz (lista-lektur.md:96)
  - AC: błąd walidacji (np. pusty tytuł, duplikat) przy polu, nie alert (lista-lektur.md:114)
  - AC: bez JS formularz POST kończy się przekierowaniem na listę z nową książką (lista-lektur.md:112)
  - Specky: (req: 01M5JNJCEPTKY0YVR0GP628M3R v1 @06b6899)
  - Specky: (req: 01M5JNJCBV01239FVTB3Q35CRD v1 @cef8c9e)
  - Specky: (req: 01M5JNJCXSEXSVD5D2NSP50PR6 v1 @8d7b3a8)
  - Specky criteria: (crit: 01M5JNJCF5FQS8KHMDEWH4EEBZ) (crit: 01M5JNJCF5K1H3JEVZQVR12B33) (crit: 01M5JNJCF5WHBZ6SQWG62J3WXG) (crit: 01M5JNJCCBFG5JC7MES61ZZ3T7) (crit: 01M5JNJCCBV4KQ4DMWTE3A5SH6) (crit: 01M5JNJCY48R0NGCK2T4RHWD50)
- [ ] Test: 2.4 — TestClient: render listy z fixture, `HX-Request` zwraca fragment, bez nagłówka redirect 303, błędy przy polu w HTML, zmiana statusu
- [ ] Task 2.5: Ekran „Lista” — rozwijana sekcja „Półki”: formularz dodania (nazwa, błąd przy polu), lista półek z licznikiem i przyciskiem usunięcia (`hx-confirm`; bez JS strona potwierdzenia); po zmianie odświeżona lista rozwijana półek (requires: 2.1, 2.4) (spec: lista-lektur.md) (tech: htmx, fastapi, accessibility)
  - AC: entry — przycisk „Półki” na ekranie Lista; `POST /shelves`, `POST /shelves/{id}/delete`
  - AC: dodanie półki pokazuje ją w sekcji i w filtrze bez przeładowania (Q2)
  - AC: usunięcie wymaga potwierdzenia; książki zostają (A4, lista-lektur.md:123)
  - AC: duplikat nazwy → komunikat przy polu nazwy
  - Specky: (req: 01M5JNJCGXJWYBMCEHGCEB21Q3 v1 @fc5d04d)
  - Specky criteria: (crit: 01M5JNJCH7S65DEFPAQ8S57P7V) (crit: 01M5JNJCH7TBY47QETRQDX28AY) (crit: 01M5JNJCH7DTP27AA4PS57K9Z6)
- [ ] Test: 2.5 — render sekcji, dodanie/usunięcie przez formularze (HTMX i bez JS), komunikat duplikatu
- [ ] Task 2.6: Ekran „Szczegóły” (`GET /books/{id}`) — pola tytuł/autor/rok/status/ocena z zapisem per pole (`hx-trigger="change"`), gwiazdki 1–5 aktywne przy `reading`/`read`, bez JS formularz „Zapisz”; „Usuń książkę” z potwierdzeniem → redirect na `/` (requires: 1.5, 2.3) (spec: lista-lektur.md) (tech: htmx, fastapi, accessibility)
  - AC: entry — link tytułu z listy prowadzi do `/books/{id}` (lista-lektur.md:97)
  - AC: zmiana pola zapisuje się bez przeładowania; po odświeżeniu wartość zachowana (Q3)
  - AC: rok 1200 → komunikat przy polu, wartość w bazie bez zmian (lista-lektur.md:29, 114)
  - AC: gwiazdki nieaktywne z podpowiedzią przy `to_read`; przy `reading` kliknięcie zapisuje ocenę; zmiana na `read` ją zachowuje (S1)
  - AC: usunięcie po potwierdzeniu przekierowuje na listę bez tej książki (lista-lektur.md:108)
  - AC: 404 dla nieistniejącej książki renderowane jako strona błędu
  - Specky: (req: 01M5JNJCN0DVWSCXXHSGHSGG6V v1 @1f96712)
  - Specky: (req: 01M5JNJD1TJ1MABNK0535BD9Z8 v1 @1d012e2)
  - Specky criteria: (crit: 01M5JNJCNC307GVYBRS5WXDG1H) (crit: 01M5JNJCNCN762H1ZTHNKDWEH7) (crit: 01M5JNJCNCT9XX35EHR5NAZRGJ) (crit: 01M5JNJCNCQ5Q9XKZHHJC5V1MK)
- [ ] Test: 2.6 — render szczegółów, PATCH per pole (fragment), formularz bez JS, gwiazdki wg statusu, usunięcie, 404
- [ ] Task 2.7: Ekran „Szczegóły” — półki jako pola wyboru (zaznacz/odznacz zapisuje od razu przez `PUT shelves`), notatki: pole dodania na górze, lista od najnowszej z datą `dd.MM.yyyy HH:mm`, przycisk usunięcia przy każdej; bez edycji (requires: 2.1, 2.2, 2.6) (spec: lista-lektur.md) (tech: htmx, fastapi, accessibility)
  - AC: entry — sekcje „Półki” i „Notatki” na `/books/{id}`; `POST /books/{id}/shelves`, `POST /books/{id}/notes`, `POST /notes/{id}/delete`
  - AC: zaznaczenie pola wyboru zapisuje od razu; po odświeżeniu pozostaje zaznaczone (lista-lektur.md:105)
  - AC: nowa notatka pojawia się na górze bez przeładowania (R7, lista-lektur.md:106-107)
  - AC: brak przycisku i pola edycji notatki (R6)
  - Specky: (req: 01M5JNJCQ3R4AE48RKKE4G98B7 v1 @4b7c65a)
  - Specky criteria: (crit: 01M5JNJCQE7A0ZQDQNNA42SX0S) (crit: 01M5JNJCQEVYGC2P99P6Q94253) (crit: 01M5JNJCQERARJF7345H59VD3K)
- [ ] Test: 2.7 — checkboxy półek (HTMX i bez JS), dodanie/usunięcie notatki, kolejność, walidacja treści przy polu
- [ ] Task 2.8: E2E test — dodanie książki → zmiana statusu w wierszu → szczegóły: edycja autora, ocena przy `czytam`, półka (dodanie, zaznaczenie), notatka dodanie/usunięcie → usunięcie książki; job `e2e` w CI (requires: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7) (spec: lista-lektur.md) (tech: playwright, python, github-actions)
  - AC: fixture uruchamia uvicorn na wolnym porcie z osobnym plikiem bazy (A19)
  - AC: test przechodzi przez ekran „Lista” i „Szczegóły” (A8, lista-lektur.md:128-129)
  - AC: CI uruchamia e2e na Chromium na PR i main; raport `reports/junit-e2e.xml` w artefakcie JUnit (Q4)
  - AC: błędy walidacji w e2e widoczne przy polu (lista-lektur.md:114)
  - Specky: (req: 01M5JNJCTA42TVEMS952S2K1H9 v1 @cf83d75)
  - Specky criteria: (crit: 01M5JNJCTX4YJJQDXH78465WHM) (crit: 01M5JNJCTXK9TDHGTB20FEZFYF)

### Phase 3: Szukanie i filtry, eksport CSV, statystyki

- [ ] Task 3.1: Pasek filtrów na ekranie „Lista” — przyciski statusu (wszystkie/do przeczytania/czytam/przeczytana), lista rozwijana półek, pole `q` z `hx-trigger="keyup changed delay:300ms"` i przyciskiem „Szukaj” bez JS; filtry łączone w query string, `hx-push-url`, podmiana tylko listy (requires: 2.4, 2.5) (spec: lista-lektur.md) (tech: htmx, fastapi, accessibility)
  - AC: entry — pasek filtrów nad listą na `GET /`; parametry `status`, `shelf`, `q`
  - AC: filtry statusu, półki i szukania łączą się; wynik zgodny z `GET /api/books` z tymi samymi parametrami (A3, lista-lektur.md:122)
  - AC: szukanie w trakcie pisania z opóźnieniem ok. 300 ms, bez przeładowania (lista-lektur.md:92)
  - AC: odświeżenie strony zachowuje aktywne filtry z URL
  - Specky: (req: 01M5JNJCJWM1SF2P2Y1NWZXSVY v1 @e99ec66)
  - Specky criteria: (crit: 01M5JNJCK89CNSWP5DT8SNJBCD) (crit: 01M5JNJCK876SZCQFJ4EX5RDVP) (crit: 01M5JNJCK8EWG0VB920K3TTRQ9)
- [ ] Test: 3.1 — render paska, kombinacje parametrów dają ten sam zbiór id co API, fragment przy `HX-Request`, formularz bez JS
- [ ] Task 3.2: `GET /api/export.csv` — wszystkie książki, kolumny tytuł,autor,rok,status,ocena,półki (nazwy rozdzielone `;`, alfabetycznie), UTF-8 z BOM, przecinek, etykiety PL statusu, `Content-Disposition: attachment; filename="lektury.csv"`; link „Eksport CSV” w nagłówku (requires: 2.1, 2.3) (spec: lista-lektur.md) (tech: python, fastapi, htmx)
  - AC: entry — link „Eksport CSV” w nagłówku obu ekranów (Q2)
  - AC: plik zawiera nagłówek i wiersz dla każdej książki z kolumnami z sekcji 4 (A6, lista-lektur.md:81)
  - AC: półki w jednej kolumnie rozdzielone `;` (lista-lektur.md:81)
  - AC: odpowiedź zaczyna się od BOM, `text/csv`, nazwa pliku `lektury.csv` (A10)
  - Specky: (req: 01M5JNJC664Y1XZXE9TK4YPB9T v1 @ca7ae9e)
  - Specky criteria: (crit: 01M5JNJC6S8FX7X6XGG4SB2B8C) (crit: 01M5JNJC6SG6Z827GYCE4XNQJ6) (crit: 01M5JNJC6SZ9SKKYRQJZVJ7GTR) (crit: 01M5JNJC6STWJ3EA28NK9ZDT4C)
- [ ] Test: 3.2 — integracyjny: nagłówek, liczba wierszy, półki `;`, BOM, nagłówki HTTP, puste pola rok/ocena; parsowanie modułem `csv`
- [ ] Task 3.3: `GET /api/stats` + `StatsService` — liczby `to_read`, `reading`, `read` i `average_rating` (tylko `read` z oceną, zaokrąglone do 0,1, `null` bez ocen); statystyki w nagłówku layoutu, odświeżane out-of-band po każdej operacji HTMX (dodanie, status, ocena, usunięcie) (requires: 2.4, 2.6, 2.7) (spec: lista-lektur.md) (tech: python, fastapi, htmx)
  - AC: entry — `GET /api/stats`; nagłówek layoutu ładuje statystyki przy każdym renderze
  - AC: 2×to_read, 1×reading, 2×read z ocenami 4 i 5 → `to_read=2, reading=1, read=2, average_rating=4.5` (lista-lektur.md:82)
  - AC: bez ocenionych przeczytanych `average_rating` = null (A11)
  - AC: po każdej operacji liczniki w nagłówku zgodne z bazą bez przeładowania (A7, lista-lektur.md:127)
  - Specky: (req: 01M5JNJC92ST45R6HKAP0C74SZ v1 @1832259)
  - Specky criteria: (crit: 01M5JNJC9EBJB0ZHNAM076HF2Q) (crit: 01M5JNJC9E527FQCDGD1MXYGDR) (crit: 01M5JNJC9ERY4G58GS31GB52B3)
- [ ] Test: 3.3 — jednostkowy zaokrąglenia i null; integracyjny endpoint; odpowiedzi HTMX zawierają fragment OOB nagłówka
- [ ] Task 3.4: E2E test — Playwright: filtry łączone (status + półka + q, porównanie z API), eksport CSV (pobranie pliku, nagłówek, zawartość), statystyki w nagłówku po dodaniu, zmianie statusu, ocenie i usunięciu książki; dodanie do jobu `e2e` w CI (requires: 3.1, 3.2, 3.3) (spec: lista-lektur.md) (tech: playwright, python)
  - AC: wynik filtrów w UI = zbiór z `GET /api/books` (A3)
  - AC: pobrany CSV parsuje się i zawiera wszystkie książki (A6)
  - AC: liczniki w nagłówku zgodne z bazą po każdej operacji (A7)
  - Specky: (req: 01M5JNJCJWM1SF2P2Y1NWZXSVY v1 @e99ec66)
  - Specky: (req: 01M5JNJC664Y1XZXE9TK4YPB9T v1 @ca7ae9e)
  - Specky: (req: 01M5JNJC92ST45R6HKAP0C74SZ v1 @1832259)

### Phase 4: Wydanie v0.1.0

- [ ] Task 4.1: Wydanie `v0.1.0` — `README.md` (instalacja, uruchomienie, `LEKTURY_DB_PATH`, testy, e2e lokalnie z WebKit), `CHANGELOG.md`, pełna suita + ruff + e2e zielone na main, tag `v0.1.0`, migawka Specky (`create_snapshot` z tagiem, SHA i scenariuszami testów manualnych) (requires: 3.4) (spec: lista-lektur.md, TECHNICAL_GUIDELINES.md) (tech: python, github-actions)
  - AC: README opisuje jedną komendę startu po `pip install -r requirements.txt` (TG:29)
  - AC: tag `v0.1.0` na zielonym main (lista-lektur.md:135)

## Spec coverage

| File | Section | Tasks |
|------|---------|-------|
| TECHNICAL_GUIDELINES.md | Tytuł | out of scope — nagłówek bez treści |
| TECHNICAL_GUIDELINES.md | Stack | 1.1, 1.2, 1.3, 2.3, 2.8 |
| TECHNICAL_GUIDELINES.md | Hosting i infrastruktura | 1.1, 1.2, 2.8, 4.1 |
| TECHNICAL_GUIDELINES.md | Wymagania niefunkcjonalne | 2.3, 2.4, 2.6, 2.7, 4.1 (WebKit lokalnie, Q4) |
| TECHNICAL_GUIDELINES.md | Inne ograniczenia | 1.1, 2.3, 4.1 |
| lista-lektur.md | Tytuł | out of scope — nagłówek bez treści |
| lista-lektur.md | Cel i kontekst | 1.1 (jeden proces, jedna baza, bez kont); integracje z księgarniami, okładki, rekomendacje, multi-user — out of scope — wprost wyłączone w spec (lista-lektur.md:10) |
| lista-lektur.md | Słownik | 1.3, 1.4 |
| lista-lektur.md | Model — nagłówek | out of scope — wstęp bez wymagań |
| lista-lektur.md | Model: Książka | 1.3, 1.4, 1.5 |
| lista-lektur.md | Model: Półka | 1.3, 2.1 |
| lista-lektur.md | Model: Notatka | 1.3, 2.2 |
| lista-lektur.md | API (JSON) | 1.1, 1.5, 2.1, 2.2, 3.2, 3.3 |
| lista-lektur.md | UI — zasady ogólne | 2.3, 2.4 |
| lista-lektur.md | Ekran „Lista” | 2.4, 2.5, 3.1, 3.3 |
| lista-lektur.md | Ekran „Szczegóły” | 2.6, 2.7 |
| lista-lektur.md | Zasady wspólne UI | 2.3, 2.4, 2.5, 2.6, 2.7, 3.1 |
| lista-lektur.md | Kryteria akceptacji | A1: 1.4, 1.5, 2.4, 2.6, 2.8; A2: 1.4, 2.6; A3: 1.5, 3.1, 3.4; A4: 2.1, 2.5, 2.7; A5: 2.2, 2.7; A6: 3.2, 3.4; A7: 3.3, 3.4; A8: 1.4–3.4 (testy), 2.8, 3.4 (e2e) |
| lista-lektur.md | Kolejność prac | Phase 1, Phase 2, Phase 3, Phase 4 (`v0.1.0`) |

## Notes

- Dependencies: `(requires: X.X, Y.Y)` - Telesma skips the task if its dependencies are not completed
- Phase numbering: digit or digit+letter (e.g. `Phase 2`, `Phase 2M`, `Phase 6.Z1`). Suffix `.Z<n>` = a rework phase resulting from a change in `telesma/changes/`.
- Documentation: `(spec: file.md, other-file.md)` - Telesma loads ONLY the related fragments of these files (through telesma/state/SPEC_INDEX.md + Read with offset/limit)
- Technology: `(tech: tag1, tag2)` - Telesma loads style/convention guidelines from `telesma/guidelines/<tag>.md` + always `general.md`. Tags must exist in `telesma/guidelines/` (missing = TELESMA BLOCKED).
- Change: `(change: <file-name>.md)` — annotation on tasks modified or created by a file from `telesma/changes/`. When working on the task Telesma reads `telesma/changes/processed/<file-name>.md` to learn the context (what changed and why).
- Every implementation task has a `- [ ] Test: ...` item (unit/integration) right after it.
- **E2E at the end of a phase as a full task**: phases with UI (`tech: htmx`) end with `Task N.X: E2E test — [scenarios]` with `(requires: ...)` covering every task of the phase and `(tech: playwright, python)` — Playwright in Python per TECHNICAL_GUIDELINES.md:10, not TypeScript.
- **Rework phases `.Z<n>`**: created automatically by Telesma when a change from `telesma/changes/` touches a ✅ task. Numbering: `Phase <N>.Z1`, `.Z2`, ..., where `N` is the phase whose task is being reworked. Every task in a Z phase has `(requires: <original-number>)` on the task being reworked and `(change: ...)`. The original task's checkbox is NOT unchecked — the completion history stays.
- Widoki HTML i `/api` korzystają z tej samej warstwy serwisów (A12) — reguły R1–R3 egzekwowane w serwisie, nigdy tylko w szablonie.
- Formularze bez JS używają POST + przekierowania (PRG); ścieżki formularzy widoków (`/books`, `/shelves`, `/notes/...`) są oddzielne od `/api` (A14).
- Specky: kryteria `(crit: …)` są nadrzędne wobec `- AC:` — test kryterium oznacz komentarzem `specky: crit <id>` w linii nad testem; własne `- AC:` uzupełniają je o punkty wejścia i odniesienia do spec.
