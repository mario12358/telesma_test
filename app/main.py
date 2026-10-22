from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import Settings, load_settings
from app.db import create_db_engine, create_session_factory, run_migrations
from app.error_pages import register_error_pages
from app.errors import register_api_error_handlers
from app.routers.api import books as books_api
from app.routers.api import export as export_api
from app.routers.api import notes as notes_api
from app.routers.api import shelves as shelves_api
from app.routers.api import stats as stats_api
from app.routers.views import book_detail, book_sections, pages
from app.routers.views import shelves as shelf_views
from app.security import reject_cross_site_writes

STATIC_DIR = Path(__file__).parent / "static"


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or load_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = create_db_engine(app_settings.db_path)
        run_migrations(engine)
        app.state.engine = engine
        app.state.session_factory = create_session_factory(engine)
        yield
        engine.dispose()

    app = FastAPI(title="Lista lektur", lifespan=lifespan)
    app.state.settings = app_settings
    register_api_error_handlers(app)
    register_error_pages(app)
    app.middleware("http")(reject_cross_site_writes)
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    app.include_router(books_api.router)
    app.include_router(shelves_api.router)
    app.include_router(notes_api.router)
    app.include_router(export_api.router)
    app.include_router(stats_api.router)
    app.include_router(pages.router)
    app.include_router(shelf_views.router)
    app.include_router(book_detail.router)
    app.include_router(book_sections.router)
    return app


app = create_app()
