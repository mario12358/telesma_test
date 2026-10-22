from typing import Annotated, Any

from fastapi import Depends, Form, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.models import Book
from app.services import books as book_service
from app.services import shelves as shelf_service
from app.services.books import BookFilters
from app.statuses import BookStatus

FormText = Annotated[str, Form()]
StatusFormText = Annotated[str, Form(alias="status")]


def parse_filters(status: str | None, shelf: str | None, q: str | None) -> BookFilters:
    """Filters come from the URL or a form; unknown values mean «no filter», never an error."""
    status_value = status if status in {member.value for member in BookStatus} else None
    shelf_text = (shelf or "").strip()
    return BookFilters(
        status=BookStatus(status_value) if status_value else None,
        shelf_id=int(shelf_text) if shelf_text.isdigit() else None,
        query=(q or "").strip() or None,
    )


def query_filters(
    status: str | None = None, shelf: str | None = None, q: str | None = None
) -> BookFilters:
    return parse_filters(status, shelf, q)


def form_filters(
    status: StatusFormText = "", shelf: FormText = "", q: FormText = ""
) -> BookFilters:
    return parse_filters(status, shelf, q)


QueryFilters = Annotated[BookFilters, Depends(query_filters)]
FormFilters = Annotated[BookFilters, Depends(form_filters)]


def list_context(
    session: Session, filters: BookFilters | None = None, **extra: Any
) -> dict[str, Any]:
    """Everything the «Lista» screen and its fragments render from."""
    active_filters = filters or BookFilters()
    return {
        "books": book_service.list_books(session, active_filters),
        "filters": active_filters,
        "shelves": shelf_service.list_shelves(session),
        "form": {},
        "errors": {},
        "shelf_form": {},
        "shelf_errors": {},
        **extra,
    }


def book_values(book: Book) -> dict[str, Any]:
    return {
        "title": book.title,
        "author": book.author,
        "year": book.year,
        "status": book.status,
        "rating": book.rating,
    }


def detail_page_context(session: Session, book: Book, **extra: Any) -> dict[str, Any]:
    """Everything the «Szczegóły» screen renders from; `values` holds the field values shown."""
    return {
        "book": book,
        "values": book_values(book),
        "shelves": shelf_service.list_shelves(session),
        "errors": {},
        "note_form": {},
        "note_errors": {},
        **extra,
    }


def redirect(url: str) -> RedirectResponse:
    return RedirectResponse(url, status_code=status.HTTP_303_SEE_OTHER)
