# Lista lektur — specyfikacja

## 1. Cel i kontekst

Mała aplikacja webowa dla jednego użytkownika do prowadzenia własnej listy lektur: co chcę
przeczytać, co czytam, co przeczytałem i co o tym myślę. Działa lokalnie (jeden proces, jeden
plik bazy), bez logowania i bez kont. Ma być szybka w obsłudze z klawiatury i czytelna na
telefonie.

Nie budujemy: integracji z księgarniami, importu okładek, rekomendacji, trybu wielu użytkowników.

## 2. Słownik

- **Książka** — pozycja na liście: tytuł, autor, rok wydania, status, ocena, notatki.
- **Półka** — nazwana kolekcja książek (np. „Fantastyka”, „Do pracy”). Książka może leżeć na
  wielu półkach albo na żadnej.
- **Notatka** — krótki wpis tekstowy przypięty do książki, z datą dodania.
- **Status** — jedna z trzech wartości: `do przeczytania`, `czytam`, `przeczytana`.

## 3. Model i reguły biznesowe

### 3.1 Książka

| Pole | Typ | Reguły |
|------|-----|--------|
| id | liczba | nadawany przez system |
| tytuł | tekst | wymagany, 1–200 znaków, po przycięciu spacji |
| autor | tekst | wymagany, 1–120 znaków |
| rok | liczba | opcjonalny; jeśli podany: 1450 ≤ rok ≤ bieżący rok + 1 |
| status | enum | wymagany, domyślnie `do przeczytania` |
| ocena | liczba | opcjonalna, 1–5; **dozwolona wyłącznie gdy status = `przeczytana`** |
| utworzono / zmieniono | data-czas | nadawane przez system, UTC |

Reguły:

- R1. Duplikat = ta sama para (tytuł, autor) po normalizacji (małe litery, pojedyncze spacje).
  Dodanie duplikatu jest odrzucane z czytelnym komunikatem.
- R2. Zmiana statusu na inny niż `przeczytana` kasuje ocenę.
- R3. Usunięcie książki usuwa jej notatki i zdejmuje ją ze wszystkich półek.

### 3.2 Półka

| Pole | Typ | Reguły |
|------|-----|--------|
| id | liczba | nadawany przez system |
| nazwa | tekst | wymagana, 1–60 znaków, unikalna bez względu na wielkość liter |

- R4. Półka może być pusta.
- R5. Kolejność półek na liście: alfabetyczna.

### 3.3 Notatka

| Pole | Typ | Reguły |
|------|-----|--------|
| id | liczba | nadawany przez system |
| książka | relacja | wymagana |
| treść | tekst | wymagana, 1–2000 znaków |
| dodano | data-czas | nadawane przez system |

- R6. Notatek nie edytujemy — można je tylko dodać i usunąć.
- R7. Notatki wyświetlamy od najnowszej.

## 4. API (JSON)

Wszystkie odpowiedzi w JSON, błędy walidacji jako `422` z listą pól i komunikatów, brak zasobu
jako `404`. Prefiks `/api`.

| Metoda i ścieżka | Działanie |
|------------------|-----------|
| `GET /api/books` | lista; filtry `status`, `shelf` (id), `q` (fragment tytułu lub autora, bez wielkości liter); sortowanie domyślne: `zmieniono` malejąco |
| `POST /api/books` | dodanie (R1) |
| `GET /api/books/{id}` | szczegóły wraz z półkami i notatkami |
| `PATCH /api/books/{id}` | zmiana dowolnych pól (R2) |
| `DELETE /api/books/{id}` | usunięcie (R3) |
| `GET /api/shelves` | lista półek z liczbą książek (R5) |
| `POST /api/shelves` | dodanie półki |
| `DELETE /api/shelves/{id}` | usunięcie półki |
| `PUT /api/books/{id}/shelves` | ustawienie pełnej listy półek książki (lista id) |
| `POST /api/books/{id}/notes` | dodanie notatki |
| `DELETE /api/notes/{id}` | usunięcie notatki |
| `GET /api/export.csv` | eksport wszystkich książek do CSV: tytuł, autor, rok, status, ocena, półki (rozdzielone `;`) |
| `GET /api/stats` | liczba książek w każdym statusie oraz średnia ocena przeczytanych (zaokrąglona do 0,1) |

## 5. Interfejs użytkownika

Interfejs renderowany po stronie serwera, odświeżany fragmentami (bez pełnego przeładowania
strony przy dodawaniu, zmianie statusu i filtrowaniu). Dwa ekrany:

### 5.1 Ekran „Lista”

- Pasek filtrów: status (przyciski „wszystkie / do przeczytania / czytam / przeczytana”), półka
  (lista rozwijana), pole szukania `q` działające w trakcie pisania (z opóźnieniem ok. 300 ms).
- Tabela lub lista kart: tytuł, autor, rok, status, ocena w gwiazdkach, półki jako etykiety.
- Formularz „Dodaj książkę” nad listą: tytuł, autor, rok. Po dodaniu formularz się czyści,
  nowa pozycja pojawia się na górze bez przeładowania.
- Zmiana statusu bezpośrednio na liście (jedno kliknięcie, bez wchodzenia w szczegóły).
- Kliknięcie tytułu prowadzi do ekranu „Szczegóły”.
- Nagłówek pokazuje statystyki z `GET /api/stats`.

### 5.2 Ekran „Szczegóły”

- Wszystkie pola książki z możliwością edycji w miejscu.
- Ocena gwiazdkami 1–5. Użytkownik może wystawić **wstępną ocenę już w statusie `czytam`**;
  po zmianie statusu na `przeczytana` ocena zostaje.
- Półki: lista pól wyboru (zaznacz/odznacz zapisuje od razu).
- Notatki: pole dodania na górze, lista poniżej od najnowszej (R7), przycisk usunięcia przy
  każdej.
- Przycisk „Usuń książkę” z potwierdzeniem.

### 5.3 Zasady wspólne

- Działa bez JavaScriptu w stopniu podstawowym (formularze zwykłe), z JavaScriptem bez przeładowań.
- Układ jednokolumnowy poniżej 640 px szerokości.
- Komunikaty błędów walidacji pojawiają się przy polu, nie jako alert.

## 6. Kryteria akceptacji (wysoki poziom)

- A1. Dodanie, edycja, zmiana statusu i usunięcie książki działają przez API i z interfejsu,
  zgodnie z R1–R3.
- A2. Ocenę da się zapisać tylko w sytuacjach dozwolonych przez model (3.1), a jej wartości
  spoza 1–5 są odrzucane.
- A3. Filtry statusu, półki i szukania można łączyć; wynik zgadza się z API.
- A4. Półki: dodanie, usunięcie, przypisanie książki do wielu półek, licznik książek.
- A5. Notatki: dodanie i usunięcie, kolejność od najnowszej, brak edycji.
- A6. Eksport CSV otwiera się w arkuszu kalkulacyjnym i zawiera wszystkie książki z kolumnami
  z sekcji 4.
- A7. Statystyki w nagłówku zgadzają się z zawartością bazy po każdej operacji.
- A8. Testy automatyczne pokrywają reguły R1–R7 i każdy punkt API; test e2e przechodzi przez
  ekran „Lista” i „Szczegóły”.

## 7. Kolejność prac (sugerowana)

1. Szkielet, baza, API książek, testy, CI.
2. Półki i notatki, interfejs obu ekranów.
3. Szukanie i filtry łączone, eksport CSV, statystyki, test e2e, pierwsze wydanie `v0.1.0`.
