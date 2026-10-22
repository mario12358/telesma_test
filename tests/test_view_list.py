import pytest

from tests.html import label_for, parse_html

HX = {"HX-Request": "true"}


def _api_book(client, title="Lalka", **fields) -> int:
    response = client.post("/api/books", json={"title": title, "author": "Bolesław Prus", **fields})
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _rows(document) -> list:
    return document.by_id("book-list").find_all("tr")[1:]


def _row_titles(document) -> list[str]:
    return [row.find("a").text for row in _rows(document)]


def test_list_page_shows_book_columns_with_detail_link(client):
    book_id = _api_book(client, year=1890, status="read", rating=5)
    shelf_id = client.post("/api/shelves", json={"name": "Klasyka"}).json()["id"]
    client.put(f"/api/books/{book_id}/shelves", json={"shelf_ids": [shelf_id]})

    row = parse_html(client.get("/").text).by_id(f"book-{book_id}")

    cells = {cell.get("data-label"): cell for cell in row.find_all("td")}
    assert cells["Tytuł"].find("a").get("href") == f"/books/{book_id}"
    assert cells["Autor"].text == "Bolesław Prus"
    assert cells["Rok"].text == "1890"
    assert "Ocena 5 z 5" in cells["Ocena"].text
    assert cells["Ocena"].find("span", class_="stars").text == "★★★★★"
    assert [tag.text for tag in cells["Półki"].find_all("span", class_="tag")] == ["Klasyka"]


# specky: crit 01M5JNJCY48R0NGCK2T4RHWD50
def test_list_shows_status_as_polish_labels(client):
    book_id = _api_book(client, status="reading")
    row = parse_html(client.get("/").text).by_id(f"book-{book_id}")
    pressed = [button.text for button in row.find_all("button", aria_pressed="true")]
    labels = [button.text for button in row.find_all("button")]
    assert pressed == ["czytam"]
    assert labels == ["do przeczytania", "czytam", "przeczytana"]
    assert "reading" not in row.text


def test_empty_list_shows_message(client):
    assert "Brak książek" in parse_html(client.get("/").text).by_id("book-list").text


# specky: crit 01M5JNJCCBXZHZ1HN80R201YG9
def test_every_add_form_control_has_an_associated_label(client):
    document = parse_html(client.get("/").text)
    form = document.by_id("add-book-form")
    for control in form.find_all("input"):
        label = label_for(document, control.get("id"))
        assert label is not None and label.text, control.get("id")
    assert form.find("button", type="submit").text == "Dodaj"


# specky: crit 01M5JNJCF5FQS8KHMDEWH4EEBZ
def test_htmx_add_returns_cleared_form_and_list_with_new_book_first(client):
    _api_book(client, title="Starsza")
    response = client.post(
        "/books", data={"title": "Faraon", "author": "Bolesław Prus", "year": "1897"}, headers=HX
    )
    document = parse_html(response.text)
    assert response.status_code == 200
    form = document.by_id("add-book-form")
    assert [field.get("value") for field in form.find_all("input")] == ["", "", ""]
    assert "autofocus" in form.by_id("new-title").attrs
    book_list = document.by_id("book-list")
    assert book_list.get("hx-swap-oob") == "true"
    assert _row_titles(document) == ["Faraon", "Starsza"]


