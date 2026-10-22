from typing import Annotated

from fastapi import APIRouter, Form, Request, status
from fastapi.responses import Response

from app.db import SessionDep
from app.errors import DomainValidationError
from app.forms import errors_by_field
from app.routers.views.common import FormText, detail_page_context, redirect
from app.services import books as book_service
from app.services import notes as note_service
from app.services import shelves as shelf_service
from app.templating import is_htmx, render

router = APIRouter(tags=["views"])


@router.post("/books/{book_id}/shelves", summary="Półki książki (pola wyboru)")
def save_book_shelves(
    request: Request,
    book_id: int,
    session: SessionDep,
    shelf_ids: Annotated[list[int], Form()] = [],  # noqa: B006 — FastAPI copies defaults
) -> Response:
    book = shelf_service.set_book_shelves(session, book_id, shelf_ids)
    if not is_htmx(request):
        return redirect(f"/books/{book_id}")
    context = detail_page_context(session, book, shelves_saved=True)
    return render(request, "partials/book_shelves.html", context)


@router.post("/books/{book_id}/notes", summary="Dodanie notatki")
def add_note(
    request: Request, book_id: int, session: SessionDep, content: FormText = ""
) -> Response:
    try:
        note_service.create_note(session, book_id, content)
    except DomainValidationError as error:
        book = book_service.get_book(session, book_id)
        context = detail_page_context(
            session, book, note_form={"content": content}, note_errors=errors_by_field(error)
        )
        template = "partials/notes_section.html" if is_htmx(request) else "detail.html"
        return render(request, template, context, status.HTTP_422_UNPROCESSABLE_CONTENT)
    if not is_htmx(request):
        return redirect(f"/books/{book_id}")
    book = book_service.get_book(session, book_id)
    return render(
        request, "partials/notes_section.html", detail_page_context(session, book, focus_note=True)
    )


@router.post("/notes/{note_id}/delete", summary="Usunięcie notatki")
def delete_note(request: Request, note_id: int, session: SessionDep) -> Response:
    book_id = note_service.delete_note(session, note_id)
    if not is_htmx(request):
        return redirect(f"/books/{book_id}")
    book = book_service.get_book(session, book_id)
    return render(request, "partials/notes_section.html", detail_page_context(session, book))
