# PROJECT_CONTEXT.md

This file keeps the project context that survives `/compact`.

## Tech stack

- Language: Python 3.12 (lokalnie `.venv` tworzony przez `uv venv --python 3.12 .venv`)
- Framework: FastAPI (API JSON pod `/api` + widoki HTML), Jinja2, HTMX 2.0.4 (`app/static/htmx.min.js`)
- Database: SQLite (`LEKTURY_DB_PATH`, domyślnie `data/lektury.db`), SQLAlchemy 2.x (sync), Alembic
- Tests: pytest + FastAPI `TestClient`; e2e Playwright (Python, marker `e2e`); ruff (lint + format)
- CI: `.github/workflows/specky-ci.yml`, job `test` (pytest z JUnit, e2e na preinstalowanym Chrome przez `--browser-channel chrome`, ruff)
- SQLite: każde połączenie dostaje `journal_mode=WAL`, `synchronous=NORMAL`, `foreign_keys=ON`, `busy_timeout=5000` (`app/db.py`); migracje `alembic upgrade head` w `lifespan`
- Testy: fixture `app`/`client`/`session` w `tests/conftest.py` — świeży plik SQLite per test w `tmp_path`

## Architecture

Mapa modułów (directory → responsibility):

| Moduł | Odpowiedzialność |
|-------|------------------|
| `app/main.py` | `create_app(settings)` + `lifespan`; rejestracja handlerów błędów, `/static`, routerów |
| `app/config.py` | Jedyne miejsce czytające `os.environ` (`LEKTURY_DB_PATH`) → `Settings` |
| `app/errors.py` | `FieldError`, `DomainValidationError`, `NotFoundError` + handlery API (422/404) |
| `app/statuses.py` | `BookStatus` (`to_read/reading/read`), `STATUS_LABELS` (PL), `RATEABLE_STATUSES` |
| `app/db.py` | Engine, sesja per request, PRAGMA foreign_keys, migracje przy starcie (1.2) |
| `app/models.py` | Modele ORM SQLAlchemy 2.0 (`Mapped`, `mapped_column`) (1.3) |
| `app/schemas.py` | Schematy Pydantic v2 per kierunek: `*Create`, `*Update`, `*Read` (1.4) |
| `app/services/` | Logika domenowa i reguły R1–R7; przyjmują sesję i proste argumenty, rzucają wyjątki domenowe |
| `app/routers/api/` | Cienkie routery JSON pod `/api` (parsowanie → serwis → schemat) |
| `app/routers/views/` | Widoki HTML i fragmenty HTMX; te same serwisy co API |
| `app/templates/`, `app/static/` | Szablony Jinja2, CSS, HTMX |
| `alembic/` | Migracje schematu |
| `tests/` | `test_<moduł>.py`; `tests/e2e/` dla Playwright |

Format błędów API: `422` → `{"detail": [{"field": "<pole>", "message": "<komunikat PL>"}]}`
(zarówno błędy Pydantic, jak i `DomainValidationError` z serwisów); `404` → `{"detail": "<komunikat>"}`.

Konwencje nazw: kod, identyfikatory, klucze JSON i komentarze po angielsku; teksty UI i komunikaty
błędów po polsku. Statusy w DB/API to kody `to_read/reading/read`, etykiety PL tylko przez `STATUS_LABELS`.
Endpointy synchroniczne (`def`) — sync SQLAlchemy działa w threadpoolu FastAPI.

Warstwy: router → serwis → ORM. Routery nie importują się nawzajem i nie zawierają reguł biznesowych.
Widoki HTML formularzy (bez JS) używają POST + 303 (PRG) na ścieżkach poza `/api`.

## Key decisions

<!-- The table grows with every session, and the file goes into the startup prompt in full, so    -->
<!-- telesma.sh keeps its 40 latest rows in it — older ones go to telesma/state/CONTEXT_ARCHIVE.md     -->
<!-- (write-only). A decision that is still BINDING — one whose violation would break the project — -->
<!-- mark with 📌 in the Decision column: a row with 📌 is never rotated.                           -->

