# Project technical guidelines

## Stack — departures from the defaults

- **Language / runtime**: Python 3.12
- **Backend framework**: FastAPI (serwuje API i widoki)
- **Frontend framework**: HTMX + szablony Jinja2 renderowane po stronie serwera; bez frameworka SPA, bez bundlera
- **Database**: SQLite — jeden plik `data/lektury.db`, tworzony przy starcie
- **ORM / DB access**: SQLAlchemy 2.x (Core lub ORM), migracje przez Alembic
- **Test runner**: pytest; e2e Playwright (Python)
- **Other imposed libraries**:

## Hosting and infrastructure

- **Target environment**: lokalny komputer użytkownika, `uvicorn` na porcie 8000
- **Containers**: brak
- **CI/CD**: GitHub Actions
- **Secrets / config**: zmienne środowiskowe (`LEKTURY_DB_PATH`), bez sekretów
- **Monitoring / logs**: standardowy log uvicorna

## Non-functional requirements (when they differ from the defaults)

- **Localization / i18n**: interfejs po polsku, kod i komentarze po angielsku; daty w UI w formacie dd.MM.yyyy
- **Browser support**: Chrome i Safari, ostatnie 2 wersje
- **Accessibility (a11y)**: formularze z etykietami, obsługa klawiaturą

## Other constraints

- Jedna komenda uruchamia aplikację po `pip install -r requirements.txt`.
- Zero zależności frontendowych instalowanych przez npm; HTMX dołączony jako jeden plik statyczny.
