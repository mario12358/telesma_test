from typing import Annotated, Any

from fastapi import Form, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.services import books as book_service
from app.services import shelves as shelf_service
from app.services.books import BookFilters

FormText = Annotated[str, Form()]


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


def redirect(url: str) -> RedirectResponse:
    return RedirectResponse(url, status_code=status.HTTP_303_SEE_OTHER)
