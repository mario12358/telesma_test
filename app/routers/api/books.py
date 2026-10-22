from fastapi import APIRouter, Response, status

from app.db import SessionDep
from app.schemas import BookCreate, BookDetail, BookRead, BookUpdate
from app.services import books as book_service
from app.services.books import BookFilters
from app.statuses import BookStatus

router = APIRouter(prefix="/api/books", tags=["books"])


@router.get("", summary="Lista książek z filtrami")
def list_books(
    session: SessionDep,
    status: BookStatus | None = None,
    shelf: int | None = None,
    q: str | None = None,
) -> list[BookRead]:
    books = book_service.list_books(session, BookFilters(status=status, shelf_id=shelf, query=q))
    return [BookRead.model_validate(book) for book in books]


@router.post("", status_code=status.HTTP_201_CREATED, summary="Dodanie książki")
def create_book(payload: BookCreate, session: SessionDep, response: Response) -> BookDetail:
    book = book_service.create_book(session, payload)
    response.headers["Location"] = f"/api/books/{book.id}"
    return BookDetail.model_validate(book)


@router.get("/{book_id}", summary="Szczegóły książki z półkami i notatkami")
def get_book(book_id: int, session: SessionDep) -> BookDetail:
    return BookDetail.model_validate(book_service.get_book(session, book_id))


@router.patch("/{book_id}", summary="Zmiana wybranych pól książki")
def update_book(book_id: int, payload: BookUpdate, session: SessionDep) -> BookDetail:
    changes = payload.model_dump(exclude_unset=True)
    return BookDetail.model_validate(book_service.update_book(session, book_id, changes))


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Usunięcie książki")
def delete_book(book_id: int, session: SessionDep) -> None:
    book_service.delete_book(session, book_id)
