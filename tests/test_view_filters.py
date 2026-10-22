import pytest

from tests.html import label_for, parse_html

HX = {"HX-Request": "true"}


def _api_book(client, title, author="Bolesław Prus", **fields) -> int:
    response = client.post("/api/books", json={"title": title, "author": author, **fields})
    assert response.status_code == 201, response.text
    return response.json()["id"]


@pytest.fixture
def library(client) -> dict[str, int]:
    fantasy = client.post("/api/shelves", json={"name": "Fantastyka"}).json()["id"]
    ids = {
        "Lalka": _api_book(client, "Lalka", status="reading"),
        "Faraon": _api_book(client, "Faraon", status="read"),
        "Wiedźmin": _api_book(client, "Wiedźmin", "Andrzej Sapkowski", status="reading"),
        "Prusy": _api_book(client, "Prusy Wschodnie", "Ktoś", status="reading"),
        "Narrenturm": _api_book(client, "Narrenturm", "Andrzej Sapkowski"),
    }
    for title in ("Wiedźmin", "Lalka", "Narrenturm"):
        client.put(f"/api/books/{ids[title]}/shelves", json={"shelf_ids": [fantasy]})
    return {**ids, "shelf": fantasy}


def _listed_ids(markup: str) -> set[int]:
    rows = parse_html(markup).by_id("book-list").find_all("tr")[1:]
    return {int(row.get("id").removeprefix("book-")) for row in rows}


def _api_ids(client, params) -> set[int]:
    return {book["id"] for book in client.get("/api/books", params=params).json()}


def test_filter_bar_has_status_buttons_shelf_select_and_search(client, library):
    document = parse_html(client.get("/").text)
    bar = document.by_id("filters")
    labels = [
        label_for(document, radio.get("id")).text for radio in bar.find_all("input", type="radio")
    ]
    assert labels == ["wszystkie", "do przeczytania", "czytam", "przeczytana"]
    assert "checked" in bar.by_id("filter-status-all").attrs
    options = [option.text for option in bar.by_id("filter-shelf").find_all("option")]
    assert options == ["wszystkie półki", "Fantastyka"]
    assert label_for(document, "filter-q").text == "Szukaj w tytule lub autorze"
    assert bar.find("button", type="submit").text == "Szukaj"


# specky: crit 01M5JNJCK89CNSWP5DT8SNJBCD
@pytest.mark.parametrize(
    "params",
    [
        {"status": "reading", "q": "prus"},
        {"status": "reading", "shelf": "SHELF", "q": "prus"},
        {"shelf": "SHELF"},
        {"q": "SAPKOWSKI"},
        {"status": "to_read", "shelf": "SHELF"},
        {"q": "wiedź"},
        {},
    ],
)
def test_combined_filters_match_the_api(client, library, params):
    resolved = {
        key: str(library["shelf"]) if value == "SHELF" else value for key, value in params.items()
    }
    assert _listed_ids(client.get("/", params=resolved).text) == _api_ids(client, resolved)


def test_status_shelf_and_query_narrow_down_to_one_book(client, library):
    params = {"status": "reading", "shelf": str(library["shelf"]), "q": "prus"}
    assert _listed_ids(client.get("/", params=params).text) == {library["Lalka"]}


def test_htmx_filter_request_returns_only_the_list_fragment(client, library):
    response = client.get("/", params={"q": "sapkowski"}, headers=HX)
    document = parse_html(response.text)
    assert document.find("html") is None
    assert document.by_id("book-list").get("hx-swap-oob") is None
    assert _listed_ids(response.text) == {library["Wiedźmin"], library["Narrenturm"]}


# specky: crit 01M5JNJCK876SZCQFJ4EX5RDVP
def test_search_field_updates_the_list_while_typing_with_delay(client, library):
    search = parse_html(client.get("/").text).by_id("filter-q")
    assert search.get("hx-get") == "/"
    assert search.get("hx-trigger") == "input changed delay:300ms, search"
    assert (search.get("hx-target"), search.get("hx-include")) == ("#book-list", "#filters")


# specky: crit 01M5JNJCK8EWG0VB920K3TTRQ9
def test_active_filters_are_in_the_url_and_restored_on_reload(client, library):
    bar_form = parse_html(client.get("/").text).by_id("filters")
    assert (bar_form.get("method"), bar_form.get("action"), bar_form.get("hx-push-url")) == (
        "get",
        "/",
        "true",
    )

    params = {"status": "read", "shelf": str(library["shelf"]), "q": "far"}
    bar = parse_html(client.get("/", params=params).text).by_id("filters")

    assert "checked" in bar.by_id("filter-status-read").attrs
    selected = [option.text for option in bar.find_all("option") if "selected" in option.attrs]
    assert selected == ["Fantastyka"]
    assert bar.by_id("filter-q").get("value") == "far"


@pytest.mark.parametrize("params", [{"status": "czytam"}, {"shelf": "abc"}, {"shelf": "999"}])
def test_unknown_filter_values_do_not_break_the_page(client, library, params):
    response = client.get("/", params=params)
    assert response.status_code == 200


def test_adding_a_book_keeps_the_active_filters(client, library):
    response = client.post(
        "/books",
        data={"title": "Nowa", "author": "Andrzej Sapkowski", "year": "", "q": "sapkowski"},
        headers=HX,
    )
    titles = {
        row.find("a").text
        for row in parse_html(response.text).by_id("book-list").find_all("tr")[1:]
    }
    assert titles == {"Nowa", "Wiedźmin", "Narrenturm"}


def test_new_shelf_appears_in_the_filter_dropdown(client, library):
    response = client.post("/shelves", data={"name": "Klasyka"}, headers=HX)
    select = parse_html(response.text).by_id("filter-shelf")
    assert select.get("hx-swap-oob") == "true"
    assert [option.text for option in select.find_all("option")] == [
        "wszystkie półki",
        "Fantastyka",
        "Klasyka",
    ]


def test_deleting_the_filtered_shelf_resets_that_filter(client, library):
    shelf_id = library["shelf"]
    response = client.post(f"/shelves/{shelf_id}/delete", data={"shelf": str(shelf_id)}, headers=HX)
    document = parse_html(response.text)
    assert [option.text for option in document.by_id("filter-shelf").find_all("option")] == [
        "wszystkie półki"
    ]
    assert len(document.by_id("book-list").find_all("tr")) - 1 == 5
