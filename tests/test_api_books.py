import re
import time

import pytest
from sqlalchemy import insert

from app.models import Note, Shelf, book_shelves
from app.normalization import normalize_text

ISO_UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z$")


def _post_book(client, **fields):
    payload = {"title": "Lalka", "author": "Bolesław Prus", **fields}
    return client.post("/api/books", json=payload)


def _created_id(client, **fields) -> int:
    response = _post_book(client, **fields)
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _field_errors(response) -> dict[str, str]:
    return {error["field"]: error["message"] for error in response.json()["detail"]}


def test_post_creates_book_with_defaults_and_location_header(client):
    response = _post_book(client, year=1890)
    body = response.json()
    assert response.status_code == 201
    assert response.headers["location"] == f"/api/books/{body['id']}"
    assert body["status"] == "to_read"
    assert body["rating"] is None
    assert body["shelves"] == []
    assert body["notes"] == []
    assert ISO_UTC.match(body["created_at"])
    assert set(body) == {
        "id",
        "title",
        "author",
        "year",
        "status",
        "rating",
        "created_at",
        "updated_at",
        "shelves",
        "notes",
    }


def test_post_blank_title_returns_422_with_field_list(client):
    response = _post_book(client, title="   ")
    assert response.status_code == 422
    assert response.json() == {"detail": [{"field": "title", "message": "Tytuł jest wymagany."}]}


def test_post_duplicate_returns_422_on_title(client):
    _created_id(client)
    response = _post_book(client, title=" LALKA ", author="bolesław prus")
    assert response.status_code == 422
    assert "już na liście" in _field_errors(response)["title"]


def test_post_rejects_unknown_field_and_wrong_types(client):
    response = _post_book(client, year="dawno", id=7)
    assert response.status_code == 422
    assert _field_errors(response) == {"year": "Wymagana liczba całkowita.", "id": "Nieznane pole."}


def test_post_missing_author_returns_422(client):
    response = client.post("/api/books", json={"title": "Lalka"})
    assert _field_errors(response) == {"author": "Pole jest wymagane."}


# specky: crit 01M5JNJCY4PC9KCVD68Y592R5S
def test_status_uses_english_codes_and_rejects_polish_values(client):
    book_id = _created_id(client, status="reading")
    assert client.get(f"/api/books/{book_id}").json()["status"] == "reading"
    assert {book["status"] for book in client.get("/api/books").json()} <= {
        "to_read",
        "reading",
        "read",
    }
    assert client.get("/api/books", params={"status": "czytam"}).status_code == 422
    assert _post_book(client, title="Inna", status="przeczytana").status_code == 422


@pytest.fixture
def library(client, session):
    ids = {
        "Lalka": _created_id(client, title="Lalka", status="reading"),
        "Faraon": _created_id(client, title="Faraon", status="read"),
        "Wiedźmin": _created_id(client, title="Wiedźmin", author="Andrzej Sapkowski"),
        "Prusy": _created_id(client, title="Prusy", author="Ktoś", status="reading"),
    }
    shelf = Shelf(name="Fantastyka", name_norm=normalize_text("Fantastyka"))
    session.add(shelf)
    session.flush()
    session.execute(
        insert(book_shelves),
        [
            {"book_id": ids["Wiedźmin"], "shelf_id": shelf.id},
            {"book_id": ids["Lalka"], "shelf_id": shelf.id},
        ],
    )
    session.commit()
    return ids, shelf.id


def _titles(response) -> list[str]:
    assert response.status_code == 200
    return [book["title"] for book in response.json()]


# specky: crit 01M5JNJC2VFM8BZCR01MZ1JCT3
def test_get_list_filters_by_status_and_query_case_insensitively(client, library):
    response = client.get("/api/books", params={"status": "reading", "q": "PRUS"})
    assert sorted(_titles(response)) == ["Lalka", "Prusy"]


def test_get_list_combines_shelf_filter_with_others(client, library):
    _, shelf_id = library
    assert sorted(_titles(client.get("/api/books", params={"shelf": shelf_id}))) == [
        "Lalka",
        "Wiedźmin",
    ]
    combined = client.get(
        "/api/books", params={"shelf": shelf_id, "status": "reading", "q": "prus"}
    )
    assert _titles(combined) == ["Lalka"]
    assert client.get("/api/books", params={"shelf": 999}).json() == []


