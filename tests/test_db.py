import sqlite3

from fastapi.testclient import TestClient
from sqlalchemy import text

from app.config import Settings
from app.main import create_app


def _table_names(db_file) -> set[str]:
    with sqlite3.connect(db_file) as connection:
        rows = connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    return {name for (name,) in rows}


# specky: crit 01M5JNJBEFT8T7ZS911ETD6407
def test_startup_creates_missing_database_file_with_schema(tmp_path):
    db_file = tmp_path / "nested" / "dir" / "lektury.db"
    assert not db_file.exists()
    with TestClient(create_app(Settings(db_path=db_file))) as client:
        assert client.get("/").status_code == 200
    assert db_file.exists()
    assert "alembic_version" in _table_names(db_file)


# specky: crit 01M5JNJBEG77T6N9EA0B04YZCX
def test_lektury_db_path_moves_database_to_given_file(monkeypatch, tmp_path):
    custom_file = tmp_path / "elsewhere" / "custom.db"
    monkeypatch.setenv("LEKTURY_DB_PATH", str(custom_file))
    with TestClient(create_app()):
        pass
    assert custom_file.exists()


def test_startup_is_idempotent_on_existing_database(db_path):
    with TestClient(create_app(Settings(db_path=db_path))):
        pass
    with TestClient(create_app(Settings(db_path=db_path))) as client:
        assert client.get("/").status_code == 200


def test_every_connection_enforces_foreign_keys(session):
    assert session.execute(text("PRAGMA foreign_keys")).scalar_one() == 1
    assert session.execute(text("PRAGMA journal_mode")).scalar_one() == "wal"
    assert session.execute(text("PRAGMA busy_timeout")).scalar_one() == 5000


def test_each_test_gets_a_fresh_database(session):
    session.execute(text("CREATE TABLE probe (id INTEGER PRIMARY KEY)"))
    session.commit()
    assert session.execute(text("SELECT count(*) FROM probe")).scalar_one() == 0


def test_fresh_database_has_no_probe_table_from_other_tests(session):
    tables = session.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).scalars()
    assert "probe" not in set(tables)
