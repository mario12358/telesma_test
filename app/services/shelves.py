from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.errors import DomainValidationError, FieldError, NotFoundError
from app.models import Book, Shelf, book_shelves, utc_now
from app.normalization import normalize_text
from app.services.books import get_book

NAME_MAX_LENGTH = 60
SHELF_NOT_FOUND = "Nie znaleziono półki."
DUPLICATE_SHELF_MESSAGE = "Półka o tej nazwie już istnieje."


@dataclass(frozen=True)
class ShelfWithCount:
    id: int
    name: str
    book_count: int


def list_shelves(session: Session) -> list[ShelfWithCount]:
    """Alphabetical, case-insensitive order (R5); empty shelves included (R4)."""
    statement = (
        select(Shelf.id, Shelf.name, func.count(book_shelves.c.book_id))
        .outerjoin(book_shelves, book_shelves.c.shelf_id == Shelf.id)
        .group_by(Shelf.id)
        .order_by(Shelf.name.collate("NOCASE"), Shelf.id)
    )
    return [ShelfWithCount(*row) for row in session.execute(statement)]


def get_shelf(session: Session, shelf_id: int) -> ShelfWithCount:
    for shelf in list_shelves(session):
        if shelf.id == shelf_id:
            return shelf
    raise NotFoundError(SHELF_NOT_FOUND)


def _validated_name(session: Session, raw_name: str) -> str:
    name = raw_name.strip()
    if not name:
        raise DomainValidationError([FieldError("name", "Nazwa półki jest wymagana.")])
    if len(name) > NAME_MAX_LENGTH:
        message = f"Nazwa półki może mieć najwyżej {NAME_MAX_LENGTH} znaków."
        raise DomainValidationError([FieldError("name", message)])
    if session.scalar(select(Shelf.id).where(Shelf.name_norm == normalize_text(name))):
        raise DomainValidationError([FieldError("name", DUPLICATE_SHELF_MESSAGE)])
    return name


def create_shelf(session: Session, raw_name: str) -> ShelfWithCount:
    name = _validated_name(session, raw_name)
    shelf = Shelf(name=name, name_norm=normalize_text(name))
    session.add(shelf)
    session.commit()
    return ShelfWithCount(id=shelf.id, name=shelf.name, book_count=0)


def delete_shelf(session: Session, shelf_id: int) -> None:
    """Removes the shelf and its links; the books themselves stay."""
    shelf = session.get(Shelf, shelf_id)
    if shelf is None:
        raise NotFoundError(SHELF_NOT_FOUND)
    session.delete(shelf)
    session.commit()


def set_book_shelves(session: Session, book_id: int, shelf_ids: list[int]) -> Book:
    """Replaces the book's full shelf list."""
    book = get_book(session, book_id)
    requested_ids = list(dict.fromkeys(shelf_ids))
    shelves = list(session.scalars(select(Shelf).where(Shelf.id.in_(requested_ids))))
    missing_ids = sorted(set(requested_ids) - {shelf.id for shelf in shelves})
    if missing_ids:
        listed = ", ".join(str(shelf_id) for shelf_id in missing_ids)
        raise DomainValidationError(
            [FieldError("shelf_ids", f"Nie istnieje półka o id: {listed}.")]
        )
    book.shelves = shelves
    book.updated_at = utc_now()
    session.commit()
    return get_book(session, book_id)
