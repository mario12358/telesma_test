from fastapi import APIRouter, status

from app.db import SessionDep
from app.schemas import BookDetail, BookShelvesUpdate, ShelfCreate, ShelfRead
from app.services import shelves as shelf_service

router = APIRouter(prefix="/api", tags=["shelves"])


@router.get("/shelves", summary="Lista półek z liczbą książek")
def list_shelves(session: SessionDep) -> list[ShelfRead]:
    return [ShelfRead.model_validate(shelf) for shelf in shelf_service.list_shelves(session)]


@router.post("/shelves", status_code=status.HTTP_201_CREATED, summary="Dodanie półki")
def create_shelf(payload: ShelfCreate, session: SessionDep) -> ShelfRead:
    return ShelfRead.model_validate(shelf_service.create_shelf(session, payload.name))


@router.delete(
    "/shelves/{shelf_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Usunięcie półki"
)
def delete_shelf(shelf_id: int, session: SessionDep) -> None:
    shelf_service.delete_shelf(session, shelf_id)


@router.put("/books/{book_id}/shelves", summary="Ustawienie pełnej listy półek książki")
def set_book_shelves(book_id: int, payload: BookShelvesUpdate, session: SessionDep) -> BookDetail:
    book = shelf_service.set_book_shelves(session, book_id, payload.shelf_ids)
    return BookDetail.model_validate(book)