| Date | Decision | Reason |
|------|----------|--------|
| 2026-10-22 | 📌 Ocena 1–5 dozwolona przy `reading` i `read`; zmiana na `to_read` kasuje ocenę | Rozstrzygnięcie S1 (QUESTIONS.md), wymaganie Specky 01M5JNJD1TJ1MABNK0535BD9Z8 |
| 2026-10-22 | 📌 Status w DB/API jako kody EN, etykiety PL w UI i CSV | Q1, wymaganie Specky 01M5JNJCXSEXSVD5D2NSP50PR6 |
| 2026-10-22 | 📌 Jeden format błędu 422 dla Pydantic i serwisów, komunikaty PL | A18; komunikaty trafiają też do szablonów przy polu |
| 2026-10-22 | Migracje Alembic uruchamiane w `lifespan` mimo wytycznej fastapi.md | A2: spec wymaga jednej komendy startu i tworzenia bazy przy starcie |
| 2026-10-22 | `requirements.txt` / `requirements-dev.txt` w pełni przypięte zamiast pyproject + lock | TECHNICAL_GUIDELINES.md:29 wymaga `pip install -r requirements.txt`; plik pełni rolę lockfile |
| 2026-10-22 | Brak pydantic-settings; `app/config.py` czyta jedną zmienną | Jedna zmienna konfiguracji, YAGNI |
| 2026-10-22 | 📌 Tabele `STRICT`; teksty `Text`, daty jako tekst ISO `%Y-%m-%dT%H:%M:%S.%fZ` (typ `UtcDateTime`) | Wytyczne sqlite.md; STRICT nie przyjmuje VARCHAR/DATETIME; stała szerokość = sortowanie tekstowe = chronologiczne |
| 2026-10-22 | 📌 `normalize_text` (casefold, przycięcie, pojedyncze spacje) dla R1, unikalności półek i szukania `q` | SQLite `LIKE` jest case-insensitive tylko dla ASCII; szukanie po kolumnach `*_norm` |
| 2026-10-22 | CHECK w bazie: status, zakres oceny, ocena tylko przy `reading`/`read` | Druga linia obrony reguł z serwisu (S1) |
| 2026-10-22 | 📌 `update_book(session, id, changes)` dostaje TYLKO pola obecne w żądaniu (`model_dump(exclude_unset=True)`); `null` czyści rok/ocenę, dla tytułu/autora/statusu daje 422 | Semantyka PATCH (A8); widoki HTML przekazują ten sam słownik |
| 2026-10-22 | Duplikat książki → 422 przy `title` z `DUPLICATE_MESSAGE`; walidacja zbiera wszystkie błędy naraz | A5, A18 — komunikaty przy wszystkich polach formularza |
| 2026-10-22 | `GET /api/books` zwraca tablicę (bez koperty `items`), `POST` → 201 + `Location`, ciała zapisu z `extra="forbid"` | Kontrakt ze spec (sekcja 4); wytyczne rest-api.md tam, gdzie nie kolidują |
| 2026-10-22 | `PUT /api/books/{id}/shelves` podbija `updated_at` książki; nieznane id półki → 422 przy `shelf_ids`, nic nie zmienia | A9; zmiana półek to zmiana książki (sort listy) |
| 2026-10-22 | 📌 Zapisy (POST/PUT/PATCH/DELETE) z innej witryny → 403 (`Origin` ≠ własny, `Sec-Fetch-Site` ≠ same-origin/none) — `app/security.py` | Wytyczne htmx.md (CSRF); aplikacja bez logowania i ciasteczek nasłuchuje na localhost |
| 2026-10-22 | 📌 HTMX: `htmx-config.responseHandling` podmienia odpowiedzi 422 (fragment formularza z błędami przy polu) | Wytyczne htmx.md; domyślnie htmx 2 nie podmienia 4xx |
| 2026-10-22 | Ścieżki spoza `/api` dostają stronę HTML 404 (także dla błędnego id), `/api` — JSON | `app/error_pages.py` |
| 2026-10-22 | Testy widoków parsują HTML helperem `tests/html.py` (stdlib), zapytania po id/atrybutach/tekście | Wytyczne htmx.md: asercje na HTML, nie porównanie stringów |
| 2026-10-22 | Akcje GitHub przypięte do SHA (checkout v4.2.2, setup-python v5.6.0, upload-artifact v4.6.2) | Wytyczne github-actions.md |

## Known problems and solutions

<!-- Known pitfalls: distilled from the Problem log at the end-of-phase checkpoint (section 7  -->
<!-- of the instructions). Only RECURRING patterns — a one-off error stays in the Problem log  -->
<!-- in REPORT.md. One row = one pitfall, on ONE line and concise: the file goes               -->
<!-- in full into the prompt of every session.                                                 -->
<!-- telesma.sh keeps the 30 latest rows here, older ones → telesma/state/CONTEXT_ARCHIVE.md.      -->
<!-- A pitfall that COMES BACK despite being written down (happened ≥2 times): mark it with 📌 -->
<!-- — such a row never rotates. Leave a one-off slip unmarked.                                -->

| Problem | Solution |
|---------|----------|
| Systemowy Python 3.13 bez certyfikatów SSL, brak 3.12 | `uv venv --python 3.12 .venv`; instalacja przez `uv pip install` |
| `playwright install --with-deps chromium` w CI trwa ~10 min | e2e na preinstalowanym Chrome runnera: `--browser-channel chrome` |
| Ruff uznaje `alembic` za moduł projektu (katalog `alembic/`) | `known-third-party = ["alembic"]` w `pyproject.toml` |
| Mutacja kodu produkcyjnego (np. wyłączenie reguły) blokowana przez klasyfikator auto mode | Czułość testu reguły uzasadniać wartością domyślną/danymi testu; zapis w Problem log |

## Component dependencies

Routery API i widoki HTML wołają te same funkcje serwisów; serwisy dostają sesję SQLAlchemy z
zależności `get_session` (1.2). Statystyki w nagłówku layoutu liczy serwis statystyk (3.3).

## Current state

<!-- CURRENT STATE — OVERWRITE. It should answer "where are we TODAY", not be a chronicle    -->
<!-- of turns: task history has its own place in REPORT.md and rotates there, while nothing  -->
<!-- rotates here. Appending more "turn of 08-19 closed" paragraphs turns this               -->
<!-- section into a second, unbounded report in the prompt of every session.                 -->

- Last completed task: 2.3 Powłoka UI
- Next task: 2.4 Ekran «Lista»
- Tag `telesma/phase-1` założony po poprawce audytu zależności (PR #6)
- Blockers: brak
