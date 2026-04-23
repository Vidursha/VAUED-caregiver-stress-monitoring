import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = str(BASE_DIR / "data" / "nurse_stress.db")


def ensure_db_initialized() -> None:
    """Create tables from CSVs if the DB file is missing or has no sensor_data table."""
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        row = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='sensor_data'"
        ).fetchone()
    finally:
        conn.close()
    if row:
        return
    from backend.init_db import seed_from_csv

    seed_from_csv()


def get_db_connection():
    ensure_db_initialized()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
