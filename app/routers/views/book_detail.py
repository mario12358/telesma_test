from typing import Any, Literal

from fastapi import APIRouter, Request, status
from fastapi.responses import HTMLResponse, Response

from app.db import SessionDep
from app.errors import DomainValidationError, FieldError
from app.forms import errors_by_field, optional_int
from app.models import Book
from app.routers.views.common import FormText, StatusFormText, redirect
from app.services import books as book_service
from app.statuses import BookStatus
from app.templating import is_htmx, render

router = APIRouter(tags=["views"])

EditableField = Literal["title", "author", "year", "status", "rating"]
STATUS_MESSAGE = "Niedozwolona wartość."


def _values(book: Book) -> dict[str, Any]:
    return {
        "title": book.title,
        "author": book.author,
        "year": book.year,
        "status": book.status,
        "rating": book.rating,
    }


def _submitted_values(raw: dict[str, str]) -> dict[str, Any]:
    """Re-display what the user typed; the rating widget needs a number to draw the stars."""
    rating = raw.get("rating", "")
    return {**raw, "rating": int(rating) if rating.isdigit() else None}


def _parse_status(raw: str) -> BookStatus:
    try:
        return BookStatus(raw)
    except ValueError:
        raise DomainValidationError([FieldError("status", STATUS_MESSAGE)]) from None


def _parse_field(field: str, raw: str) -> Any:
    if field in ("year", "rating"):
        return optional_int(raw, field)
    if field == "status":
        return _parse_status(raw)
    return raw


def _detail_context(book: Book, **extra: Any) -> dict[str, Any]:
    return {"book": book, "values": _values(book), "errors": {}, **extra}


@router.get("/books/{book_id}", response_class=HTMLResponse, summary="Ekran «Szczegóły»")
def detail_page(request: Request, book_id: int, session: SessionDep) -> HTMLResponse:
    return render(request, "detail.html", _detail_context(book_service.get_book(session, book_id)))


@router.post("/books/{book_id}/fields/{field}", summary="Zapis jednego pola (edycja w miejscu)")
def save_field(
    request: Request,
    book_id: int,
    field: EditableField,
    session: SessionDep,
    title: FormText = "",
    author: FormText = "",
    year: FormText = "",
    status_value: StatusFormText = "",
    rating: FormText = "",
) -> HTMLResponse:
    raw = {"title": title, "author": author, "year": year, "status": status_value, "rating": rating}
    book = book_service.get_book(session, book_id)
    try:
        changes = {field: _parse_field(field, raw[field])}
        updated = book_service.update_book(session, book.id, changes)
    except DomainValidationError as error:
        values = {**_values(book), field: _submitted_values(raw)[field]}
        context = _detail_context(book, field=field, values=values, errors=errors_by_field(error))
        return render(
            request,
            "partials/detail_field_response.html",
            context,
            status.HTTP_422_UNPROCESSABLE_CONTENT,
        )
    context = _detail_context(updated, field=field, saved=field)
    return render(request, "partials/detail_field_response.html", context)


@router.post("/books/{book_id}", summary="Zapis całego formularza (bez JavaScriptu)")
def save_book(
    request: Request,
    book_id: int,
    session: SessionDep,
    title: FormText = "",
    author: FormText = "",
    year: FormText = "",
    status_value: StatusFormText = "",
    rating: FormText = "",
) -> Response:
    book = book_service.get_book(session, book_id)
    raw = {"title": title, "author": author, "year": year, "status": status_value, "rating": rating}
    try:
        changes = {field: _parse_field(field, value) for field, value in raw.items()}
        book_service.update_book(session, book.id, changes)
    except DomainValidationError as error:
        values = _submitted_values(raw)
        context = _detail_context(book, values=values, errors=errors_by_field(error))
        return render(request, "detail.html", context, status.HTTP_422_UNPROCESSABLE_CONTENT)
    return redirect(f"/books/{book_id}")


@router.get("/books/{book_id}/delete", response_class=HTMLResponse, summary="Potwierdzenie")
def confirm_delete_book(request: Request, book_id: int, session: SessionDep) -> HTMLResponse:
    book = book_service.get_book(session, book_id)
    return render(request, "confirm_delete_book.html", {"book": book})


@router.post("/books/{book_id}/delete", summary="Usunięcie książki")
def delete_book(request: Request, book_id: int, session: SessionDep) -> Response:
    book_service.delete_book(session, book_id)
    if is_htmx(request):
        return Response(headers={"HX-Redirect": "/"})
    return redirect("/")
