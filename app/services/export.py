import csv
import io

from sqlalchemy.orm import Session

from app.models import Book
from app.services.books import BookFilters, list_books
from app.statuses import status_label

CSV_HEADER = ("tytuł", "autor", "rok", "status", "ocena", "półki")
SHELF_SEPARATOR = ";"
UTF8_BOM = "﻿"
FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def _safe_cell(value: str) -> str:
    """Spreadsheets run cells starting with = + - @ as formulas; a leading apostrophe stops that."""
    return f"'{value}" if value.startswith(FORMULA_PREFIXES) else value


def _row(book: Book) -> list[str]:
    return [
        _safe_cell(book.title),
        _safe_cell(book.author),
        "" if book.year is None else str(book.year),
        status_label(book.status),
        "" if book.rating is None else str(book.rating),
        _safe_cell(SHELF_SEPARATOR.join(shelf.name for shelf in book.shelves)),
    ]


def books_csv(session: Session) -> str:
    """All books as CSV (UTF-8 with BOM, comma-separated) that opens directly in a spreadsheet."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(CSV_HEADER)
    writer.writerows(_row(book) for book in list_books(session, BookFilters()))
    return UTF8_BOM + buffer.getvalue()
