from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.config import Settings
from app.main import create_app


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "lektury-test.db"


@pytest.fixture
def app(db_path) -> FastAPI:
    return create_app(Settings(db_path=db_path))


@pytest.fixture
def client(app) -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def session(client, app) -> Iterator[Session]:
    with app.state.session_factory() as db_session:
        yield db_session
