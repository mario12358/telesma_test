from pathlib import Path

from fastapi import APIRouter
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.config import DEFAULT_DB_PATH, load_settings
from app.errors import FieldError, field_errors_payload
from app.main import create_app
from app.statuses import STATUS_LABELS, BookStatus, status_label

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class _Probe(BaseModel):
    year: int


def _app_with_probe_route():
    app = create_app()
    probe = APIRouter()

    @probe.post("/api/_probe")
    def probe_endpoint(payload: _Probe) -> dict[str, int]:
        return {"year": payload.year}

    app.include_router(probe)
    return app


def test_home_returns_html_page():
    with TestClient(create_app()) as client:
        response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_static_htmx_is_served_from_single_file():
    with TestClient(create_app()) as client:
        response = client.get("/static/htmx.min.js")
    assert response.status_code == 200
    assert response.text.startswith("var htmx=")


# specky: crit 01M5JNJBEG18125FHAA7RP42K4
def test_frontend_has_no_npm_dependencies():
    static_files = sorted(path.name for path in (PROJECT_ROOT / "app" / "static").iterdir())
    assert "htmx.min.js" in static_files
    assert not (PROJECT_ROOT / "package.json").exists()
    assert not (PROJECT_ROOT / "node_modules").exists()


def test_request_validation_error_uses_field_message_format():
    with TestClient(_app_with_probe_route()) as client:
        response = client.post("/api/_probe", json={"year": "abc"})
    assert response.status_code == 422
    assert response.json() == {
        "detail": [{"field": "year", "message": "Wymagana liczba całkowita."}]
    }


def test_missing_field_reports_polish_required_message():
    with TestClient(_app_with_probe_route()) as client:
        response = client.post("/api/_probe", json={})
    assert response.json()["detail"] == [{"field": "year", "message": "Pole jest wymagane."}]


def test_field_errors_payload_lists_every_error():
    payload = field_errors_payload(
        [FieldError("title", "Tytuł jest wymagany."), FieldError("author", "Autor jest wymagany.")]
    )
    assert [item["field"] for item in payload["detail"]] == ["title", "author"]


def test_status_labels_cover_every_status():
    assert set(STATUS_LABELS) == set(BookStatus)
    assert status_label("reading") == "czytam"
    assert status_label(BookStatus.TO_READ) == "do przeczytania"


def test_settings_default_db_path(monkeypatch):
    monkeypatch.delenv("LEKTURY_DB_PATH", raising=False)
    assert load_settings().db_path == DEFAULT_DB_PATH


def test_settings_read_db_path_from_environment(monkeypatch, tmp_path):
    monkeypatch.setenv("LEKTURY_DB_PATH", str(tmp_path / "x.db"))
    assert load_settings().db_path == tmp_path / "x.db"
