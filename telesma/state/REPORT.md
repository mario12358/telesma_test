# telesma/state/REPORT.md - Project execution report

<!-- This file goes IN FULL into the startup prompt of every session. Two kinds of sections:  -->
<!--   • current state (Summary) — OVERWRITE it, it is meant to be one up-to-date description; -->
<!--   • chronicle (Test status, Task history, Change history, Problem log,                    -->
<!--     Visual artifacts) — APPEND one entry; older ones rotate to telesma/state/REPORT_ARCHIVE.md   -->
<!--     at startup (Test status: the 3 latest runs).                                          -->
<!-- Do not create your own `## ` sections for session summaries — EVERY `## ` section outside -->
<!-- this template is ad-hoc and only the 3 newest of them are kept.                           -->
<!-- Rotation moves WHOLE entries, multi-line ones too. An entry must have a recognisable      -->
<!-- start (a table row, `### …`, `- [date] …`, `- **Name …**`), and a paragraph glued        -->
<!-- under an entry counts as its continuation and goes to the archive together with it.      -->

## Summary

- **Start**: 2026-10-22
- **Status**: Completed
- **Progress**: 18/18 tasks completed (Phase 1–4 ✅), release `v0.1.0`

## Test status

<!--
The table is the current state — REPLACE the numbers, do not add a second table.
Above the table, one paragraph per full-suite run, opened with bold text carrying the date:

**Regression after Phase 12 (2026-08-20) — GREEN:** backend `pytest -q` 340/0, frontend 210/0.
Compared with 328/205 after Phase 11: +12 backend tests. Tag `telesma/phase-12`.

The date in the first line is MANDATORY — rotation uses it to tell which runs to keep
(the 3 latest) and which to move to telesma/state/REPORT_ARCHIVE.md. A paragraph without a date
is treated as a continuation of the run above it. A block without a date stays in the file
forever and grows in the prompt of every session.
-->

