import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_DB_PATH = Path("data/lektury.db")


@dataclass(frozen=True)
class Settings:
    db_path: Path


def load_settings() -> Settings:
    raw_path = os.environ.get("LEKTURY_DB_PATH", "").strip()
    return Settings(db_path=Path(raw_path) if raw_path else DEFAULT_DB_PATH)
