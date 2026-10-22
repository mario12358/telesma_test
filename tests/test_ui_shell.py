from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi import Request

from app.statuses import BookStatus
from app.templating import format_date, format_datetime, is_htmx, rating_stars, templates
from tests.html import parse_html

STYLE_CSS = Path(__file__).resolve().parent.parent / "app" / "static" / "style.css"


def _request(headers: dict[str, str]) -> Request:
    raw_headers = [(name.lower().encode(), value.encode()) for name, value in headers.items()]
    return Request({"type": "http", "headers": raw_headers})


def test_home_renders_full_page_with_layout(client):
    response = client.get("/")
    document = parse_html(response.text)
    assert response.status_code == 200
    assert document.find("html").get("lang") == "pl"
    assert document.find("main", id="main") is not None
    assert document.find("h1").text == "Moje lektury"
    assert document.find("a", class_="skip-link").get("href") == "#main"
    assert document.find("meta", name="viewport") is not None
    scripts = [script.get("src") for script in document.find_all("script")]
    assert scripts == ["http://testserver/static/htmx.min.js"]


def test_layout_configures_htmx_to_swap_validation_errors(client):
    meta = parse_html(client.get("/").text).find("meta", name="htmx-config")
    assert '"code":"422","swap":true' in meta.get("content")


# specky: crit 01M5JNJCY4CP4ZYBZ9HR3X8S00
def test_dates_are_formatted_dd_mm_yyyy_in_local_time():
    moment = datetime(2026, 3, 7, 23, 30, tzinfo=UTC)
    local = moment.astimezone()
    assert format_date(moment) == f"{local.day:02d}.{local.month:02d}.{local.year}"
    assert format_datetime(moment) == local.strftime("%d.%m.%Y %H:%M")


@pytest.mark.parametrize(
    ("rating", "expected"), [(None, ""), (1, "★☆☆☆☆"), (4, "★★★★☆"), (5, "★★★★★")]
)
def test_rating_stars(rating, expected):
    assert rating_stars(rating) == expected


def test_status_label_filter_is_available_in_templates():
    rendered = templates.env.from_string("{{ 'reading' | status_label }}").render()
    assert rendered == "czytam"
    assert templates.env.globals["BookStatus"] is BookStatus


def test_is_htmx_recognises_the_htmx_request_header():
    assert is_htmx(_request({"HX-Request": "true"}))
    assert not is_htmx(_request({}))


# specky: crit 01M5JNJCCBDSJ3G1P8HK42H9Z4
def test_stylesheet_switches_to_one_column_below_640px():
    css = STYLE_CSS.read_text(encoding="utf-8")
    assert "@media (max-width: 639px)" in css
    narrow_rules = css.split("@media (max-width: 639px)", 1)[1]
    assert "grid-template-columns: 1fr" in narrow_rules
    assert "display: block" in narrow_rules


def test_stylesheet_keeps_a_visible_focus_indicator():
    css = STYLE_CSS.read_text(encoding="utf-8")
    assert ":focus-visible" in css
    assert "outline: none" not in css


def test_unknown_html_route_renders_polish_404_page(client):
    response = client.get("/nie-ma-takiej-strony")
    assert response.status_code == 404
    assert "text/html" in response.headers["content-type"]
    assert parse_html(response.text).find("h1").text == "Nie znaleziono"


def test_unknown_api_route_still_returns_json_404(client):
    response = client.get("/api/nie-ma")
    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/json")


@pytest.mark.parametrize(
    "headers",
    [
        {"Origin": "https://evil.example"},
        {"Sec-Fetch-Site": "cross-site"},
        {"Sec-Fetch-Site": "same-site"},
    ],
)
def test_cross_site_write_requests_are_rejected(client, headers):
    response = client.post("/api/shelves", json={"name": "Spam"}, headers=headers)
    assert response.status_code == 403
    assert client.get("/api/shelves").json() == []


def test_same_origin_write_requests_are_accepted(client):
    headers = {"Origin": "http://testserver", "Sec-Fetch-Site": "same-origin"}
    assert client.post("/api/shelves", json={"name": "Moja"}, headers=headers).status_code == 201


def test_cross_site_reads_are_allowed(client):
    assert client.get("/api/shelves", headers={"Sec-Fetch-Site": "cross-site"}).status_code == 200
