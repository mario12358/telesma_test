from fastapi import APIRouter
from fastapi.responses import Response

from app.db import SessionDep
from app.services.export import books_csv

router = APIRouter(prefix="/api", tags=["export"])


@router.get(
    "/export.csv",
    summary="Eksport wszystkich książek do CSV",
    response_class=Response,
    responses={200: {"content": {"text/csv": {}}}},
)
def export_csv(session: SessionDep) -> Response:
    return Response(
        content=books_csv(session).encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="lektury.csv"'},
    )
