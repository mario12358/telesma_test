import pytest

from app.services.stats import _round_one_decimal
from app.templating import decimal_pl
from tests.html import parse_html

HX = {"HX-Request": "true"}


def _api_book(client, title, **fields) -> int:
    response = client.post("/api/books", json={"title": title, "author": "Autor", **fields})
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _header_stats(markup: str) -> dict[str, str]:
    stats = parse_html(markup).by_id("stats")
    return {item.get("data-stat"): item.text for item in stats.find_all("dd")}


# specky: crit 01M5JNJC9EBJB0ZHNAM076HF2Q
def test_stats_count_each_status_and_average_read_ratings(client):
    _api_book(client, "A")
    _api_book(client, "B")
    _api_book(client, "C", status="reading", rating=1)
    _api_book(client, "D", status="read", rating=4)
    _api_book(client, "E", status="read", rating=5)
    assert client.get("/api/stats").json() == {
        "to_read": 2,
        "reading": 1,
        "read": 2,
        "average_rating": 4.5,
    }


# specky: crit 01M5JNJC9E527FQCDGD1MXYGDR
def test_average_is_null_without_rated_read_books(client):
    _api_book(client, "A", status="read")
    _api_book(client, "B", status="reading", rating=5)
    assert client.get("/api/stats").json() == {
        "to_read": 0,
        "reading": 1,
        "read": 1,
        "average_rating": None,
    }


def test_average_is_rounded_to_one_decimal(client):
    for title, rating in (("A", 4), ("B", 4), ("C", 5)):
        _api_book(client, title, status="read", rating=rating)
    assert client.get("/api/stats").json()["average_rating"] == 4.3


@pytest.mark.parametrize(
    ("value", "expected"), [(4.25, 4.3), (4.333, 4.3), (4.35, 4.4), (5.0, 5.0)]
)
def test_rounding_is_half_up(value, expected):
    assert _round_one_decimal(value) == expected


def test_empty_library_stats(client):
    assert client.get("/api/stats").json() == {
        "to_read": 0,
        "reading": 0,
        "read": 0,
        "average_rating": None,
    }


def test_header_shows_stats_on_both_screens(client):
    book_id = _api_book(client, "A", status="read", rating=4)
    _api_book(client, "B")
    expected = {"to_read": "1", "reading": "0", "read": "1", "average_rating": "4,0"}
    assert _header_stats(client.get("/").text) == expected
    assert _header_stats(client.get(f"/books/{book_id}").text) == expected


def test_header_shows_dash_without_average(client):
    assert _header_stats(client.get("/").text)["average_rating"] == "—"


# specky: crit 01M5JNJC9ERY4G58GS31GB52B3
def test_status_change_on_the_list_refreshes_header_counters(client):
    book_id = _api_book(client, "A")
    response = client.post(f"/books/{book_id}/status", data={"status": "reading"}, headers=HX)
    stats = parse_html(response.text).by_id("stats")
    assert stats.get("hx-swap-oob") == "true"
    assert _header_stats(response.text) == {
        "to_read": "0",
        "reading": "1",
        "read": "0",
        "average_rating": "—",
    }


def test_adding_a_book_refreshes_header_counters(client):
    response = client.post("/books", data={"title": "Nowa", "author": "X", "year": ""}, headers=HX)
    assert parse_html(response.text).by_id("stats").get("hx-swap-oob") == "true"
    assert _header_stats(response.text)["to_read"] == "1"


@pytest.mark.parametrize(
    ("field", "value", "stat", "expected"),
    [("status", "read", "read", "1"), ("rating", "3", "average_rating", "3,0")],
)
def test_detail_changes_of_status_or_rating_refresh_header(client, field, value, stat, expected):
    book_id = _api_book(client, "A", status="read")
    if field == "status":
        client.patch(f"/api/books/{book_id}", json={"status": "reading"})
    response = client.post(f"/books/{book_id}/fields/{field}", data={field: value}, headers=HX)
    assert parse_html(response.text).by_id("stats").get("hx-swap-oob") == "true"
    assert _header_stats(response.text)[stat] == expected


def test_title_change_does_not_send_stats(client):
    book_id = _api_book(client, "A")
    response = client.post(f"/books/{book_id}/fields/title", data={"title": "B"}, headers=HX)
    assert parse_html(response.text).find(id="stats") is None


@pytest.mark.parametrize(("value", "text"), [(4.5, "4,5"), (4.0, "4,0"), (3.25, "3,2")])
def test_decimal_pl_uses_a_comma(value, text):
    assert decimal_pl(value) == text
