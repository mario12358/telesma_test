from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.statuses import STATUS_LABELS, BookStatus, status_label

TEMPLATES_DIR = Path(__file__).parent / "templates"
MAX_RATING = 5

templates = Jinja2Templates(directory=TEMPLATES_DIR)


def format_date(value: datetime) -> str:
    """dd.MM.yyyy in the local time zone of the machine running the app."""
    return value.astimezone().strftime("%d.%m.%Y")


def format_datetime(value: datetime) -> str:
    return value.astimezone().strftime("%d.%m.%Y %H:%M")


def rating_stars(rating: int | None) -> str:
    if not rating:
        return ""
    return "★" * rating + "☆" * (MAX_RATING - rating)


templates.env.filters.update(
    date_pl=format_date,
    datetime_pl=format_datetime,
    status_label=status_label,
    stars=rating_stars,
)
templates.env.globals.update(
    STATUS_LABELS=STATUS_LABELS, BookStatus=BookStatus, MAX_RATING=MAX_RATING
)


def is_htmx(request: Request) -> bool:
    return request.headers.get("HX-Request") == "true"


def render(
    request: Request,
    template_name: str,
    context: dict[str, Any] | None = None,
    status_code: int = 200,
    headers: dict[str, str] | None = None,
) -> HTMLResponse:
    return templates.TemplateResponse(
        request, template_name, context or {}, status_code=status_code, headers=headers
    )
