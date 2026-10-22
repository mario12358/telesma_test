from app.errors import DomainValidationError, FieldError

INTEGER_MESSAGE = "Wymagana liczba całkowita."


def optional_int(raw: str | None, field: str) -> int | None:
    """Form values arrive as text; an empty field means 'not given'."""
    value = (raw or "").strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        raise DomainValidationError([FieldError(field, INTEGER_MESSAGE)]) from None


def errors_by_field(error: DomainValidationError) -> dict[str, str]:
    return {field_error.field: field_error.message for field_error in error.errors}
