from dataclasses import replace

from fastapi import APIRouter, Request, status
from fastapi.responses import HTMLResponse, Response

from app.db import SessionDep
from app.errors import DomainValidationError
from app.forms import errors_by_field
from app.routers.views.common import FormFilters, FormText, list_context, redirect
from app.services import shelves as shelf_service
from app.templating import is_htmx, render

router = APIRouter(tags=["views"])


@router.post("/shelves", summary="Dodanie półki z sekcji «Półki»")
def add_shelf(
    request: Request, session: SessionDep, filters: FormFilters, name: FormText = ""
) -> Response:
    try:
        shelf_service.create_shelf(session, name)
    except DomainValidationError as error:
        context = list_context(
            session,
            filters,
            shelf_form={"name": name},
            shelf_errors=errors_by_field(error),
            shelves_open=True,
        )
        template = "partials/shelves_section.html" if is_htmx(request) else "list.html"
        return render(request, template, context, status.HTTP_422_UNPROCESSABLE_CONTENT)
    if not is_htmx(request):
        return redirect("/")
    context = list_context(session, filters, shelves_open=True)
    return render(request, "partials/shelves_response.html", context)


@router.get("/shelves/{shelf_id}/delete", response_class=HTMLResponse, summary="Potwierdzenie")
def confirm_delete_shelf(request: Request, shelf_id: int, session: SessionDep) -> HTMLResponse:
    shelf = shelf_service.get_shelf(session, shelf_id)
    return render(request, "confirm_delete_shelf.html", {"shelf": shelf})


@router.post("/shelves/{shelf_id}/delete", summary="Usunięcie półki")
def delete_shelf(
    request: Request, shelf_id: int, session: SessionDep, filters: FormFilters
) -> Response:
    shelf_service.delete_shelf(session, shelf_id)
    if not is_htmx(request):
        return redirect("/")
    if filters.shelf_id == shelf_id:
        filters = replace(filters, shelf_id=None)
    context = list_context(session, filters, shelves_open=True)
    return render(request, "partials/shelves_response.html", context)
