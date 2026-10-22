# telesma/state/SPEC_INDEX.md — indeks dokumentacji

Wygenerowano: 2026-10-22

## Statistics

- **Files**: 2
- **Total lines**: 165
- **Total size**: ~7.4 KB
- **UX/UI files**: 0 (katalog `telesma/spec/ux_ui/` istnieje, ale jest pusty)
- **Flow files**: 0 (`telesma/spec/APP_FLOW.md` nie istnieje; `Recordings: no`)

## Files

### TECHNICAL_GUIDELINES.md (30 lines)
Wytyczne techniczne projektu: narzucony stack (Python 3.12, FastAPI, HTMX + Jinja2, SQLite, SQLAlchemy 2.x, Alembic, pytest, Playwright), hosting lokalny, CI w GitHub Actions oraz wymagania niefunkcjonalne (język UI, przeglądarki, a11y).

#### Sections:
| Lines | Section | Anchor | Description |
|-------|--------|---------|------|
| 1-2 | Tytuł | # Project technical guidelines | Nagłówek dokumentu |
| 3-12 | Stack | ## Stack — departures from the defaults | Python 3.12, FastAPI (API + widoki), HTMX + Jinja2 bez SPA, SQLite `data/lektury.db`, SQLAlchemy 2.x + Alembic, pytest + Playwright (Python) |
| 13-20 | Hosting i infrastruktura | ## Hosting and infrastructure | Lokalny komputer, `uvicorn` na porcie 8000, bez kontenerów, GitHub Actions, zmienna `LEKTURY_DB_PATH`, log uvicorna |
| 21-26 | Wymagania niefunkcjonalne | ## Non-functional requirements (when they differ from the defaults) | UI po polsku, kod po angielsku, daty dd.MM.yyyy, Chrome i Safari (2 ostatnie wersje), formularze z etykietami i klawiatura |
| 27-30 | Inne ograniczenia | ## Other constraints | Jedna komenda startu po `pip install -r requirements.txt`, zero npm, HTMX jako jeden plik statyczny |

#### Keywords: Python 3.12, FastAPI, HTMX, Jinja2, SQLite, SQLAlchemy, Alembic, pytest, Playwright, uvicorn, GitHub Actions, a11y

### lista-lektur.md (135 lines)
Specyfikacja funkcjonalna aplikacji „Lista lektur”: jednoosobowa, lokalna aplikacja webowa do prowadzenia listy książek z półkami, notatkami, ocenami, filtrowaniem, eksportem CSV i statystykami. Zawiera model danych z regułami R1–R7, pełne API JSON, opis dwóch ekranów UI i kryteria akceptacji A1–A8.

#### Sections:
| Lines | Section | Anchor | Description |
|-------|--------|---------|------|
| 1-2 | Tytuł | # Lista lektur — specyfikacja | Nagłówek dokumentu |
| 3-11 | Cel i kontekst | ## 1. Cel i kontekst | Jeden użytkownik, lokalnie, bez kont; poza zakresem: księgarnie, okładki, rekomendacje, multi-user |
| 12-19 | Słownik | ## 2. Słownik | Definicje: Książka, Półka (M:N), Notatka, Status (3 wartości) |
| 20-21 | Model — nagłówek | ## 3. Model i reguły biznesowe | Wstęp do podsekcji modelu |
| 22-40 | Model: Książka | ### 3.1 Książka | Pola i walidacja (tytuł, autor, rok, status, ocena 1–5 tylko dla `przeczytana`), R1 duplikaty, R2 kasowanie oceny, R3 kaskada usuwania |
| 41-50 | Model: Półka | ### 3.2 Półka | Nazwa 1–60 znaków unikalna bez wielkości liter, R4 może być pusta, R5 kolejność alfabetyczna |
| 51-62 | Model: Notatka | ### 3.3 Notatka | Treść 1–2000 znaków, data dodania, R6 bez edycji, R7 od najnowszej |
| 63-83 | API (JSON) | ## 4. API (JSON) | Prefiks `/api`, 422/404, 13 endpointów: książki CRUD + filtry, półki, przypisanie półek, notatki, eksport CSV, statystyki |
| 84-88 | UI — zasady ogólne | ## 5. Interfejs użytkownika | SSR, odświeżanie fragmentami bez przeładowania, dwa ekrany |
| 89-99 | Ekran „Lista” | ### 5.1 Ekran „Lista” | Pasek filtrów (status, półka, szukanie 300 ms), tabela/karty, formularz dodawania, zmiana statusu na liście, statystyki w nagłówku |
| 100-109 | Ekran „Szczegóły” | ### 5.2 Ekran „Szczegóły” | Edycja w miejscu, gwiazdki (wstępna ocena w `czytam`), półki jako pola wyboru, notatki, usuwanie z potwierdzeniem |
| 110-115 | Zasady wspólne UI | ### 5.3 Zasady wspólne | Działa bez JS podstawowo, jedna kolumna < 640 px, błędy walidacji przy polu |
| 116-130 | Kryteria akceptacji | ## 6. Kryteria akceptacji (wysoki poziom) | A1–A8: CRUD przez API i UI, ocena, filtry łączone, półki, notatki, CSV, statystyki, testy + e2e |
| 131-135 | Kolejność prac | ## 7. Kolejność prac (sugerowana) | 3 etapy: szkielet + API książek + CI; półki, notatki, UI; filtry, CSV, statystyki, e2e, wydanie `v0.1.0` |

