from sqlalchemy.orm import Session

from app.errors import DomainValidationError, FieldError, NotFoundError
from app.models import Note
from app.services.books import get_book

CONTENT_MAX_LENGTH = 2000
NOTE_NOT_FOUND = "Nie znaleziono notatki."


def _validated_content(raw_content: str) -> str:
    content = raw_content.strip()
    if not content:
        raise DomainValidationError([FieldError("content", "Treść notatki jest wymagana.")])
    if len(content) > CONTENT_MAX_LENGTH:
        message = f"Notatka może mieć najwyżej {CONTENT_MAX_LENGTH} znaków."
        raise DomainValidationError([FieldError("content", message)])
    return content


def create_note(session: Session, book_id: int, raw_content: str) -> Note:
    """Notes can only be added and deleted, never edited (R6)."""
    book = get_book(session, book_id)
    note = Note(book_id=book.id, content=_validated_content(raw_content))
    session.add(note)
    session.commit()
    return note


def delete_note(session: Session, note_id: int) -> int:
    """Returns the id of the book the note belonged to."""
    note = session.get(Note, note_id)
    if note is None:
        raise NotFoundError(NOTE_NOT_FOUND)
    book_id = note.book_id
    session.delete(note)
    session.commit()
    return book_id
