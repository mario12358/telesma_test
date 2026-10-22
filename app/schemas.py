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


class StatsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    to_read: int
    reading: int
    read: int
    average_rating: float | None


class ShelfCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str


class ShelfRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    book_count: int


class BookShelvesUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    shelf_ids: list[int]


class ShelfSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class NoteCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: str


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
