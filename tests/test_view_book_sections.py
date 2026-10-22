import re

import pytest

from tests.html import label_for, parse_html

HX = {"HX-Request": "true"}
DATE_TIME = re.compile(r"^\d{2}\.\d{2}\.\d{4} \d{2}:\d{2}$")


def _api_book(client, title: str = "Lalka") -> int:
    return client.post("/api/books", json={"title": title, "author": "Bolesław Prus"}).json()["id"]


def _api_shelf(client, name: str) -> int:
    return client.post("/api/shelves", json={"name": name}).json()["id"]


def _detail(client, book_id: int):
    return parse_html(client.get(f"/books/{book_id}").text)


def _checked_shelves(document) -> list[str]:
    form = document.by_id("book-shelves")
    return [
        label_for(document, box.get("id")).text
        for box in form.find_all("input", type="checkbox")
        if "checked" in box.attrs
    ]


def _note_texts(section) -> list[str]:
    return [item.find("p", class_="note-content").text for item in section.find_all("li")]


def test_detail_lists_every_shelf_as_labelled_checkbox(client):
    book_id = _api_book(client)
    for name in ("Fantastyka", "Do pracy"):
        _api_shelf(client, name)
    document = _detail(client, book_id)
    boxes = document.by_id("book-shelves").find_all("input", type="checkbox")
    assert [label_for(document, box.get("id")).text for box in boxes] == ["Do pracy", "Fantastyka"]
    assert _checked_shelves(document) == []
    assert boxes[0].get("hx-post") == f"/books/{book_id}/shelves"
    assert boxes[0].get("hx-trigger") == "change"


# specky: crit 01M5JNJCQE7A0ZQDQNNA42SX0S
def test_checking_a_shelf_saves_immediately_and_survives_reload(client):
    book_id = _api_book(client)
    fantasy = _api_shelf(client, "Fantastyka")
    _api_shelf(client, "Do pracy")

    response = client.post(
        f"/books/{book_id}/shelves", data={"shelf_ids": [str(fantasy)]}, headers=HX
    )

    fragment = parse_html(response.text)
    assert response.status_code == 200
    assert fragment.by_id("book-shelves").find("p", class_="saved").text == "Zapisano"
    assert _checked_shelves(_detail(client, book_id)) == ["Fantastyka"]


def test_unchecking_the_last_shelf_clears_the_list(client):
    book_id = _api_book(client)
    shelf_id = _api_shelf(client, "Fantastyka")
    client.put(f"/api/books/{book_id}/shelves", json={"shelf_ids": [shelf_id]})
    client.post(f"/books/{book_id}/shelves", data={}, headers=HX)
    assert client.get(f"/api/books/{book_id}").json()["shelves"] == []


def test_shelves_form_without_javascript_redirects_back(client):
    book_id = _api_book(client)
    first, second = _api_shelf(client, "A"), _api_shelf(client, "B")
    response = client.post(
        f"/books/{book_id}/shelves",
        data={"shelf_ids": [str(first), str(second)]},
        follow_redirects=False,
    )
    assert (response.status_code, response.headers["location"]) == (303, f"/books/{book_id}")
    assert sorted(_checked_shelves(_detail(client, book_id))) == ["A", "B"]


def test_detail_without_shelves_points_to_the_list_screen(client):
    book_id = _api_book(client)
    assert "Nie masz jeszcze półek" in _detail(client, book_id).by_id("book-shelves").text


# specky: crit 01M5JNJCQEVYGC2P99P6Q94253
def test_added_note_appears_first_with_date_and_time(client):
    book_id = _api_book(client)
    client.post(f"/books/{book_id}/notes", data={"content": "starsza"}, headers=HX)

    response = client.post(f"/books/{book_id}/notes", data={"content": "nowsza"}, headers=HX)

    section = parse_html(response.text).by_id("notes-section")
    assert response.status_code == 200
    assert _note_texts(section) == ["nowsza", "starsza"]
    assert DATE_TIME.match(section.find("li").find("time").text)
    assert section.by_id("note-content").text == ""
    assert "autofocus" in section.by_id("note-content").attrs


def test_note_form_is_labelled_and_posts_to_the_section(client):
    book_id = _api_book(client)
    document = _detail(client, book_id)
    form = document.by_id("add-note-form")
    assert label_for(document, "note-content").text == "Nowa notatka"
    assert (form.get("hx-post"), form.get("hx-target")) == (
        f"/books/{book_id}/notes",
        "#notes-section",
    )


@pytest.mark.parametrize("content", ["   ", "a" * 2001])
def test_invalid_note_shows_error_next_to_the_field(client, content):
    book_id = _api_book(client)
    response = client.post(f"/books/{book_id}/notes", data={"content": content}, headers=HX)
    section = parse_html(response.text).by_id("notes-section")
    assert response.status_code == 422
    assert section.by_id("note-content").get("aria-invalid") == "true"
    assert section.by_id("note-content-error").text
    assert client.get(f"/api/books/{book_id}").json()["notes"] == []


def test_note_error_without_javascript_renders_full_detail_page(client):
    book_id = _api_book(client)
    response = client.post(f"/books/{book_id}/notes", data={"content": ""})
    document = parse_html(response.text)
    assert response.status_code == 422
    assert document.by_id("book-heading").text == "Lalka"
    assert document.by_id("note-content-error").text == "Treść notatki jest wymagana."


def test_add_note_without_javascript_redirects_back(client):
    book_id = _api_book(client)
    response = client.post(
        f"/books/{book_id}/notes", data={"content": "notatka"}, follow_redirects=False
    )
    assert (response.status_code, response.headers["location"]) == (303, f"/books/{book_id}")
    assert _note_texts(_detail(client, book_id).by_id("notes-section")) == ["notatka"]


# specky: crit 01M5JNJCQERARJF7345H59VD3K
def test_delete_button_removes_note_and_there_is_no_edit_control(client):
    book_id = _api_book(client)
    for text in ("zostaje", "do usunięcia"):
        client.post(f"/books/{book_id}/notes", data={"content": text}, headers=HX)
    section = _detail(client, book_id).by_id("notes-section")
    target = next(item for item in section.find_all("li") if "do usunięcia" in item.text)
    button = target.find("button")
    assert button.text == "Usuń"
    assert [b.text for b in section.find_all("button")] == ["Dodaj notatkę", "Usuń", "Usuń"]
    assert section.find("textarea", name="content") is not None
    assert len(section.find_all("textarea")) == 1

    note_id = target.get("id").removeprefix("note-")
    response = client.post(f"/notes/{note_id}/delete", headers=HX)

    assert _note_texts(parse_html(response.text).by_id("notes-section")) == ["zostaje"]


def test_delete_note_without_javascript_redirects_to_its_book(client):
    book_id = _api_book(client)
    note_id = client.post(f"/api/books/{book_id}/notes", json={"content": "x"}).json()["id"]
    response = client.post(f"/notes/{note_id}/delete", follow_redirects=False)
    assert (response.status_code, response.headers["location"]) == (303, f"/books/{book_id}")
    assert client.post(f"/notes/{note_id}/delete").status_code == 404


def test_note_content_is_escaped(client):
    book_id = _api_book(client)
    client.post(
        f"/books/{book_id}/notes", data={"content": "<script>alert(1)</script>"}, headers=HX
    )
    page = client.get(f"/books/{book_id}").text
    assert "<script>alert(1)</script>" not in page
    assert "&lt;script&gt;" in page
