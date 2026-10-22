import pytest

from tests.html import label_for, parse_html

HX = {"HX-Request": "true"}


def _api_book(client, **fields) -> int:
    payload = {"title": "Lalka", "author": "Bolesław Prus", "year": 1890, **fields}
    response = client.post("/api/books", json=payload)
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _api(client, book_id: int) -> dict:
    return client.get(f"/api/books/{book_id}").json()


def _save_field(client, book_id: int, field: str, value: str):
    form_name = "status" if field == "status" else field
    return client.post(f"/books/{book_id}/fields/{field}", data={form_name: value}, headers=HX)


def test_detail_page_shows_all_fields_with_labels(client):
    book_id = _api_book(client, status="read", rating=4)
    document = parse_html(client.get(f"/books/{book_id}").text)
    assert document.by_id("book-heading").text == "Lalka"
    assert document.by_id("detail-title").get("value") == "Lalka"
    assert document.by_id("detail-author").get("value") == "Bolesław Prus"
    assert document.by_id("detail-year").get("value") == "1890"
    options = document.by_id("detail-status").find_all("option")
    assert [option.text for option in options if "selected" in option.attrs] == ["przeczytana"]
    assert "checked" in document.by_id("rating-4").attrs
    for control_id in ("detail-title", "detail-author", "detail-year", "detail-status", "rating-4"):
        assert label_for(document, control_id) is not None, control_id


def test_detail_fields_save_individually_on_change(client):
    book_id = _api_book(client)
    title = parse_html(client.get(f"/books/{book_id}").text).by_id("detail-title")
    assert title.get("hx-post") == f"/books/{book_id}/fields/title"
    assert (title.get("hx-trigger"), title.get("hx-target")) == ("change", "#field-title")


# specky: crit 01M5JNJCNC307GVYBRS5WXDG1H
def test_changing_author_saves_without_reload_and_persists(client):
    book_id = _api_book(client)
    response = _save_field(client, book_id, "author", "B. Prus")
    fragment = parse_html(response.text)
    assert response.status_code == 200
    assert fragment.by_id("field-author").find("p", class_="saved").text == "Zapisano"
    assert fragment.find("html") is None
    reloaded = parse_html(client.get(f"/books/{book_id}").text)
    assert reloaded.by_id("detail-author").get("value") == "B. Prus"


def test_changing_title_also_updates_the_heading(client):
    book_id = _api_book(client)
    heading = parse_html(_save_field(client, book_id, "title", "Emancypantki").text).by_id(
        "book-heading"
    )
    assert (heading.text, heading.get("hx-swap-oob")) == ("Emancypantki", "true")


# specky: crit 01M5JNJCNCN762H1ZTHNKDWEH7
def test_invalid_year_shows_error_at_the_field_and_keeps_database(client):
    book_id = _api_book(client, year=1890)
    response = _save_field(client, book_id, "year", "1200")
    field = parse_html(response.text).by_id("field-year")
    year_input = field.by_id("detail-year")
    assert response.status_code == 422
    assert year_input.get("value") == "1200"
    assert year_input.get("aria-invalid") == "true"
    assert field.by_id("detail-year-error").text.startswith("Rok musi być z zakresu 1450")
    assert _api(client, book_id)["year"] == 1890


@pytest.mark.parametrize(("field", "value"), [("title", " "), ("author", ""), ("year", "abc")])
def test_invalid_field_values_are_rejected_at_the_field(client, field, value):
    book_id = _api_book(client)
    response = _save_field(client, book_id, field, value)
    assert response.status_code == 422
    assert parse_html(response.text).by_id(f"detail-{field}-error").text


# specky: crit 01M5JNJCNCT9XX35EHR5NAZRGJ
def test_stars_are_disabled_with_hint_while_to_read(client):
    book_id = _api_book(client)
    document = parse_html(client.get(f"/books/{book_id}").text)
    rating = document.by_id("field-rating").find("fieldset")
    assert "disabled" in rating.attrs
    assert document.by_id("rating-hint").text.startswith("Ocenę można wystawić")


