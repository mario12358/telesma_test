from datetime import timedelta

import pytest
from sqlalchemy import func, select

from app.errors import DomainValidationError, NotFoundError
from app.models import Book, Note, Shelf, book_shelves
from app.normalization import normalize_text
from app.schemas import BookCreate
from app.services import books as book_service
from app.services.books import BookFilters
from app.statuses import BookStatus


def _create(session, title="Lalka", author="Bolesław Prus", **fields) -> Book:
    return book_service.create_book(session, BookCreate(title=title, author=author, **fields))


def _errors(excinfo) -> dict[str, str]:
    return {error.field: error.message for error in excinfo.value.errors}


def _shelf(session, name: str) -> Shelf:
    shelf = Shelf(name=name, name_norm=normalize_text(name))
    session.add(shelf)
    session.commit()
    return shelf


# specky: crit 01M5JNJBNHHKH0CPABRA46YMVD
@pytest.mark.parametrize("title", ["", "   ", "\t\n"])
def test_create_rejects_blank_title(session, title):
    with pytest.raises(DomainValidationError) as excinfo:
        _create(session, title=title)
    assert _errors(excinfo) == {"title": "Tytuł jest wymagany."}


def test_create_trims_title_and_accepts_exactly_200_characters(session):
    book = _create(session, title=f"  {'a' * 200}  ")
    assert book.title == "a" * 200


def test_create_rejects_title_longer_than_200_after_trimming(session):
    with pytest.raises(DomainValidationError) as excinfo:
        _create(session, title="a" * 201)
    assert "title" in _errors(excinfo)


@pytest.mark.parametrize(("author", "valid"), [("", False), ("a" * 120, True), ("a" * 121, False)])
def test_create_validates_author_length(session, author, valid):
    if valid:
        assert _create(session, author=author).author == author
        return
    with pytest.raises(DomainValidationError) as excinfo:
        _create(session, author=author)
    assert "author" in _errors(excinfo)


# specky: crit 01M5JNJBNJ5FWS6X307GYV86AQ
@pytest.mark.parametrize(("offset_from_now", "valid"), [(None, True), (1, True), (2, False)])
def test_create_validates_year_against_current_year(session, offset_from_now, valid):
    year = None if offset_from_now is None else book_service.current_year() + offset_from_now
    if valid:
        assert _create(session, year=year).year == year
        return
    with pytest.raises(DomainValidationError) as excinfo:
        _create(session, year=year)
    assert "year" in _errors(excinfo)


@pytest.mark.parametrize(("year", "valid"), [(1449, False), (1450, True)])
def test_create_validates_earliest_year(session, year, valid):
    if valid:
        assert _create(session, year=year).year == 1450
        return
    with pytest.raises(DomainValidationError) as excinfo:
        _create(session, year=year)
    assert _errors(excinfo)["year"].startswith("Rok musi być z zakresu 1450")


# specky: crit 01M5JNJBNJ3G2PT3YYPX92YS5X
def test_create_defaults_status_to_read_and_sets_utc_timestamps(session):
    book = _create(session)
    assert book.status == BookStatus.TO_READ
    assert book.created_at.utcoffset() == timedelta(0)
    assert book.updated_at == book.created_at


def test_create_reports_every_invalid_field_at_once(session):
    with pytest.raises(DomainValidationError) as excinfo:
        _create(session, title="", author="", year=1000)
    assert set(_errors(excinfo)) == {"title", "author", "year"}


# specky: crit 01M5JNJD03R9G6CQ77028G996V
def test_create_rejects_duplicate_after_normalization(session):
    _create(session, title="Lalka", author="Bolesław Prus")
    with pytest.raises(DomainValidationError) as excinfo:
        _create(session, title=" lalka  ", author="bolesław  PRUS")
    assert _errors(excinfo) == {"title": book_service.DUPLICATE_MESSAGE}
    assert session.scalar(select(func.count()).select_from(Book)) == 1


# specky: crit 01M5JNJD032FE1JGM0AFGAN4V2
def test_create_accepts_same_title_with_other_author(session):
    _create(session, title="Lalka", author="Bolesław Prus")
    _create(session, title="Lalka", author="Ktoś Inny")
    assert session.scalar(select(func.count()).select_from(Book)) == 2


def test_update_to_duplicate_of_another_book_is_rejected(session):
    _create(session, title="Lalka")
    other = _create(session, title="Faraon")
    with pytest.raises(DomainValidationError) as excinfo:
        book_service.update_book(session, other.id, {"title": "LALKA"})
    assert "title" in _errors(excinfo)


def test_update_keeping_own_title_is_not_a_duplicate(session):
    book = _create(session)
    assert book_service.update_book(session, book.id, {"title": "Lalka", "year": 1890}).year == 1890


# specky: crit 01M5JNJD26WJ3MMGENKV9M116X
def test_rating_is_rejected_for_book_to_read(session):
    book = _create(session)
    with pytest.raises(DomainValidationError) as excinfo:
        book_service.update_book(session, book.id, {"rating": 4})
    assert _errors(excinfo) == {"rating": book_service.RATING_STATUS_MESSAGE}


# specky: crit 01M5JNJD26AKTJC1MJED59BPX6
def test_preliminary_rating_while_reading_survives_status_change_to_read(session):
    book = _create(session, status=BookStatus.READING)
    book_service.update_book(session, book.id, {"rating": 4})
    updated = book_service.update_book(session, book.id, {"status": BookStatus.READ})
    assert (updated.status, updated.rating) == (BookStatus.READ, 4)


