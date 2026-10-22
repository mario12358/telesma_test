from typing import Annotated

from fastapi import APIRouter, Form, Request, status
from fastapi.responses import HTMLResponse, Response

from app.db import SessionDep
from app.errors import DomainValidationError
from app.forms import errors_by_field, optional_int
from app.routers.views.common import FormFilters, FormText, QueryFilters, list_context, redirect
from app.schemas import BookCreate
from app.services import books as book_service
from app.statuses import BookStatus
from app.templating import is_htmx, render

router = APIRouter(tags=["views"])


@router.get("/", response_class=HTMLResponse, summary="Ekran «Lista» z filtrami")
def list_page(request: Request, session: SessionDep, filters: QueryFilters) -> HTMLResponse:
    template = "partials/book_list.html" if is_htmx(request) else "list.html"
    return render(request, template, list_context(session, filters))


@router.post("/books", summary="Dodanie książki z formularza")
def add_book(
    request: Request,
    session: SessionDep,
    filters: FormFilters,
    title: FormText = "",
    author: FormText = "",
    year: FormText = "",
) -> Response:
    submitted = {"title": title, "author": author, "year": year}
    try:
        book_data = BookCreate(title=title, author=author, year=optional_int(year, "year"))
        book_service.create_book(session, book_data)
    except DomainValidationError as error:
        context = list_context(session, filters, form=submitted, errors=errors_by_field(error))
        template = "partials/add_book_form.html" if is_htmx(request) else "list.html"
        return render(request, template, context, status.HTTP_422_UNPROCESSABLE_CONTENT)
    if not is_htmx(request):
        return redirect("/")
    context = list_context(session, filters, focus_title=True)
    return render(request, "partials/add_book_response.html", context)


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
        return redirect("/")
    book = book_service.update_book(session, book_id, {"status": new_status})
    if not is_htmx(request):
        return redirect("/")
    return render(request, "partials/book_row.html", {"book": book})
