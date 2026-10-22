from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["views"])


@router.get("/", response_class=HTMLResponse, summary="Strona główna")
def home() -> str:
    return (
        '<!doctype html><html lang="pl"><head><meta charset="utf-8">'
        "<title>Lista lektur</title></head><body><h1>Lista lektur</h1></body></html>"
    )