# specky: crit 01M5JNJD265HM74ETSWG8NSMHA
@pytest.mark.parametrize("start", [BookStatus.READING, BookStatus.READ])
def test_status_change_to_read_later_clears_rating(session, start):
    book = _create(session, status=start, rating=5)
    updated = book_service.update_book(session, book.id, {"status": BookStatus.TO_READ})
    assert updated.rating is None


def test_status_change_between_rateable_statuses_keeps_rating(session):
    book = _create(session, status=BookStatus.READ, rating=3)
    assert book_service.update_book(session, book.id, {"status": BookStatus.READING}).rating == 3


def test_status_to_read_with_explicit_rating_in_same_request_is_rejected(session):
    book = _create(session, status=BookStatus.READ, rating=3)
    with pytest.raises(DomainValidationError) as excinfo:
        book_service.update_book(session, book.id, {"status": BookStatus.TO_READ, "rating": 3})
    assert "rating" in _errors(excinfo)


# specky: crit 01M5JNJD26RDSKJT1RQ58DD2PR
@pytest.mark.parametrize("rating", [0, 6, -1])
def test_rating_outside_one_to_five_is_rejected(session, rating):
    book = _create(session, status=BookStatus.READ)
    with pytest.raises(DomainValidationError) as excinfo:
        book_service.update_book(session, book.id, {"rating": rating})
    assert _errors(excinfo) == {"rating": "Ocena musi być liczbą od 1 do 5."}


def test_null_rating_clears_existing_rating(session):
    book = _create(session, status=BookStatus.READ, rating=2)
    assert book_service.update_book(session, book.id, {"rating": None}).rating is None


def test_partial_update_changes_only_given_field_and_bumps_updated_at(session):
    book = _create(session, year=1890)
    before = book.updated_at
    updated = book_service.update_book(session, book.id, {"author": "B. Prus"})
    assert (updated.title, updated.author, updated.year) == ("Lalka", "B. Prus", 1890)
    assert updated.updated_at > before


def test_update_rejects_explicit_null_for_required_fields(session):
    book = _create(session)
    with pytest.raises(DomainValidationError) as excinfo:
        book_service.update_book(session, book.id, {"title": None, "status": None})
    assert set(_errors(excinfo)) == {"title", "status"}


def test_get_missing_book_raises_not_found(session):
    with pytest.raises(NotFoundError):
        book_service.get_book(session, 999)


def test_delete_removes_book_notes_and_shelf_links_but_keeps_shelves(session):
    fantasy, work = _shelf(session, "Fantastyka"), _shelf(session, "Do pracy")
    book = _create(session)
    book.shelves = [fantasy, work]
    book.notes = [Note(content="a"), Note(content="b")]
    session.commit()

    book_service.delete_book(session, book.id)

    assert session.scalar(select(func.count()).select_from(Note)) == 0
    assert session.scalar(select(func.count()).select_from(book_shelves)) == 0
    assert session.scalar(select(func.count()).select_from(Shelf)) == 2
    with pytest.raises(NotFoundError):
        book_service.delete_book(session, book.id)


def _titles(books) -> list[str]:
    return [book.title for book in books]


@pytest.fixture
def library(session):
    fantasy = _shelf(session, "Fantastyka")
    _create(session, title="Lalka", author="Bolesław Prus", status=BookStatus.READING)
    _create(session, title="Faraon", author="Bolesław Prus", status=BookStatus.READ)
    witcher = _create(session, title="Wiedźmin", author="Andrzej Sapkowski")
    _create(session, title="Prusy Wschodnie", author="Ktoś", status=BookStatus.READING)
    witcher.shelves = [fantasy]
    session.commit()
    return fantasy


def test_list_is_sorted_by_updated_at_descending(session, library):
    assert _titles(book_service.list_books(session, BookFilters())) == [
        "Prusy Wschodnie",
        "Wiedźmin",
        "Faraon",
        "Lalka",
    ]


def test_recently_updated_book_moves_to_top(session, library):
    lalka = session.scalars(select(Book).where(Book.title == "Lalka")).one()
    book_service.update_book(session, lalka.id, {"year": 1890})
    assert _titles(book_service.list_books(session, BookFilters()))[0] == "Lalka"


def test_query_matches_title_or_author_case_insensitively(session, library):
    found = book_service.list_books(session, BookFilters(query="PRUS"))
    assert set(_titles(found)) == {"Lalka", "Faraon", "Prusy Wschodnie"}


def test_query_matches_non_ascii_case_insensitively(session, library):
    assert _titles(book_service.list_books(session, BookFilters(query="WIEDŹ"))) == ["Wiedźmin"]


def test_filters_combine_status_query_and_shelf(session, library):
    reading_prus = BookFilters(status=BookStatus.READING, query="prus")
    assert set(_titles(book_service.list_books(session, reading_prus))) == {
        "Lalka",
        "Prusy Wschodnie",
    }
    on_shelf = BookFilters(shelf_id=library.id, query="sapkowski")
    assert _titles(book_service.list_books(session, on_shelf)) == ["Wiedźmin"]
    assert book_service.list_books(session, BookFilters(shelf_id=library.id, query="prus")) == []


def test_query_treats_like_wildcards_literally(session, library):
    assert book_service.list_books(session, BookFilters(query="%")) == []
