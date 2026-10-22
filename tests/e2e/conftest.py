import socket
import threading
import time
from collections.abc import Iterator

import pytest
import uvicorn
from playwright.sync_api import Page

from app.config import Settings
from app.main import create_app

STARTUP_TIMEOUT_SECONDS = 10


def _free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


@pytest.fixture
def app_url(tmp_path) -> Iterator[str]:
    """The real app served by uvicorn on a free port with its own database file."""
    port = _free_port()
    app = create_app(Settings(db_path=tmp_path / "e2e.db"))
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + STARTUP_TIMEOUT_SECONDS
    while not server.started:
        if time.monotonic() > deadline:
            raise RuntimeError("uvicorn did not start in time")
        time.sleep(0.05)
    yield f"http://127.0.0.1:{port}"
    server.should_exit = True
    thread.join(timeout=STARTUP_TIMEOUT_SECONDS)


@pytest.fixture
def confirm_dialogs(page: Page) -> Page:
    """hx-confirm uses the browser's confirm(); the user answers «OK»."""
    page.on("dialog", lambda dialog: dialog.accept())
    return page