# specky: crit 01M5JNJCCBFG5JC7MES61ZZ3T7
def test_add_without_javascript_redirects_to_list_with_new_book(client):
    response = client.post(
        "/books",
        data={"title": "Faraon", "author": "Bolesław Prus", "year": ""},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/"
    assert _row_titles(parse_html(client.get("/").text)) == ["Faraon"]


def test_htmx_add_request_targets_the_form_itself(client):
    form = parse_html(client.get("/").text).by_id("add-book-form")
    assert (form.get("hx-post"), form.get("hx-target"), form.get("hx-swap")) == (
        "/books",
        "this",
        "outerHTML",
    )
    assert (form.get("method"), form.get("action")) == ("post", "/books")


# specky: crit 01M5JNJCCBV4KQ4DMWTE3A5SH6
def test_validation_error_is_rendered_next_to_the_title_field(client):
    response = client.post("/books", data={"title": "  ", "author": "Prus", "year": ""}, headers=HX)
    form = parse_html(response.text).by_id("add-book-form")
    title = form.by_id("new-title")
    assert response.status_code == 422
    assert title.get("aria-invalid") == "true"
    assert form.by_id(title.get("aria-describedby")).text == "Tytuł jest wymagany."
    assert form.by_id("new-author").get("value") == "Prus"
    assert "alert(" not in response.text


@pytest.mark.parametrize(
    ("data", "field", "message"),
    [
        ({"title": "Lalka", "author": "Bolesław Prus", "year": ""}, "title", "już na liście"),
        ({"title": "Nowa", "author": "X", "year": "dawno"}, "year", "Wymagana liczba całkowita."),
        ({"title": "Nowa", "author": "X", "year": "1200"}, "year", "Rok musi być z zakresu"),
    ],
)
def test_add_form_reports_duplicate_and_year_errors_at_the_field(client, data, field, message):
    _api_book(client)
    response = client.post("/books", data=data, headers=HX)
    error = parse_html(response.text).by_id(f"new-{field}-error")
    assert response.status_code == 422
    assert message in error.text


def test_add_error_without_javascript_rerenders_full_page_with_errors(client):
    response = client.post("/books", data={"title": "", "author": "", "year": ""})
    document = parse_html(response.text)
    assert response.status_code == 422
    assert document.find("h1").text == "Moje lektury"
    assert document.by_id("new-author-error").text == "Autor jest wymagany."


# specky: crit 01M5JNJCF5K1H3JEVZQVR12B33
def test_status_button_changes_status_and_returns_only_that_row(client):
    book_id = _api_book(client)
    response = client.post(f"/books/{book_id}/status", data={"status": "reading"}, headers=HX)
    document = parse_html(response.text)
    assert response.status_code == 200
    rows = document.find_all("tr")
    assert [row.get("id") for row in rows] == [f"book-{book_id}"]
    assert [button.text for button in rows[0].find_all("button", aria_pressed="true")] == ["czytam"]
    assert client.get(f"/api/books/{book_id}").json()["status"] == "reading"


def test_status_buttons_target_their_own_row(client):
    book_id = _api_book(client)
    form = parse_html(client.get("/").text).by_id(f"book-{book_id}").find("form")
    assert form.get("hx-post") == f"/books/{book_id}/status"
    assert (form.get("hx-target"), form.get("hx-swap")) == ("closest tr", "outerHTML")


def test_status_change_to_read_later_clears_rating_from_the_row(client):
    book_id = _api_book(client, status="read", rating=4)
    response = client.post(f"/books/{book_id}/status", data={"status": "to_read"}, headers=HX)
    assert "★" not in response.text
    assert client.get(f"/api/books/{book_id}").json()["rating"] is None


def test_status_change_without_javascript_redirects(client):
    book_id = _api_book(client)
    response = client.post(
        f"/books/{book_id}/status", data={"status": "read"}, follow_redirects=False
    )
    assert (response.status_code, response.headers["location"]) == (303, "/")
    assert client.get(f"/api/books/{book_id}").json()["status"] == "read"


def test_status_change_for_missing_book_returns_404_page(client):
    response = client.post("/books/999/status", data={"status": "read"}, headers=HX)
    assert response.status_code == 404


# specky: crit 01M5JNJCF5WHBZ6SQWG62J3WXG
def test_title_links_to_detail_screen(client):
    book_id = _api_book(client)
    link = parse_html(client.get("/").text).by_id(f"book-{book_id}").find("a")
    assert link.get("href") == f"/books/{book_id}"