def test_get_list_returns_shelves_as_labels(client, library):
    by_title = {book["title"]: book for book in client.get("/api/books").json()}
    assert [shelf["name"] for shelf in by_title["Wiedźmin"]["shelves"]] == ["Fantastyka"]
    assert "notes" not in by_title["Wiedźmin"]


# specky: crit 01M5JNJC2VP96Y3TNJNYETA8NT
def test_get_list_sorted_by_updated_at_descending_and_fresh_change_first(client, library):
    ids, _ = library
    assert _titles(client.get("/api/books")) == ["Prusy", "Wiedźmin", "Faraon", "Lalka"]
    client.patch(f"/api/books/{ids['Faraon']}", json={"year": 1897})
    assert _titles(client.get("/api/books"))[0] == "Faraon"


# specky: crit 01M5JNJC2VZ603VSQV5K1WD17A
def test_get_detail_contains_shelves_and_notes_and_404_for_missing(client, library, session):
    ids, _ = library
    session.add(Note(book_id=ids["Lalka"], content="Świetna"))
    session.commit()
    detail = client.get(f"/api/books/{ids['Lalka']}").json()
    assert [shelf["name"] for shelf in detail["shelves"]] == ["Fantastyka"]
    assert [note["content"] for note in detail["notes"]] == ["Świetna"]
    missing = client.get("/api/books/9999")
    assert missing.status_code == 404
    assert missing.json() == {"detail": "Nie znaleziono książki."}


# specky: crit 01M5JNJC2VY0KCBQBY5YFCQ8DZ
def test_patch_with_only_author_changes_author_and_updated_at(client):
    book_id = _created_id(client, year=1890)
    before = client.get(f"/api/books/{book_id}").json()
    time.sleep(0.001)
    after = client.patch(f"/api/books/{book_id}", json={"author": "B. Prus"}).json()
    assert after["author"] == "B. Prus"
    assert {key: after[key] for key in ("title", "year", "status", "rating", "created_at")} == {
        key: before[key] for key in ("title", "year", "status", "rating", "created_at")
    }
    assert after["updated_at"] > before["updated_at"]


def test_patch_rating_rules_through_api(client):
    book_id = _created_id(client)
    assert client.patch(f"/api/books/{book_id}", json={"rating": 4}).status_code == 422
    client.patch(f"/api/books/{book_id}", json={"status": "reading"})
    assert client.patch(f"/api/books/{book_id}", json={"rating": 4}).json()["rating"] == 4
    assert client.patch(f"/api/books/{book_id}", json={"status": "read"}).json()["rating"] == 4
    assert (
        client.patch(f"/api/books/{book_id}", json={"status": "to_read"}).json()["rating"] is None
    )
    assert client.patch(f"/api/books/{book_id}", json={"rating": 6}).status_code == 422


def test_patch_null_year_clears_it_and_null_title_is_rejected(client):
    book_id = _created_id(client, year=1890)
    assert client.patch(f"/api/books/{book_id}", json={"year": None}).json()["year"] is None
    response = client.patch(f"/api/books/{book_id}", json={"title": None})
    assert _field_errors(response) == {"title": "Tytuł jest wymagany."}


def test_patch_missing_book_returns_404(client):
    assert client.patch("/api/books/9999", json={"year": 2000}).status_code == 404


def test_delete_returns_204_then_404(client):
    book_id = _created_id(client)
    response = client.delete(f"/api/books/{book_id}")
    assert response.status_code == 204
    assert response.content == b""
    assert client.get(f"/api/books/{book_id}").status_code == 404
    assert client.delete(f"/api/books/{book_id}").status_code == 404


def test_non_numeric_book_id_returns_422(client):
    assert _field_errors(client.get("/api/books/abc")) == {"book_id": "Wymagana liczba całkowita."}


def test_openapi_schema_is_served(client):
    assert client.get("/openapi.json").status_code == 200
