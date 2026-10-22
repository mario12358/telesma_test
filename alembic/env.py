from alembic import context
from sqlalchemy import Connection

from app.config import load_settings
from app.db import create_db_engine
from app.models import Base

target_metadata = Base.metadata


def _run_with_connection(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata, render_as_batch=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    provided_connection = context.config.attributes.get("connection")
    if provided_connection is not None:
        _run_with_connection(provided_connection)
        return
    engine = create_db_engine(load_settings().db_path)
    with engine.begin() as connection:
        _run_with_connection(connection)
    engine.dispose()


run_migrations_online()