#### Keywords: książka, półka, notatka, status, ocena, duplikat, filtr, szukanie, eksport CSV, statystyki, HTMX, R1–R7, A1–A8

## UX/UI guidelines

Katalog `telesma/spec/ux_ui/` jest pusty — brak makiet, tokenów i rejestru linków. Zadania UI opierają się wyłącznie na opisie tekstowym w `lista-lektur.md` (sekcja 5).

## Documentation quality

- **Completeness**: 80% — wymagania funkcjonalne, model danych z walidacją, pełna lista endpointów API, kryteria akceptacji, stack, CI i uruchomienie są opisane. Brakuje: szczegółów obsługi błędów (kod odpowiedzi dla duplikatu, format listy błędów 422), reprezentacji wartości statusu w API/DB, miejsca zarządzania półkami i linku eksportu w UI, semantyki „edycji w miejscu”, zakresu działania bez JavaScriptu, zakresu e2e w CI. Brak wymagań wydajnościowych i bezpieczeństwa, ale dla lokalnej aplikacji jednego użytkownika nie są one potrzebne.
- **Unambiguity**: medium — większość reguł jest precyzyjna (zakresy pól, R1–R7, A1–A8), ale kilka miejsc zostawia wybór implementacyjny: „tabela lub lista kart”, „edycja w miejscu”, „w stopniu podstawowym” bez JS, kolejność alfabetyczna półek przy polskich znakach.
- **Consistency**: medium — jedna wyraźna sprzeczność: model (3.1, R2, A2) dopuszcza ocenę wyłącznie przy statusie `przeczytana`, a ekran „Szczegóły” (5.2) pozwala wystawić wstępną ocenę w statusie `czytam`. Poza tym dokumenty są spójne ze sobą i z wytycznymi technicznymi.
- **Project size**: small — jeden proces, 3 encje, 13 endpointów, 2 ekrany, brak integracji zewnętrznych, brak logowania.
- **Topic gaps**:
  - reprezentacja statusu (wartości polskie z backticków vs kody angielskie w kodzie i API)
  - kod odpowiedzi i format błędu dla duplikatu książki (R1) oraz duplikatu nazwy półki
  - UI zarządzania półkami (dodanie/usunięcie) i link do eksportu CSV — API je ma, ekrany ich nie opisują
  - semantyka edycji w miejscu na ekranie „Szczegóły” (zapis per pole vs przycisk)
  - zakres działania bez JavaScriptu i sposób potwierdzania usunięcia bez JS
  - strefa czasowa prezentacji dat (UTC w bazie, dd.MM.yyyy w UI)
  - e2e Playwright: tylko lokalnie czy także w CI, które przeglądarki
  - szczegóły CSV: separator kolumn, kodowanie, nagłówek
- **Recommendation**: specyfikacja wystarcza do zbudowania planu po rozstrzygnięciu sprzeczności dotyczącej oceny i potwierdzeniu kilku założeń; nie wymaga uzupełniania przed startem.

<!-- TELESMA_SPEC_CHECKSUMS (generated by telesma.sh — do not edit)
886525541 1331 telesma/spec/TECHNICAL_GUIDELINES.md
509265278 6282 telesma/spec/lista-lektur.md
-->
