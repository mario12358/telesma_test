import csv
import io

from tests.html import parse_html

HEADER = ["tytuł", "autor", "rok", "status", "ocena", "półki"]


def _api_book(client, title, **fields) -> int:
    response = client.post("/api/books", json={"title": title, "author": "Bolesław Prus", **fields})
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _rows(response) -> list[list[str]]:
    text = response.content.decode("utf-8-sig")
    return list(csv.reader(io.StringIO(text)))


# specky: crit 01M5JNJC6S8FX7X6XGG4SB2B8C
def test_export_has_header_and_one_row_per_book(client):
    _api_book(client, "Lalka", year=1890, status="read", rating=5)
    _api_book(client, "Faraon")
    _api_book(client, "Emancypantki", status="reading")
    rows = _rows(client.get("/api/export.csv"))
    assert len(rows) == 4
    assert rows[0] == HEADER
    by_title = {row[0]: row for row in rows[1:]}
    assert by_title["Lalka"] == ["Lalka", "Bolesław Prus", "1890", "przeczytana", "5", ""]
    assert by_title["Faraon"] == ["Faraon", "Bolesław Prus", "", "do przeczytania", "", ""]


# specky: crit 01M5JNJC6SG6Z827GYCE4XNQJ6
def test_shelves_are_joined_with_semicolons_in_one_column(client):
    book_id = _api_book(client, "Lalka")
    shelf_ids = [
        client.post("/api/shelves", json={"name": name}).json()["id"]
        for name in ("Fantastyka", "Do pracy")
    ]
    client.put(f"/api/books/{book_id}/shelves", json={"shelf_ids": shelf_ids})
    rows = _rows(client.get("/api/export.csv"))
    assert rows[1][5] == "Do pracy;Fantastyka"
    assert len(rows[1]) == 6


# specky: crit 01M5JNJC6SZ9SKKYRQJZVJ7GTR
def test_export_is_a_utf8_bom_csv_attachment_named_lektury(client):
    _api_book(client, "Żółw")
    response = client.get("/api/export.csv")
    assert response.status_code == 200
    assert response.content.startswith(b"\xef\xbb\xbf")
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert response.headers["content-disposition"] == 'attachment; filename="lektury.csv"'
    assert "Żółw" in response.content.decode("utf-8-sig")


def test_values_with_commas_and_quotes_are_quoted(client):
    _api_book(client, 'Ogniem i mieczem, tom "1"')
    assert _rows(client.get("/api/export.csv"))[1][0] == 'Ogniem i mieczem, tom "1"'


def test_cells_that_look_like_formulas_are_neutralised(client):
    _api_book(client, "=HYPERLINK(1)")
    _api_book(client, "+48 opowiadań")
    titles = {row[0] for row in _rows(client.get("/api/export.csv"))[1:]}
    assert titles == {"'=HYPERLINK(1)", "'+48 opowiadań"}


def test_empty_library_exports_only_the_header(client):
    assert _rows(client.get("/api/export.csv")) == [HEADER]


# specky: crit 01M5JNJC6STWJ3EA28NK9ZDT4C
def test_list_and_detail_headers_link_to_the_export(client):
    book_id = _api_book(client, "Lalka")
    for path in ("/", f"/books/{book_id}"):
        header = parse_html(client.get(path).text).find("header")
        link = header.find("a", class_="export-link")
        assert (link.get("href"), link.text) == ("/api/export.csv", "Eksport CSV")