**Regression after Phase 1 (2026-10-22) — GREEN:** `pytest -q` 85/0, `ruff check .` clean.
First full-suite run of the project; CI job `test` green on every PR (#1–#4).

**Regression after Phase 2 (2026-10-22) — GREEN:** `pytest -q` 197/0, e2e `pytest -m e2e --browser-channel chrome` 6/0, `ruff check .` clean.
Compared with 85 after Phase 1: +112 tests (shelves/notes API, UI shell, both screens, e2e).

**Regression after Phase 3 (2026-10-22) — GREEN:** `pytest -q` 240/0, e2e 10/0 (Chrome), `ruff check .` clean.
Compared with 197 + 6 after Phase 2: +43 tests (filters, CSV export, stats) and +4 e2e.

| Metric | Value |
|--------|-------|
| Total tests | 250 |
| Pass | 250 |
| Fail | 0 |
| Skip | 0 |
| Last run | 2026-10-22 |

## Task history

| Task | Status | Tests | Tries | Commit | Time |
|------|--------|-------|-------|--------|------|
| 1.1 Szkielet i konwencje | ✅ | 9/9 | 1 | bb7dab0 (PR #1) | 2026-10-22 |
| 1.2 Warstwa bazy | ✅ | 15/15 | 1 | 76d8eb5 (PR #2) | 2026-10-22 |
| 1.3 Schemat i modele ORM | ✅ | 28/28 | 1 | PR #3 | 2026-10-22 |
| 1.4 Schematy + BookService | ✅ | 67/67 | 1 | a12febf (PR #4) | 2026-10-22 |
| 1.5 Router `/api/books` | ✅ | 85/85 | 1 | PR #5 | 2026-10-22 |
| 2.1 Półki — serwis i API | ✅ | 100/100 | 1 | PR #6 | 2026-10-22 |
| 2.2 Notatki — serwis i API | ✅ | 112/112 | 1 | PR #7 | 2026-10-22 |
| 2.3 Powłoka UI | ✅ | 130/130 | 1 | PR #8 | 2026-10-22 |
| 2.4 Ekran «Lista» | ✅ | 148/148 | 1 | PR #9 | 2026-10-22 |
| 2.5 Sekcja «Półki» | ✅ | 162/162 | 1 | PR #10 | 2026-10-22 |
| 2.6 Ekran «Szczegóły» | ✅ | 183/183 | 1 | PR #11 | 2026-10-22 |
| 2.7 Półki i notatki w szczegółach | ✅ | 197/197 | 1 | PR #12 | 2026-10-22 |
| 2.8 E2E fazy 2 | ✅ | 197 + 6 e2e | 2 | PR #13 | 2026-10-22 |
| 3.1 Pasek filtrów | ✅ | 215 + 6 e2e | 2 | PR #14 | 2026-10-22 |
| 3.2 Eksport CSV | ✅ | 222/222 | 1 | PR #15 | 2026-10-22 |
| 3.3 Statystyki | ✅ | 240/240 | 1 | PR #16 | 2026-10-22 |
| 3.4 E2E fazy 3 | ✅ | 240 + 10 e2e | 1 | PR #17 | 2026-10-22 |
| 4.1 Wydanie v0.1.0 | ✅ | 240 + 10 e2e | 1 | PR #18, tag `v0.1.0` | 2026-10-22 |

## Change history

<!--
Entries added by Telesma after processing a file from telesma/changes/.
Entry format (one ### per change):

### YYYY-MM-DD <file-name>.md
- **Kind**: bug | correction | feature
- **Bug source**: [bugs only: task X.Y that built it | unknown]
- **Detected by**: [bugs only: test | scenario | review | telesma | owner | production]
- **Priority**: critical | normal
- **Affects**: [the affects field from the frontmatter, or "general"]
- **Summary**: [1-2 sentences on what changes and why]
- **Modified pending tasks**: [list of numbers, e.g. 4.2, 5.1] or "none"
- **New rework phase**: [e.g. Phase 6.Z1 with 3 tasks] or "none"
- **New tasks**: [list of numbers, e.g. 7.4, 7.5] or "none"

The change's source file lives in telesma/changes/processed/<file-name>.md (audit trail in git).
-->

## Visual artifacts

<!--
Section filled in ONLY when the `## Visual artifacts` section in telesma/config.md has
`Screenshots: yes` or `Recordings: yes`. Full procedure: section 0.5 of the instructions.

Row format:
| Phase | Type | ID | Artifact file | Spec source |
|-------|------|----|--------------:|-------------|
| 1     | screen | B1_ProjectOverview | telesma/artifacts/screens/B1_ProjectOverview.png | telesma/spec/ux_ui/screens-b1-b2.jsx:52-200 |
| 1     | flow   | step-1             | telesma/artifacts/flows/step-1-sign-up.webm      | telesma/spec/APP_FLOW.md:11-30 |

Info warnings (no APP_FLOW.md despite Recordings: yes, no flow_files, etc.) go
below the table with the prefix `> ⚠ Info:` so the user can see what happened "silently".
-->

| Phase | Type | ID | Artifact file | Spec source |
|-------|------|----|---------------|-------------|
| | | | | |

## Problem log

<!-- Format: [date] Task X.X: problem description - fix/status -->
<!-- We do NOT keep a list of changed files — git knows it better: git log --stat -->

- [2026-10-22] Task 1.1: kontrola hygiene ostrzega o `app/static/htmx.min.js` (minified bundle, fingerprint `579606aa6fb6`) — świadomie: TECHNICAL_GUIDELINES.md:30 wymaga HTMX jako jednego pliku statycznego bez npm; nie dodano wyjątku.
- [2026-10-22] Task 1.1: krok `playwright install --with-deps chromium` w CI trwał ~10 min — zastąpiony preinstalowanym Chrome runnera (`--browser-channel chrome`), CI ~20 s.
- [2026-10-22] Task 1.2: mutacja reguły (`foreign_keys=OFF`) zablokowana przez klasyfikator auto mode — test sprawdza wartość 1, a domyślna w SQLite to 0, więc nie przejdzie bez pragmy; mutacji nie wykonano.
- [2026-10-22] Task 1.4: rebase gałęzi po squash-merge poprzedniego PR zmienił SHA i status `Telesma: checks (local)` zgłosił brak dowodu — `git commit --amend --no-edit` + `--force-with-lease`; kolejne gałęzie zakładane od `origin/main` po scaleniu poprzedniego PR.
- [2026-10-22] Tag `telesma/phase-1`: audyt OSV zablokował `certifi 2026.7.22` (GHSA-6q48-6c7w-9gw2, krytyczna) — podbito do 2026.10.19 oraz `opentelemetry-api` do 1.45.1 (PR #6); tag założony po scaleniu.
- [2026-10-22] Tag `telesma/phase-1`: dead-entry ostrzegał o `status_label` bez wywołań — podłączony jako filtr Jinja w 2.3.
- [2026-10-22] Task 2.6: SAST ostrzegał o atrybutach wstawianych jako gotowy ciąg (`{{ hx_attrs }}`) — przepisane na jawne atrybuty w cudzysłowach (PR #11).
- [2026-10-22] Tag `telesma/phase-2`: dead-entry zgłosił 9 tras widoków «bez klienta» (fingerprinty 842e6d99bc7d, 22c86514cd9d, 8c3bd41c62a1, 130c5330f4ea, 6e9bed5954fe, c86483257381, 38240eec6a2f) — fałszywy alarm: szablony Jinja wołają je ścieżkami z `{{ id }}`, pokryte testami widoków i e2e; bez wyjątku w CHECK_EXCEPTIONS.md (decyzja człowieka).
- [2026-10-22] Task 4.1: smoke test jednej komendy startu (`uvicorn app.main:app` z `LEKTURY_DB_PATH` w zagnieżdżonym katalogu) — baza utworzona, `GET /` 200, `/api/stats` OK.
- [2026-10-22] Task 3.1: e2e — `get_by_label("Autor")` dopasowywał też «Szukaj w tytule lub autorze» (tryb ścisły) → `exact=True`.
- [2026-10-22] Task 2.8: drugi zapis w e2e wypełniał formularz przed podmianą HTMX po pierwszym — test czeka na wiersz (`expect(...).to_be_visible()`) przed kolejną akcją.
