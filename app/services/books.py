from dataclasses import dataclass
from datetime import date
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.errors import DomainValidationError, FieldError, NotFoundError
from app.models import Book, Shelf, utc_now
from app.normalization import normalize_text
from app.schemas import BookCreate
from app.statuses import RATEABLE_STATUSES, BookStatus

TITLE_MAX_LENGTH = 200
AUTHOR_MAX_LENGTH = 120
EARLIEST_YEAR = 1450
RATING_RANGE = range(1, 6)

BOOK_NOT_FOUND = "Nie znaleziono książki."
DUPLICATE_MESSAGE = "Ta książka jest już na liście (ten sam tytuł i autor)."
RATING_STATUS_MESSAGE = "Ocenę można wystawić tylko przy statusie «czytam» lub «przeczytana»."


@dataclass(frozen=True)
class BookFilters:
    status: BookStatus | None = None
    shelf_id: int | None = None
    query: str | None = None


def current_year() -> int:
    return date.today().year


def _required_text(value: str | None, field: str, label: str, max_length: int) -> str | FieldError:
    stripped = (value or "").strip()
    if not stripped:
        return FieldError(field, f"{label} jest wymagany.")
    if len(stripped) > max_length:
        return FieldError(field, f"{label} może mieć najwyżej {max_length} znaków.")
    return stripped


def _year_error(year: int | None) -> FieldError | None:
    latest = current_year() + 1
    if year is not None and not EARLIEST_YEAR <= year <= latest:
        return FieldError("year", f"Rok musi być z zakresu {EARLIEST_YEAR}–{latest}.")
    return None


def _rating_error(rating: int | None, status: BookStatus) -> FieldError | None:
    if rating is None:
        return None
    if rating not in RATING_RANGE:
        return FieldError("rating", "Ocena musi być liczbą od 1 do 5.")
    if status not in RATEABLE_STATUSES:
        return FieldError("rating", RATING_STATUS_MESSAGE)
    return None


def _duplicate_error(
    session: Session, title: str, author: str, own_id: int | None
) -> FieldError | None:
    duplicate = select(Book.id).where(
        Book.title_norm == normalize_text(title), Book.author_norm == normalize_text(author)
    )
    if own_id is not None:
        duplicate = duplicate.where(Book.id != own_id)
    return FieldError("title", DUPLICATE_MESSAGE) if session.scalar(duplicate) else None


def _validated_fields(
    session: Session, fields: dict[str, Any], own_id: int | None
) -> dict[str, Any]:
    errors: list[FieldError] = []
    title = _required_text(fields["title"], "title", "Tytuł", TITLE_MAX_LENGTH)
    author = _required_text(fields["author"], "author", "Autor", AUTHOR_MAX_LENGTH)
    for checked in (title, author):
        if isinstance(checked, FieldError):
            errors.append(checked)
    if fields["status"] is None:
        errors.append(FieldError("status", "Status jest wymagany."))
    status = BookStatus(fields["status"] or BookStatus.TO_READ)
    errors.extend(
        error
        for error in (_year_error(fields["year"]), _rating_error(fields["rating"], status))
        if error is not None
    )
    if not errors and isinstance(title, str) and isinstance(author, str):
        duplicate = _duplicate_error(session, title, author, own_id)
        errors.extend([duplicate] if duplicate else [])
    if errors:
        raise DomainValidationError(errors)
    return {**fields, "title": title, "author": author, "status": status}


def _apply(book: Book, fields: dict[str, Any]) -> None:
    book.title = fields["title"]
    book.author = fields["author"]
    book.title_norm = normalize_text(fields["title"])
    book.author_norm = normalize_text(fields["author"])
    book.year = fields["year"]
    book.status = fields["status"].value
    book.rating = fields["rating"]
    book.updated_at = utc_now()


def create_book(session: Session, data: BookCreate) -> Book:
    fields = _validated_fields(session, data.model_dump(), own_id=None)
    book = Book()
    _apply(book, fields)
    book.created_at = book.updated_at
    session.add(book)
    session.commit()
    return get_book(session, book.id)


def get_book(session: Session, book_id: int) -> Book:
    book = session.scalar(
        select(Book)
        .where(Book.id == book_id)
        .options(selectinload(Book.shelves), selectinload(Book.notes))
        .execution_options(populate_existing=True)
    )
    if book is None:
        raise NotFoundError(BOOK_NOT_FOUND)
    return book


def list_books(session: Session, filters: BookFilters) -> list[Book]:
    statement = select(Book).options(selectinload(Book.shelves))
    if filters.status is not None:
        statement = statement.where(Book.status == filters.status.value)
    if filters.shelf_id is not None:
        statement = statement.where(Book.shelves.any(Shelf.id == filters.shelf_id))
    normalized_query = normalize_text(filters.query or "")
    if normalized_query:
        statement = statement.where(
            or_(
                Book.title_norm.contains(normalized_query, autoescape=True),
                Book.author_norm.contains(normalized_query, autoescape=True),
            )
        )
    statement = statement.order_by(Book.updated_at.desc(), Book.id.desc())
    return list(session.scalars(statement))


def _merged_changes(book: Book, changes: dict[str, Any]) -> dict[str, Any]:
    merged = {
        "title": book.title,
        "author": book.author,
        "year": book.year,
        "status": BookStatus(book.status),
        "rating": book.rating,
        **changes,
    }
    if (
        "status" in changes
        and changes["status"] not in RATEABLE_STATUSES
        and "rating" not in changes
    ):
        merged["rating"] = None
    return merged


def update_book(session: Session, book_id: int, changes: dict[str, Any]) -> Book:
    """Apply only the given fields; R2 (S1): moving to `to_read` clears the rating."""
    book = get_book(session, book_id)
    fields = _validated_fields(session, _merged_changes(book, changes), own_id=book.id)
    _apply(book, fields)
    session.commit()
    return get_book(session, book.id)


def delete_book(session: Session, book_id: int) -> None:
    session.delete(get_book(session, book_id))
    session.commit()
