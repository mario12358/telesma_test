"""Quality requirement guards: every API endpoint and rule is tested, and CI reports it."""

import re
from pathlib import Path

import pytest

from app.main import create_app

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TESTS_DIR = PROJECT_ROOT / "tests"
WORKFLOW = PROJECT_ROOT / ".github" / "workflows" / "specky-ci.yml"

# Rules R1-R7 from the specification (lista-lektur.md, section 3) and the tests that check them.
SHELF_ORDER_TEST = "test_get_shelves_alphabetical_case_insensitive_with_counts"
RULE_TESTS = {
    "R1 duplicate rejected": "test_create_rejects_duplicate_after_normalization",
    "R2 rating cleared on to_read": "test_status_change_to_read_later_clears_rating",
    "R3 delete removes notes and links": (
        "test_deleting_book_removes_its_notes_and_keeps_shelves_with_lower_count"
    ),
    "R4 a shelf may be empty": SHELF_ORDER_TEST,
    "R5 shelves listed alphabetically": SHELF_ORDER_TEST,
    "R6 notes cannot be edited": "test_notes_cannot_be_edited",
    "R7 notes listed newest first": "test_book_detail_lists_notes_newest_first",
}


def _test_sources() -> str:
    files = TESTS_DIR.rglob("test_*.py")
    return "\n".join(
        path.read_text(encoding="utf-8") for path in files if path.name != Path(__file__).name
    )


def _api_endpoints() -> list[tuple[str, str]]:
    paths = create_app().openapi()["paths"]
    return sorted(
        (method.upper(), path)
        for path, operations in paths.items()
        if path.startswith("/api")
        for method in operations
    )


def _call_pattern(method: str, path: str) -> re.Pattern[str]:
    """A test call such as client.patch(f"/api/books/{book_id}") for PATCH /api/books/{book_id}."""
    path_regex = re.sub(r"\\\{\w+\\\}", r"[^\"'/]+", re.escape(path))
    return re.compile(rf"\.{method.lower()}\(\s*f?[\"']{path_regex}[\"'?]")


# specky: crit 01M5JNJCTX4YJJQDXH78465WHM
@pytest.mark.parametrize(("method", "path"), _api_endpoints())
def test_every_api_endpoint_has_an_integration_test(method, path):
    assert _call_pattern(method, path).search(_test_sources()), f"no test calls {method} {path}"


def test_every_api_endpoint_from_the_specification_exists():
    specified = {
        ("GET", "/api/books"),
        ("POST", "/api/books"),
        ("GET", "/api/books/{book_id}"),
        ("PATCH", "/api/books/{book_id}"),
        ("DELETE", "/api/books/{book_id}"),
        ("GET", "/api/shelves"),
        ("POST", "/api/shelves"),
        ("DELETE", "/api/shelves/{shelf_id}"),
        ("PUT", "/api/books/{book_id}/shelves"),
        ("POST", "/api/books/{book_id}/notes"),
        ("DELETE", "/api/notes/{note_id}"),
        ("GET", "/api/export.csv"),
        ("GET", "/api/stats"),
    }
    assert specified <= set(_api_endpoints())


@pytest.mark.parametrize(("rule", "test_name"), RULE_TESTS.items())
def test_every_business_rule_has_a_test(rule, test_name):
    assert re.search(rf"^def {test_name}\(", _test_sources(), re.MULTILINE), rule


# specky: crit 01M5JNJCTX1C3MCC3C32KJQP5W
def test_ci_publishes_junit_reports_and_fails_on_any_failed_test():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "pull_request:" in workflow
    assert "branches: [main]" in workflow
    assert "--junitxml=reports/junit.xml" in workflow
    assert "--junitxml=reports/junit-e2e.xml" in workflow
    upload = workflow.split("actions/upload-artifact@", 1)[1]
    assert re.search(r"name: \S*junit\S*", upload)
    assert "if-no-files-found: error" in upload
    assert "grep -l '<failure\\|<error' reports/*.xml" in workflow
    assert workflow.rstrip().endswith('reports/*.xml 2>/dev/null)"')
