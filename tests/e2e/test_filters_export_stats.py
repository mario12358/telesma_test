import csv
import io
import re

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e


def _seed(page: Page, app_url: str) -> int:
    """Library seeded through the JSON API; returns the id of the «Fantastyka» shelf."""
    api = page.request
    shelf_id = api.post(f"{app_url}/api/shelves", data={"name": "Fantastyka"}).json()["id"]
    books = [
        ("Lalka", "Bolesław Prus", "reading", True),
        ("Faraon", "Bolesław Prus", "read", False),
        ("Wiedźmin", "Andrzej Sapkowski", "reading", True),
        ("Prusy Wschodnie", "Ktoś", "reading", False),
        ("Narrenturm", "Andrzej Sapkowski", "to_read", True),
    ]
    for title, author, status, on_shelf in books:
        book = api.post(
            f"{app_url}/api/books", data={"title": title, "author": author, "status": status}
        )
        if on_shelf:
            api.put(
                f"{app_url}/api/books/{book.json()['id']}/shelves", data={"shelf_ids": [shelf_id]}
            )
    return shelf_id


def _listed_titles(page: Page) -> list[str]:
    return sorted(page.locator("#book-list tbody tr td:first-child a").all_inner_texts())


def _api_titles(page: Page, app_url: str, params: dict[str, str]) -> list[str]:
    response = page.request.get(f"{app_url}/api/books", params=params)
    return sorted(book["title"] for book in response.json())


def _stat(page: Page, name: str):
    return page.locator(f'#stats [data-stat="{name}"]')


# specky: crit 01M5JNJCK89CNSWP5DT8SNJBCD
def test_combined_filters_show_the_same_books_as_the_api(app_url: str, page: Page):
    shelf_id = _seed(page, app_url)
    page.goto(app_url)

    page.locator("label[for=filter-status-reading]").click()
    page.get_by_label("Półka").select_option(label="Fantastyka")
    page.get_by_label("Szukaj w tytule lub autorze").fill("prus")

    expected = _api_titles(
        page, app_url, {"status": "reading", "shelf": str(shelf_id), "q": "prus"}
    )
    assert expected == ["Lalka"]
    expect(page.locator("#book-list tbody tr")).to_have_count(1)
    assert _listed_titles(page) == expected
    expect(page).to_have_url(re.compile(r"status=reading.*shelf=\d+.*q=prus"))

    page.reload()
    expect(page.locator("#book-list tbody tr")).to_have_count(1)
    expect(page.locator("#filter-status-reading")).to_be_checked()
    expect(page.get_by_label("Szukaj w tytule lub autorze")).to_have_value("prus")


def test_search_while_typing_narrows_the_list(app_url: str, page: Page):
    _seed(page, app_url)
    page.goto(app_url)
    page.get_by_label("Szukaj w tytule lub autorze").press_sequentially("sapk", delay=50)
    expect(page.locator("#book-list tbody tr")).to_have_count(2)
    assert _listed_titles(page) == ["Narrenturm", "Wiedźmin"]


# specky: crit 01M5JNJC6S8FX7X6XGG4SB2B8C
def test_csv_export_downloads_every_book(app_url: str, page: Page):
    _seed(page, app_url)
    page.goto(app_url)
    with page.expect_download() as download_info:
        page.get_by_role("link", name="Eksport CSV").click()
    download = download_info.value
    assert download.suggested_filename == "lektury.csv"
    with open(download.path(), encoding="utf-8-sig", newline="") as exported:
        rows = list(csv.reader(io.StringIO(exported.read())))
    assert rows[0] == ["tytuł", "autor", "rok", "status", "ocena", "półki"]
    assert sorted(row[0] for row in rows[1:]) == sorted(
        ["Lalka", "Faraon", "Wiedźmin", "Prusy Wschodnie", "Narrenturm"]
    )


# specky: crit 01M5JNJC9ERY4G58GS31GB52B3
def test_header_stats_follow_every_change_without_reload(app_url: str, page: Page):
    page.on("dialog", lambda dialog: dialog.accept())
    page.goto(app_url)
    page.evaluate("window.__marker = 'same-page'")

    page.get_by_label("Tytuł", exact=True).fill("Lalka")
    page.get_by_label("Autor", exact=True).fill("Bolesław Prus")
    page.get_by_role("button", name="Dodaj", exact=True).click()
    expect(_stat(page, "to_read")).to_have_text("1")

    page.locator("#book-list tbody tr").first.get_by_role("button", name="przeczytana").click()
    expect(_stat(page, "read")).to_have_text("1")
    expect(_stat(page, "to_read")).to_have_text("0")
    assert page.evaluate("window.__marker") == "same-page"

    page.get_by_role("link", name="Lalka").click()
    page.locator("label[for=rating-5]").click()
    expect(_stat(page, "average_rating")).to_have_text("5,0")

    page.get_by_role("button", name="Usuń książkę").click()
    expect(page).to_have_url(f"{app_url}/")
    expect(_stat(page, "read")).to_have_text("0")
    expect(_stat(page, "average_rating")).to_have_text("—")
    assert page.request.get(f"{app_url}/api/stats").json() == {
        "to_read": 0,
        "reading": 0,
        "read": 0,
        "average_rating": None,
    }
