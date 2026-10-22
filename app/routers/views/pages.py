from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.templating import render

router = APIRouter(tags=["views"])


@router.get("/", response_class=HTMLResponse, summary="Ekran «Lista»")
def list_page(request: Request) -> HTMLResponse:
    return render(request, "list.html")
