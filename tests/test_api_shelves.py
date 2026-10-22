import pytest


def _create_shelf(client, name: str) -> int:
    response = client.post("/api/shelves", json={"name": name})
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _create_book(client, title: str = "Lalka") -> int:
    response = client.post("/api/books", json={"title": title, "author": "Bolesław Prus"})
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _set_shelves(client, book_id: int, shelf_ids: list[int]):
    return client.put(f"/api/books/{book_id}/shelves", json={"shelf_ids": shelf_ids})


def _shelf_names(client, book_id: int) -> list[str]:
    return [shelf["name"] for shelf in client.get(f"/api/books/{book_id}").json()["shelves"]]


def _counts(client) -> dict[str, int]:
    return {shelf["name"]: shelf["book_count"] for shelf in client.get("/api/shelves").json()}


def test_post_shelf_returns_201_with_zero_books(client):
    response = client.post("/api/shelves", json={"name": "  Fantastyka  "})
    assert response.status_code == 201
    assert response.json() == {"id": response.json()["id"], "name": "Fantastyka", "book_count": 0}


# specky: crit 01M5JNJBSM2GAM0PE09MT2TFYC
def test_post_shelf_with_name_differing_only_in_case_returns_422(client):
    _create_shelf(client, "Fantastyka")
    response = client.post("/api/shelves", json={"name": "fantastyka"})
    assert response.status_code == 422
    assert response.json() == {
        "detail": [{"field": "name", "message": "Półka o tej nazwie już istnieje."}]
    }


@pytest.mark.parametrize(
    ("name", "valid"), [("", False), ("   ", False), ("a" * 60, True), ("a" * 61, False)]
)
def test_post_shelf_validates_name_length(client, name, valid):
    response = client.post("/api/shelves", json={"name": name})
    assert response.status_code == (201 if valid else 422)
    if not valid:
        assert response.json()["detail"][0]["field"] == "name"


# specky: crit 01M5JNJBSN9J04WGFZXK49R5HX
def test_get_shelves_alphabetical_case_insensitive_with_counts(client):
    for name in ("zakupy", "Fantastyka", "Do pracy", "biografie"):
        _create_shelf(client, name)
    book_id = _create_book(client)
    shelves = {shelf["name"]: shelf["id"] for shelf in client.get("/api/shelves").json()}
    _set_shelves(client, book_id, [shelves["Fantastyka"]])

    listed = client.get("/api/shelves").json()
    assert [shelf["name"] for shelf in listed] == ["biografie", "Do pracy", "Fantastyka", "zakupy"]
    assert _counts(client) == {"biografie": 0, "Do pracy": 0, "Fantastyka": 1, "zakupy": 0}


# specky: crit 01M5JNJBSNE7VH0561MPY70YTA
def test_delete_shelf_with_books_keeps_books_without_that_shelf(client):
    fantasy, work = _create_shelf(client, "Fantastyka"), _create_shelf(client, "Do pracy")
    first, second = _create_book(client, "Lalka"), _create_book(client, "Faraon")
    _set_shelves(client, first, [fantasy, work])
    _set_shelves(client, second, [fantasy])

    response = client.delete(f"/api/shelves/{fantasy}")

    assert response.status_code == 204
    assert _shelf_names(client, first) == ["Do pracy"]
    assert _shelf_names(client, second) == []
    assert len(client.get("/api/books").json()) == 2
    assert client.delete(f"/api/shelves/{fantasy}").status_code == 404


# specky: crit 01M5JNJD70JB2J9YHXSMR9FVXS
def test_put_shelves_replaces_full_list(client):
    first, second = _create_shelf(client, "Fantastyka"), _create_shelf(client, "Do pracy")
    book_id = _create_book(client)
    assert sorted(_shelf_names(client, book_id)) == []
    assert _set_shelves(client, book_id, [first, second]).status_code == 200
    assert sorted(_shelf_names(client, book_id)) == ["Do pracy", "Fantastyka"]

    response = _set_shelves(client, book_id, [second])

    assert [shelf["id"] for shelf in response.json()["shelves"]] == [second]
    assert _counts(client) == {"Do pracy": 1, "Fantastyka": 0}


# specky: crit 01M5JNJD70P6Q8WWBAS94B0PQV
def test_put_shelves_with_unknown_shelf_id_returns_422_and_changes_nothing(client):
    known = _create_shelf(client, "Fantastyka")
    book_id = _create_book(client)
    _set_shelves(client, book_id, [known])

    response = _set_shelves(client, book_id, [known, 999])

    assert response.status_code == 422
    assert response.json() == {
        "detail": [{"field": "shelf_ids", "message": "Nie istnieje półka o id: 999."}]
    }
    assert _shelf_names(client, book_id) == ["Fantastyka"]


# specky: crit 01M5JNJD70889VR4YEM4WWA3S8
def test_book_can_be_on_many_shelves_or_none(client):
    ids = [_create_shelf(client, name) for name in ("A", "B", "C")]
    book_id = _create_book(client)
    assert len(_set_shelves(client, book_id, ids).json()["shelves"]) == 3
    response = _set_shelves(client, book_id, [])
    assert response.status_code == 200
    assert response.json()["shelves"] == []


def test_put_shelves_ignores_repeated_ids(client):
    shelf_id = _create_shelf(client, "Fantastyka")
    book_id = _create_book(client)
    assert len(_set_shelves(client, book_id, [shelf_id, shelf_id]).json()["shelves"]) == 1


def test_put_shelves_for_missing_book_returns_404(client):
    shelf_id = _create_shelf(client, "Fantastyka")
    assert _set_shelves(client, 999, [shelf_id]).status_code == 404


def test_put_shelves_moves_book_to_top_of_list(client):
    shelf_id = _create_shelf(client, "Fantastyka")
    older = _create_book(client, "Lalka")
    _create_book(client, "Faraon")
    _set_shelves(client, older, [shelf_id])
    assert client.get("/api/books").json()[0]["id"] == older


def test_shelf_filter_on_book_list_uses_assignments(client):
    shelf_id = _create_shelf(client, "Fantastyka")
    on_shelf, _ = _create_book(client, "Wiedźmin"), _create_book(client, "Lalka")
    _set_shelves(client, on_shelf, [shelf_id])
    listed = client.get("/api/books", params={"shelf": shelf_id}).json()
    assert [book["id"] for book in listed] == [on_shelf]
