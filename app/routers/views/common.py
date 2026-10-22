from typing import Annotated, Any

from fastapi import Form, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.models import Book
from app.services import books as book_service
from app.services import shelves as shelf_service
from app.services.books import BookFilters

FormText = Annotated[str, Form()]
StatusFormText = Annotated[str, Form(alias="status")]


def list_context(session: Session, **extra: Any) -> dict[str, Any]:
    """Everything the «Lista» screen and its fragments render from."""
    return {
        "books": book_service.list_books(session, BookFilters()),
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
