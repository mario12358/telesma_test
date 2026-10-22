from fastapi import APIRouter

from app.db import SessionDep
from app.schemas import StatsRead
from app.services.stats import library_stats

router = APIRouter(prefix="/api", tags=["stats"])


@router.get("/stats", summary="Liczba książek w każdym statusie i średnia ocena przeczytanych")
def get_stats(session: SessionDep) -> StatsRead:
    return StatsRead.model_validate(library_stats(session))
