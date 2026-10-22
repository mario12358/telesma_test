from fastapi import APIRouter, status

from app.db import SessionDep
from app.schemas import NoteCreate, NoteRead
from app.services import notes as note_service

router = APIRouter(prefix="/api", tags=["notes"])


@router.post(
    "/books/{book_id}/notes", status_code=status.HTTP_201_CREATED, summary="Dodanie notatki"
)
def create_note(book_id: int, payload: NoteCreate, session: SessionDep) -> NoteRead:
    return NoteRead.model_validate(note_service.create_note(session, book_id, payload.content))


@router.delete(
    "/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Usunięcie notatki"
)
def delete_note(note_id: int, session: SessionDep) -> None:
    note_service.delete_note(session, note_id)
