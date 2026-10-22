from typing import Annotated, Any

from fastapi import APIRouter, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy.orm import Session

from app.db import SessionDep
from app.errors import DomainValidationError
from app.forms import errors_by_field, optional_int
from app.schemas import BookCreate
from app.services import books as book_service
from app.services.books import BookFilters
from app.statuses import BookStatus
from app.templating import is_htmx, render

router = APIRouter(tags=["views"])

FormText = Annotated[str, Form()]


def _list_context(session: Session, **extra: Any) -> dict[str, Any]:
    return {
        "books": book_service.list_books(session, BookFilters()),
        "form": {},
        "errors": {},
        **extra,
    }


def _redirect(url: str) -> RedirectResponse:
    return RedirectResponse(url, status_code=status.HTTP_303_SEE_OTHER)


@router.get("/", response_class=HTMLResponse, summary="Ekran «Lista»")
def list_page(request: Request, session: SessionDep) -> HTMLResponse:
    return render(request, "list.html", _list_context(session))


@router.post("/books", summary="Dodanie książki z formularza")
def add_book(
    request: Request,
    session: SessionDep,
    title: FormText = "",
    author: FormText = "",
    year: FormText = "",
) -> Response:
    submitted = {"title": title, "author": author, "year": year}
    try:
        book_data = BookCreate(title=title, author=author, year=optional_int(year, "year"))
        book_service.create_book(session, book_data)
    except DomainValidationError as error:
        context = _list_context(session, form=submitted, errors=errors_by_field(error))
        template = "partials/add_book_form.html" if is_htmx(request) else "list.html"
        return render(request, template, context, status.HTTP_422_UNPROCESSABLE_CONTENT)
    if not is_htmx(request):
        return _redirect("/")
    return render(
        request, "partials/add_book_response.html", _list_context(session, focus_title=True)
    )


@router.post("/books/{book_id}/status", summary="Zmiana statusu z listy")
def change_status(
    request: Request,
    book_id: int,
    session: SessionDep,
    status_value: Annotated[str, Form(alias="status")] = "",
) -> Response:
    try:
        new_status = BookStatus(status_value)
    except ValueError:
        return _redirect("/")
    book = book_service.update_book(session, book_id, {"status": new_status})
    if not is_htmx(request):
        return _redirect("/")
    return render(request, "partials/book_row.html", {"book": book})
