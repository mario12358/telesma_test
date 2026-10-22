from datetime import UTC, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, PlainSerializer

from app.statuses import BookStatus


def _serialize_utc(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


UtcTimestamp = Annotated[datetime, PlainSerializer(_serialize_utc, return_type=str)]


class BookCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    author: str
    year: int | None = None
    status: BookStatus = BookStatus.TO_READ
    rating: int | None = None


class BookUpdate(BaseModel):
    """Partial update: only fields present in the request body are applied."""

    model_config = ConfigDict(extra="forbid")

    title: str | None = None
    author: str | None = None
    year: int | None = None
    status: BookStatus | None = None
    rating: int | None = None


class ShelfSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class NoteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    book_id: int
    content: str
    created_at: UtcTimestamp


class BookRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    author: str
    year: int | None
    status: BookStatus
    rating: int | None
    created_at: UtcTimestamp
    updated_at: UtcTimestamp
    shelves: list[ShelfSummary]


class BookDetail(BookRead):
    notes: list[NoteRead]
