from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Book
from app.statuses import BookStatus

ONE_DECIMAL = Decimal("0.1")


@dataclass(frozen=True)
class LibraryStats:
    to_read: int
    reading: int
    read: int
    average_rating: float | None


def _round_one_decimal(value: float) -> float:
    """Half-up rounding as people expect it (4.25 → 4.3), not banker's rounding."""
    return float(Decimal(str(value)).quantize(ONE_DECIMAL, rounding=ROUND_HALF_UP))


def library_stats(session: Session) -> LibraryStats:
    counts = dict(session.execute(select(Book.status, func.count()).group_by(Book.status)).all())
    average = session.scalar(
        select(func.avg(Book.rating)).where(
            Book.status == BookStatus.READ.value, Book.rating.is_not(None)
        )
    )
    return LibraryStats(
        to_read=counts.get(BookStatus.TO_READ.value, 0),
        reading=counts.get(BookStatus.READING.value, 0),
        read=counts.get(BookStatus.READ.value, 0),
        average_rating=None if average is None else _round_one_decimal(average),
    )
