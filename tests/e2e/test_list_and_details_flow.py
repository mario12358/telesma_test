import re

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e


def _add_book(page: Page, title: str, author: str, year: str = "") -> None:
    page.get_by_label("Tytuł", exact=True).fill(title)
    page.get_by_label("Autor", exact=True).fill(author)
    page.get_by_label("Rok", exact=True).fill(year)
    page.get_by_role("button", name="Dodaj", exact=True).click()


def _row(page: Page, title: str):
    return page.get_by_role("row").filter(has=page.get_by_role("link", name=title, exact=True))


# specky: crit 01M5JNJCTXK9TDHGTB20FEZFYF
def test_book_lifecycle_through_list_and_details(app_url: str, confirm_dialogs: Page):
    page = confirm_dialogs
    page.goto(app_url)

    _add_book(page, "Lalka", "Bolesław Prus", "1890")
    row = _row(page, "Lalka")
    expect(row).to_be_visible()
    expect(page.get_by_label("Tytuł", exact=True)).to_have_value("")

    row.get_by_role("button", name="czytam").click()
    expect(_row(page, "Lalka").get_by_role("button", name="czytam")).to_have_attribute(
        "aria-pressed", "true"
    )

    page.get_by_text("Półki (0)").click()
    page.get_by_label("Nazwa nowej półki").fill("Klasyka")
    page.get_by_role("button", name="Dodaj półkę").click()
    expect(page.locator("#shelves-section li")).to_have_count(1)

    _row(page, "Lalka").get_by_role("link", name="Lalka").click()
    expect(page).to_have_url(re.compile(r"/books/\d+$"))
    expect(page.get_by_role("heading", level=1)).to_have_text("Lalka")

    author = page.get_by_label("Autor", exact=True)
    author.fill("B. Prus")
    author.press("Tab")
    expect(page.locator("#field-author").get_by_role("status")).to_have_text("Zapisano")

    page.locator("label[for=rating-4]").click()
    expect(page.locator("#rating-4")).to_be_checked()

    page.get_by_label("Klasyka").check()
    expect(page.locator("#book-shelves").get_by_role("status")).to_have_text("Zapisano")

    page.get_by_label("Nowa notatka").fill("Świetny portret epoki")
    page.get_by_role("button", name="Dodaj notatkę").click()
    expect(page.locator("#notes-section li")).to_have_count(1)
    expect(page.locator("#notes-section li").first).to_contain_text("Świetny portret epoki")

    page.reload()
    expect(page.get_by_label("Autor", exact=True)).to_have_value("B. Prus")
    expect(page.locator("#rating-4")).to_be_checked()
    expect(page.get_by_label("Klasyka")).to_be_checked()

    page.locator("#notes-section").get_by_role("button", name=re.compile("Usuń notatkę")).click()
    expect(page.locator("#notes-section")).to_contain_text("Brak notatek.")

    page.get_by_role("button", name="Usuń książkę").click()
    expect(page).to_have_url(f"{app_url}/")
    expect(page.get_by_text("Brak książek do wyświetlenia.")).to_be_visible()


# specky: crit 01M5JNJCCBFG5JC7MES61ZZ3T7
def test_adding_a_book_does_not_navigate_the_page(app_url: str, page: Page):
    page.goto(app_url)
    page.evaluate("window.__marker = 'still-here'")
    _add_book(page, "Faraon", "Bolesław Prus")
    expect(_row(page, "Faraon")).to_be_visible()
    assert page.evaluate("window.__marker") == "still-here"
    assert page.url == f"{app_url}/"


def test_validation_error_appears_next_to_the_field(app_url: str, page: Page):
    page.goto(app_url)
    _add_book(page, "Lalka", "Bolesław Prus")
    expect(_row(page, "Lalka")).to_be_visible()
    # htmx swaps the out-of-band list before the form itself: wait for the fresh, empty form.
    expect(page.get_by_label("Tytuł", exact=True)).to_have_value("")
    _add_book(page, " lalka ", "bolesław prus")
    error = page.locator("#new-title-error")
    expect(error).to_contain_text("już na liście")
    expect(page.get_by_label("Tytuł", exact=True)).to_have_attribute("aria-invalid", "true")


def test_details_reject_invalid_year_at_the_field(app_url: str, page: Page):
    page.goto(app_url)
    _add_book(page, "Lalka", "Bolesław Prus", "1890")
    _row(page, "Lalka").get_by_role("link", name="Lalka").click()
    year = page.get_by_label("Rok", exact=True)
    year.fill("1200")
    year.press("Tab")
    expect(page.locator("#detail-year-error")).to_contain_text("Rok musi być z zakresu 1450")
    page.reload()
    expect(page.get_by_label("Rok", exact=True)).to_have_value("1890")


def test_book_can_be_added_with_the_keyboard_only(app_url: str, page: Page):
    page.goto(app_url)
    page.get_by_label("Tytuł", exact=True).focus()
    page.keyboard.type("Wiedźmin")
    page.keyboard.press("Tab")
    page.keyboard.type("Andrzej Sapkowski")
    page.keyboard.press("Enter")
    expect(_row(page, "Wiedźmin")).to_be_visible()


# specky: crit 01M5JNJCCBDSJ3G1P8HK42H9Z4
def test_narrow_screen_shows_one_column_without_horizontal_scroll(app_url: str, page: Page):
    page.set_viewport_size({"width": 400, "height": 800})
    page.goto(app_url)
    _add_book(
        page, "Bardzo długi tytuł książki o czymś ważnym", "Autor Z Długim Nazwiskiem", "2001"
    )
    expect(page.locator("#book-list tbody tr")).to_have_count(1)
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    first_cell, second_cell = (
        page.locator("#book-list tbody td").nth(0),
        page.locator("#book-list tbody td").nth(1),
    )
    assert first_cell.bounding_box()["y"] < second_cell.bounding_box()["y"]
