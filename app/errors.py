from dataclasses import dataclass

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

PYDANTIC_MESSAGES = {
    "missing": "Pole jest wymagane.",
    "int_parsing": "Wymagana liczba całkowita.",
    "int_type": "Wymagana liczba całkowita.",
    "int_from_float": "Wymagana liczba całkowita.",
    "string_type": "Wymagany tekst.",
    "list_type": "Wymagana lista.",
    "enum": "Niedozwolona wartość.",
    "literal_error": "Niedozwolona wartość.",
    "json_invalid": "Nieprawidłowy JSON.",
    "model_attributes_type": "Nieprawidłowe dane.",
    "dict_type": "Nieprawidłowe dane.",
    "extra_forbidden": "Nieznane pole.",
}
DEFAULT_MESSAGE = "Nieprawidłowa wartość."


@dataclass(frozen=True)
class FieldError:
    field: str
    message: str


class DomainValidationError(Exception):
    def __init__(self, errors: list[FieldError]) -> None:
        super().__init__("; ".join(f"{error.field}: {error.message}" for error in errors))
        self.errors = errors


class NotFoundError(Exception):
    def __init__(self, message: str = "Nie znaleziono zasobu.") -> None:
        super().__init__(message)
        self.message = message


def field_errors_payload(errors: list[FieldError]) -> dict[str, list[dict[str, str]]]:
    return {"detail": [{"field": error.field, "message": error.message} for error in errors]}


def pydantic_errors_to_field_errors(raw_errors: list[dict]) -> list[FieldError]:
    field_errors = []
    for raw in raw_errors:
        location = [
            str(part) for part in raw.get("loc", ()) if part not in ("body", "query", "path")
        ]
        field = location[0] if location else "body"
        message = PYDANTIC_MESSAGES.get(raw.get("type", ""), DEFAULT_MESSAGE)
        field_errors.append(FieldError(field=field, message=message))
    return field_errors


async def handle_request_validation(_: Request, exc: RequestValidationError) -> JSONResponse:
    errors = pydantic_errors_to_field_errors(list(exc.errors()))
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, content=field_errors_payload(errors)
    )


async def handle_domain_validation(_: Request, exc: DomainValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, content=field_errors_payload(exc.errors)
    )


async def handle_not_found(_: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": exc.message})


def register_api_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(RequestValidationError, handle_request_validation)
    app.add_exception_handler(DomainValidationError, handle_domain_validation)
    app.add_exception_handler(NotFoundError, handle_not_found)
