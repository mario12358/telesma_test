import pytest

from app.templating import books_count
from tests.html import label_for, parse_html

HX = {"HX-Request": "true"}


def _api_shelf(client, name: str) -> int:
    return client.post("/api/shelves", json={"name": name}).json()["id"]


def _api_book(client, title: str = "Lalka") -> int:
    return client.post("/api/books", json={"title": title, "author": "Bolesław Prus"}).json()["id"]


def _shelf_names(section) -> list[str]:
    return [item.find("span", class_="shelf-name").text for item in section.find_all("li")]


def test_list_page_has_collapsible_shelves_section_with_counts(client):
    shelf_id = _api_shelf(client, "Fantastyka")
    _api_shelf(client, "Do pracy")
    book_id = _api_book(client)
    client.put(f"/api/books/{book_id}/shelves", json={"shelf_ids": [shelf_id]})

    document = parse_html(client.get("/").text)
    section = document.by_id("shelves-section")

    assert section.find("details") is not None
    assert section.find("summary").text == "Półki (2)"
    assert _shelf_names(section) == ["Do pracy", "Fantastyka"]
    assert (
        section.by_id(f"shelf-{shelf_id}").find("span", class_="shelf-count").text == "(1 książka)"
    )
    assert label_for(document, "shelf-name").text == "Nazwa nowej półki"


# specky: crit 01M5JNJCH7S65DEFPAQ8S57P7V
def test_htmx_add_shelf_returns_open_section_with_new_shelf(client):
    response = client.post("/shelves", data={"name": "Fantastyka"}, headers=HX)
    document = parse_html(response.text)
    section = document.by_id("shelves-section")
    assert response.status_code == 200
    assert "open" in section.find("details").attrs
    assert _shelf_names(section) == ["Fantastyka"]
    assert section.by_id("shelf-name").get("value") == ""
    assert document.by_id("book-list").get("hx-swap-oob") == "true"


def test_add_shelf_form_targets_the_section(client):
    form = parse_html(client.get("/").text).by_id("add-shelf-form")
    assert (form.get("hx-post"), form.get("hx-target"), form.get("hx-swap")) == (
        "/shelves",
        "#shelves-section",
        "outerHTML",
    )


# specky: crit 01M5JNJCH7DTP27AA4PS57K9Z6
def test_duplicate_shelf_name_shows_message_next_to_the_name_field(client):
    _api_shelf(client, "Fantastyka")
    response = client.post("/shelves", data={"name": "FANTASTYKA"}, headers=HX)
    section = parse_html(response.text).by_id("shelves-section")
    name_input = section.by_id("shelf-name")
    assert response.status_code == 422
    assert name_input.get("aria-invalid") == "true"
    assert section.by_id("shelf-name-error").text == "Półka o tej nazwie już istnieje."
    assert name_input.get("value") == "FANTASTYKA"


def test_add_shelf_without_javascript_redirects(client):
    response = client.post("/shelves", data={"name": "Klasyka"}, follow_redirects=False)
    assert (response.status_code, response.headers["location"]) == (303, "/")
    assert [shelf["name"] for shelf in client.get("/api/shelves").json()] == ["Klasyka"]


# specky: crit 01M5JNJCH7TBY47QETRQDX28AY
def test_delete_button_asks_for_confirmation_and_keeps_books(client):
    shelf_id = _api_shelf(client, "Fantastyka")
    book_id = _api_book(client)
    client.put(f"/api/books/{book_id}/shelves", json={"shelf_ids": [shelf_id]})
    button = parse_html(client.get("/").text).by_id(f"shelf-{shelf_id}").find("button")
    assert button.get("hx-confirm") == "Usunąć półkę «Fantastyka»? Książki zostaną na liście."
    assert button.get("hx-post") == f"/shelves/{shelf_id}/delete"

    response = client.post(f"/shelves/{shelf_id}/delete", headers=HX)

    document = parse_html(response.text)
    assert _shelf_names(document.by_id("shelves-section")) == []
    row = document.by_id(f"book-{book_id}")
    assert "Fantastyka" not in row.text
    assert [book["id"] for book in client.get("/api/books").json()] == [book_id]


def test_delete_without_javascript_uses_a_confirmation_page(client):
    shelf_id = _api_shelf(client, "Fantastyka")
    confirm = client.get(f"/shelves/{shelf_id}/delete")
    form = parse_html(confirm.text).find("form", method="post")
    assert confirm.status_code == 200
    assert form.get("action") == f"/shelves/{shelf_id}/delete"

    response = client.post(f"/shelves/{shelf_id}/delete", follow_redirects=False)

    assert (response.status_code, response.headers["location"]) == (303, "/")
    assert client.get("/api/shelves").json() == []


def test_confirmation_page_for_missing_shelf_is_404(client):
    assert client.get("/shelves/999/delete").status_code == 404


@pytest.mark.parametrize(
    ("count", "text"),
    [
        (0, "0 książek"),
        (1, "1 książka"),
        (2, "2 książki"),
        (5, "5 książek"),
        (12, "12 książek"),
        (22, "22 książki"),
    ],
)
def test_books_count_uses_polish_plural_forms(count, text):
    assert books_count(count) == text
