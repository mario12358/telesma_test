import re

import pytest

ISO_UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z$")


def _create_book(client, title: str = "Lalka") -> int:
    response = client.post("/api/books", json={"title": title, "author": "Bolesław Prus"})
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _add_note(client, book_id: int, content: str):
    return client.post(f"/api/books/{book_id}/notes", json={"content": content})


def _note_contents(client, book_id: int) -> list[str]:
    return [note["content"] for note in client.get(f"/api/books/{book_id}").json()["notes"]]


# specky: crit 01M5JNJD8ZYH50QK3K5CSQ4AWG
def test_post_note_returns_201_with_fields(client):
    book_id = _create_book(client)
    response = _add_note(client, book_id, "  Świetna powieść  ")
    body = response.json()
    assert response.status_code == 201
    assert set(body) == {"id", "book_id", "content", "created_at"}
    assert (body["book_id"], body["content"]) == (book_id, "Świetna powieść")
    assert ISO_UTC.match(body["created_at"])


# specky: crit 01M5JNJBYS280EEM43ZME7Y9AB
@pytest.mark.parametrize("content", ["", "   ", "a" * 2001])
def test_post_note_with_empty_or_too_long_content_returns_422(client, content):
    book_id = _create_book(client)
    response = _add_note(client, book_id, content)
    assert response.status_code == 422
    assert [error["field"] for error in response.json()["detail"]] == ["content"]
    assert _note_contents(client, book_id) == []


def test_post_note_accepts_exactly_2000_characters(client):
    book_id = _create_book(client)
    assert _add_note(client, book_id, "a" * 2000).status_code == 201


def test_post_note_for_missing_book_returns_404(client):
    response = _add_note(client, 999, "treść")
    assert response.status_code == 404
    assert response.json() == {"detail": "Nie znaleziono książki."}


# specky: crit 01M5JNJBYSBQ2M7QNWZKYM3R0Y
def test_book_detail_lists_notes_newest_first(client):
    book_id = _create_book(client)
    for content in ("pierwsza", "druga", "trzecia"):
        _add_note(client, book_id, content)
    notes = client.get(f"/api/books/{book_id}").json()["notes"]
    assert [note["content"] for note in notes] == ["trzecia", "druga", "pierwsza"]
    timestamps = [note["created_at"] for note in notes]
    assert timestamps == sorted(timestamps, reverse=True)


def test_notes_belong_only_to_their_book(client):
    first, second = _create_book(client, "Lalka"), _create_book(client, "Faraon")
    _add_note(client, first, "o Lalce")
    assert _note_contents(client, second) == []


# specky: crit 01M5JNJD8ZVZA1G2XQEB30V6BA
def test_delete_note_removes_it_and_second_delete_returns_404(client):
    book_id = _create_book(client)
    keep = _add_note(client, book_id, "zostaje").json()["id"]
    remove = _add_note(client, book_id, "do usunięcia").json()["id"]

    assert client.delete(f"/api/notes/{remove}").status_code == 204
    assert _note_contents(client, book_id) == ["zostaje"]
    second = client.delete(f"/api/notes/{remove}")
    assert second.status_code == 404
    assert second.json() == {"detail": "Nie znaleziono notatki."}
    assert keep != remove


# specky: crit 01M5JNJBYSEH0759CW3W8F234H
@pytest.mark.parametrize("method", ["patch", "put"])
def test_notes_cannot_be_edited(client, method):
    book_id = _create_book(client)
    note_id = _add_note(client, book_id, "oryginał").json()["id"]
    response = getattr(client, method)(f"/api/notes/{note_id}", json={"content": "zmiana"})
    assert response.status_code in (404, 405)
    assert _note_contents(client, book_id) == ["oryginał"]


# specky: crit 01M5JNJD4JQNSEDMCKPZQD7DWS
def test_deleting_book_removes_its_notes_and_keeps_shelves_with_lower_count(client):
    book_id = _create_book(client)
    other_id = _create_book(client, "Faraon")
    note_ids = [_add_note(client, book_id, text).json()["id"] for text in ("a", "b")]
    shelf_ids = [
        client.post("/api/shelves", json={"name": name}).json()["id"]
        for name in ("Fantastyka", "Do pracy")
    ]
    client.put(f"/api/books/{book_id}/shelves", json={"shelf_ids": shelf_ids})
    client.put(f"/api/books/{other_id}/shelves", json={"shelf_ids": shelf_ids})

    assert client.delete(f"/api/books/{book_id}").status_code == 204

    assert [client.delete(f"/api/notes/{note_id}").status_code for note_id in note_ids] == [
        404,
        404,
    ]
    counts = {shelf["name"]: shelf["book_count"] for shelf in client.get("/api/shelves").json()}
    assert counts == {"Do pracy": 1, "Fantastyka": 1}
