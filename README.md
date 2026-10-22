# Lista lektur

Mała aplikacja webowa dla jednej osoby do prowadzenia własnej listy lektur: co chcę przeczytać,
co czytam, co przeczytałem i co o tym myślę. Działa lokalnie (jeden proces, jeden plik bazy SQLite),
bez logowania i bez kont. Interfejs jest po polsku, renderowany po stronie serwera (FastAPI + Jinja2)
i odświeżany fragmentami przez HTMX — działa też bez JavaScriptu (zwykłe formularze).

## Wymagania

- Python 3.12
- Chrome lub Safari (2 ostatnie wersje)

## Instalacja i uruchomienie

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --port 8000
```

Aplikacja jest dostępna pod <http://127.0.0.1:8000/>. Przy pierwszym starcie tworzy plik bazy
`data/lektury.db` i zakłada schemat (migracje Alembic uruchamiają się automatycznie przy każdym starcie).

| Zmienna | Domyślnie | Znaczenie |
|---------|-----------|-----------|
| `LEKTURY_DB_PATH` | `data/lektury.db` | Ścieżka do pliku bazy SQLite; brakujące katalogi są tworzone |

## Ekrany

- **Lista** (`/`) — dodawanie książek, zmiana statusu jednym kliknięciem, filtry statusu, półki
  i szukania (łączone, zapisane w adresie strony), sekcja „Półki” (dodawanie i usuwanie półek),
  statystyki i link „Eksport CSV” w nagłówku.
- **Szczegóły** (`/books/{id}`) — edycja pól w miejscu (każde pole zapisuje się osobno), ocena
  gwiazdkami 1–5 (przy statusie „czytam” i „przeczytana”), półki jako pola wyboru, notatki,
  usuwanie książki z potwierdzeniem.

## API (JSON)

Odpowiedzi w JSON; błędy walidacji to `422` z listą `{"detail": [{"field", "message"}]}`,
brak zasobu to `404`. Status książki ma wartości `to_read`, `reading`, `read`.

| Metoda i ścieżka | Działanie |
|------------------|-----------|
| `GET /api/books` | Lista; filtry `status`, `shelf` (id), `q` (fragment tytułu lub autora); sortowanie po dacie zmiany malejąco |
| `POST /api/books` | Dodanie książki (`201` + `Location`); duplikat tytułu i autora → `422` |
| `GET /api/books/{id}` | Szczegóły z półkami i notatkami (od najnowszej) |
| `PATCH /api/books/{id}` | Zmiana wybranych pól; ocena 1–5 tylko przy `reading`/`read`, zmiana na `to_read` kasuje ocenę |
| `DELETE /api/books/{id}` | Usunięcie książki razem z notatkami (`204`) |
| `GET /api/shelves` | Półki alfabetycznie z liczbą książek |
| `POST /api/shelves` | Dodanie półki (nazwa unikalna bez względu na wielkość liter) |
| `DELETE /api/shelves/{id}` | Usunięcie półki; książki zostają (`204`) |
| `PUT /api/books/{id}/shelves` | Ustawienie pełnej listy półek książki: `{"shelf_ids": [1, 2]}` |
| `POST /api/books/{id}/notes` | Dodanie notatki (`{"content": "..."}`, 1–2000 znaków) |
| `DELETE /api/notes/{id}` | Usunięcie notatki (`204`); notatek nie można edytować |
| `GET /api/export.csv` | Eksport wszystkich książek do CSV (UTF-8 z BOM, półki rozdzielone `;`) |
| `GET /api/stats` | Liczba książek w każdym statusie i średnia ocena przeczytanych (`null` bez ocen) |

Dokumentacja interaktywna: <http://127.0.0.1:8000/docs>.

## Testy

```bash
pip install -r requirements-dev.txt
pytest -q                 # testy jednostkowe i integracyjne
ruff check .              # lint
pytest -m e2e --browser chromium --browser-channel chrome   # e2e w Chrome (Playwright)
pytest -m e2e --browser webkit                              # e2e w WebKit (Safari), po `playwright install webkit`
```

CI (GitHub Actions, `.github/workflows/specky-ci.yml`) uruchamia testy, e2e na Chrome i ruff dla każdego
pull requesta i dla `main`, publikując raporty JUnit.

## Struktura

| Katalog | Zawartość |
|---------|-----------|
| `app/services/` | Reguły biznesowe (książki, półki, notatki, eksport, statystyki) |
| `app/routers/api/` | API JSON pod `/api` |
| `app/routers/views/` | Widoki HTML i fragmenty HTMX |
| `app/templates/`, `app/static/` | Szablony Jinja2, CSS, HTMX |
| `alembic/` | Migracje schematu |
| `tests/`, `tests/e2e/` | Testy pytest i Playwright |
