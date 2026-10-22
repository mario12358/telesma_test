# Changelog

## v0.1.0 — 2026-10-22

Pierwsze wydanie.

### Dodane

- Książki: dodawanie, edycja, zmiana statusu, usuwanie; walidacja tytułu, autora i roku;
  odrzucanie duplikatów (ten sam tytuł i autor bez względu na wielkość liter i spacje).
- Ocena 1–5 przy statusie „czytam” i „przeczytana”; zmiana statusu na „do przeczytania” kasuje ocenę.
- Półki: dodawanie, usuwanie, przypisywanie książki do wielu półek, licznik książek.
- Notatki: dodawanie i usuwanie, wyświetlane od najnowszej, bez edycji.
- Ekran „Lista”: formularz dodawania, zmiana statusu jednym kliknięciem, filtry statusu, półki
  i szukania (łączone, zapisane w adresie), sekcja „Półki”.
- Ekran „Szczegóły”: edycja pól w miejscu, ocena gwiazdkami, półki jako pola wyboru, notatki.
- Eksport wszystkich książek do CSV.
- Statystyki w nagłówku: liczba książek w każdym statusie i średnia ocena przeczytanych.
- API JSON dla wszystkich operacji (`/api`).
- Działanie bez JavaScriptu (formularze), układ jednokolumnowy poniżej 640 px.
- Ochrona przed zapisami wysyłanymi z innych witryn (CSRF).
