from fastapi import FastAPI, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.errors import NotFoundError, handle_not_found, handle_request_validation
from app.templating import render

PAGE_NOT_FOUND = "Nie znaleziono strony."


def _is_api(request: Request) -> bool:
    return request.url.path.startswith("/api")


def _not_found_page(request: Request, message: str) -> Response:
    return render(request, "not_found.html", {"message": message}, status.HTTP_404_NOT_FOUND)


async def handle_not_found_error(request: Request, exc: NotFoundError) -> Response:
    if _is_api(request):
        return await handle_not_found(request, exc)
    return _not_found_page(request, exc.message)


async def handle_invalid_request(request: Request, exc: RequestValidationError) -> Response:
    """A malformed id in an HTML route (e.g. /books/abc) is a missing page, not a JSON error."""
    if _is_api(request):
        return await handle_request_validation(request, exc)
    return _not_found_page(request, PAGE_NOT_FOUND)


async def handle_http_error(request: Request, exc: StarletteHTTPException) -> Response:
    if exc.status_code == status.HTTP_404_NOT_FOUND and not _is_api(request):
        return _not_found_page(request, PAGE_NOT_FOUND)
    return JSONResponse({"detail": exc.detail}, status_code=exc.status_code, headers=exc.headers)


def register_error_pages(app: FastAPI) -> None:
    app.add_exception_handler(NotFoundError, handle_not_found_error)
    app.add_exception_handler(RequestValidationError, handle_invalid_request)
    app.add_exception_handler(StarletteHTTPException, handle_http_error)
