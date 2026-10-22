from datetime import UTC, datetime, timedelta

import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError

from app.models import Base, Book, Note, Shelf, book_shelves
from app.normalization import normalize_text


def _book(title="Lalka", author="Bolesław Prus", **fields) -> Book:
    return Book(
        title=title,
        author=author,
        title_norm=normalize_text(title),
        author_norm=normalize_text(author),
        **fields,
    )


def _shelf(name: str) -> Shelf:
    return Shelf(name=name, name_norm=normalize_text(name))


def test_migration_creates_all_tables_as_strict(session):
    rows = session.execute(text("SELECT name, sql FROM sqlite_master WHERE type='table'")).all()
    created = {name: sql for name, sql in rows}
    for table in ("books", "shelves", "book_shelves", "notes"):
        assert table in created
        assert created[table].rstrip().endswith("STRICT")


def test_orm_models_match_the_migration(client, app):
    with app.state.engine.connect() as connection:
        differences = compare_metadata(MigrationContext.configure(connection), Base.metadata)
    assert differences == []


def test_normalize_text_trims_collapses_spaces_and_lowercases():
    assert normalize_text("  Bolesław   PRUS ") == "bolesław prus"


def test_database_rejects_duplicate_normalized_title_and_author(session):
    session.add(_book("Lalka", "Bolesław Prus"))
    session.commit()
    session.add(_book(" lalka  ", "bolesław  PRUS"))
    with pytest.raises(IntegrityError, match="title_norm"):
        session.commit()


def test_database_accepts_same_title_with_other_author(session):
    session.add_all([_book("Lalka", "Bolesław Prus"), _book("Lalka", "Ktoś Inny")])
    session.commit()
    assert session.scalar(select(func.count()).select_from(Book)) == 2


def test_deleting_book_cascades_to_notes_and_shelf_links(session):
    fantasy, work = _shelf("Fantastyka"), _shelf("Do pracy")
    book = _book(shelves=[fantasy, work])
    book.notes = [Note(content="pierwsza"), Note(content="druga")]
    session.add(book)
    session.commit()

    session.execute(text("DELETE FROM books WHERE id = :id"), {"id": book.id})
    session.commit()

    assert session.scalar(select(func.count()).select_from(Note)) == 0
    assert session.scalar(select(func.count()).select_from(book_shelves)) == 0
    assert session.scalar(select(func.count()).select_from(Shelf)) == 2


def test_shelf_name_is_unique_regardless_of_case(session):
    session.add(_shelf("Fantastyka"))
    session.commit()
    session.add(_shelf("fantastyka"))
    with pytest.raises(IntegrityError, match="name_norm"):
        session.commit()


@pytest.mark.parametrize(
    ("status", "rating"),
    [("to_read", 3), ("reading", 0), ("read", 6), ("unknown", None)],
)
def test_database_rejects_invalid_status_or_rating(session, status, rating):
    session.add(_book(status=status, rating=rating))
    with pytest.raises(IntegrityError, match="CHECK"):
        session.commit()


def test_strict_table_rejects_text_in_integer_column(session):
    with pytest.raises(IntegrityError):
        session.execute(
            text(
                "INSERT INTO books (title, author, title_norm, author_norm, year, status,"
                " created_at, updated_at) VALUES ('a', 'b', 'a', 'b', 'abc', 'to_read', 'x', 'x')"
            )
        )


def test_timestamps_round_trip_as_utc_and_sort_chronologically(session):
    older = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    session.add_all(
        [
            _book("A", "X", updated_at=older),
            _book("B", "X", updated_at=older + timedelta(microseconds=1)),
        ]
    )
    session.commit()
    stored = session.execute(text("SELECT updated_at FROM books ORDER BY updated_at")).scalars()
    assert list(stored) == ["2026-01-01T12:00:00.000000Z", "2026-01-01T12:00:00.000001Z"]
    session.expire_all()
    book = session.scalars(select(Book).where(Book.title == "A")).one()
    assert book.updated_at == older
    assert book.created_at.tzinfo is UTC