def test_clicking_fourth_star_while_reading_saves_rating_four(client):
    book_id = _api_book(client, status="reading")
    star = parse_html(client.get(f"/books/{book_id}").text).by_id("rating-4")
    assert star.get("hx-post") == f"/books/{book_id}/fields/rating"

    response = _save_field(client, book_id, "rating", "4")

    rating = parse_html(response.text).by_id("field-rating")
    assert "checked" in rating.by_id("rating-4").attrs
    assert [label.text[0] for label in rating.find_all("label", class_="star")] == list("★★★★☆")
    assert _api(client, book_id)["rating"] == 4


def test_status_change_refreshes_the_rating_widget(client):
    book_id = _api_book(client, status="reading", rating=3)
    response = _save_field(client, book_id, "status", "read")
    document = parse_html(response.text)
    rating = document.by_id("field-rating")
    assert rating.get("hx-swap-oob") == "true"
    assert "checked" in rating.by_id("rating-3").attrs

    cleared = parse_html(_save_field(client, book_id, "status", "to_read").text).by_id(
        "field-rating"
    )
    assert "disabled" in cleared.find("fieldset").attrs
    assert "checked" in cleared.by_id("rating-none").attrs
    assert _api(client, book_id)["rating"] is None


def test_rating_while_to_read_is_rejected_by_the_server(client):
    book_id = _api_book(client)
    response = _save_field(client, book_id, "rating", "5")
    assert response.status_code == 422
    assert _api(client, book_id)["rating"] is None


def test_choosing_no_rating_clears_it(client):
    book_id = _api_book(client, status="read", rating=2)
    _save_field(client, book_id, "rating", "")
    assert _api(client, book_id)["rating"] is None


def test_full_form_without_javascript_saves_all_fields(client):
    book_id = _api_book(client)
    data = {"title": "Faraon", "author": "B. Prus", "year": "1897", "status": "read", "rating": "5"}
    response = client.post(f"/books/{book_id}", data=data, follow_redirects=False)
    assert (response.status_code, response.headers["location"]) == (303, f"/books/{book_id}")
    saved = _api(client, book_id)
    assert (saved["title"], saved["year"], saved["status"], saved["rating"]) == (
        "Faraon",
        1897,
        "read",
        5,
    )


def test_full_form_errors_render_the_page_with_messages(client):
    book_id = _api_book(client)
    data = {"title": "", "author": "B. Prus", "year": "1897", "status": "to_read", "rating": ""}
    response = client.post(f"/books/{book_id}", data=data)
    document = parse_html(response.text)
    assert response.status_code == 422
    assert document.by_id("detail-title-error").text == "Tytuł jest wymagany."
    assert document.by_id("detail-author").get("value") == "B. Prus"
    assert _api(client, book_id)["author"] == "Bolesław Prus"


def test_save_button_is_offered_only_without_javascript(client):
    book_id = _api_book(client)
    form = parse_html(client.get(f"/books/{book_id}").text).by_id("book-form")
    assert form.find("noscript").find("button").text == "Zapisz"


# specky: crit 01M5JNJCNCQ5Q9XKZHHJC5V1MK
def test_delete_asks_for_confirmation_and_redirects_to_list(client):
    book_id = _api_book(client)
    button = (
        parse_html(client.get(f"/books/{book_id}").text)
        .find("form", class_="delete-book")
        .find("button")
    )
    assert button.get("hx-confirm") == "Usunąć książkę «Lalka»? Jej notatki też zostaną usunięte."

    response = client.post(f"/books/{book_id}/delete", headers=HX)

    assert response.headers["hx-redirect"] == "/"
    assert parse_html(client.get("/").text).find(id=f"book-{book_id}") is None


def test_delete_without_javascript_uses_a_confirmation_page(client):
    book_id = _api_book(client)
    confirm = parse_html(client.get(f"/books/{book_id}/delete").text)
    assert confirm.find("form", method="post").get("action") == f"/books/{book_id}/delete"
    response = client.post(f"/books/{book_id}/delete", follow_redirects=False)
    assert (response.status_code, response.headers["location"]) == (303, "/")
    assert client.get(f"/api/books/{book_id}").status_code == 404


@pytest.mark.parametrize("path", ["/books/999", "/books/abc", "/books/999/delete"])
def test_missing_book_detail_renders_404_page(client, path):
    response = client.get(path)
    assert response.status_code == 404
    assert parse_html(response.text).find("h1").text == "Nie znaleziono"
