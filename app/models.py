from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, Column, ForeignKey, Index, Table, Text, UniqueConstraint
from sqlalchemy.engine import Dialect
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator

from app.statuses import BookStatus

UTC_TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


def utc_now() -> datetime:
    return datetime.now(UTC)


class UtcDateTime(TypeDecorator[datetime]):
    """Stores aware datetimes as fixed-width ISO-8601 UTC text, so text order equals time order."""

    impl = Text
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: Dialect) -> str | None:
        if value is None:
            return None
        return value.astimezone(UTC).strftime(UTC_TIMESTAMP_FORMAT)

    def process_result_value(self, value: str | None, dialect: Dialect) -> datetime | None:
        if value is None:
            return None
        return datetime.strptime(value, UTC_TIMESTAMP_FORMAT).replace(tzinfo=UTC)


class Base(DeclarativeBase):
    pass


book_shelves = Table(
    "book_shelves",
    Base.metadata,
    Column("book_id", ForeignKey("books.id", ondelete="CASCADE"), primary_key=True),
    Column("shelf_id", ForeignKey("shelves.id", ondelete="CASCADE"), primary_key=True),
    sqlite_strict=True,
)


class Book(Base):
    __tablename__ = "books"
    __table_args__ = (
        UniqueConstraint("title_norm", "author_norm", name="uq_books_title_author"),
        CheckConstraint("status IN ('to_read', 'reading', 'read')", name="ck_books_status"),
        CheckConstraint("rating IS NULL OR rating BETWEEN 1 AND 5", name="ck_books_rating_range"),
        CheckConstraint(
            "rating IS NULL OR status IN ('reading', 'read')", name="ck_books_rating_status"
        ),
        Index("ix_books_updated_at", "updated_at"),
        {"sqlite_strict": True},
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(Text)
    author: Mapped[str] = mapped_column(Text)
    title_norm: Mapped[str] = mapped_column(Text)
    author_norm: Mapped[str] = mapped_column(Text)
    year: Mapped[int | None]
    status: Mapped[str] = mapped_column(Text, default=BookStatus.TO_READ.value)
    rating: Mapped[int | None]
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(UtcDateTime, default=utc_now)

    shelves: Mapped[list["Shelf"]] = relationship(
        secondary=book_shelves, back_populates="books", order_by="Shelf.name_norm"
    )
    notes: Mapped[list["Note"]] = relationship(
        back_populates="book",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="(Note.created_at.desc(), Note.id.desc())",
    )


class Shelf(Base):
    __tablename__ = "shelves"
    __table_args__ = (
        UniqueConstraint("name_norm", name="uq_shelves_name_norm"),
        {"sqlite_strict": True},
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    name_norm: Mapped[str] = mapped_column(Text)

    books: Mapped[list[Book]] = relationship(secondary=book_shelves, back_populates="shelves")


class Note(Base):
    __tablename__ = "notes"
    __table_args__ = (
        Index("ix_notes_book_id_created_at", "book_id", "created_at"),
        {"sqlite_strict": True},
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id", ondelete="CASCADE"))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, default=utc_now)

    book: Mapped[Book] = relationship(back_populates="notes")
