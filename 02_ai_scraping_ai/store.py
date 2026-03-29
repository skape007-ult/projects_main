import json
import logging
import sqlite3
import os
from datetime import date
from difflib import SequenceMatcher
from config import DB_PATH, LEGACY_JSON_PATH, FUZZY_TITLE_THRESHOLD, FUZZY_LOOKBACK_DAYS

logger = logging.getLogger(__name__)


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            url TEXT PRIMARY KEY,
            date TEXT NOT NULL,
            extract TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_articles_date ON articles(date)
    """)
    return conn


def migrate_from_json():
    """One-time migration from legacy JSON store to SQLite."""
    if not os.path.exists(LEGACY_JSON_PATH):
        return
    if os.path.exists(DB_PATH):
        conn = _get_conn()
        count = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
        conn.close()
        if count > 0:
            return

    logger.info("Migrating JSON store to SQLite...")
    with open(LEGACY_JSON_PATH) as f:
        store = json.load(f)

    conn = _get_conn()
    for url, data in store.items():
        conn.execute(
            "INSERT OR IGNORE INTO articles (url, date, extract) VALUES (?, ?, ?)",
            (url, data.get("date", ""), json.dumps(data.get("extract", {})))
        )
    conn.commit()
    conn.close()
    logger.info(f"Migrated {len(store)} articles to SQLite.")


def load_store() -> dict:
    """Load all articles as a dict (for backward compat). Prefer targeted queries."""
    migrate_from_json()
    conn = _get_conn()
    rows = conn.execute("SELECT url, date, extract FROM articles").fetchall()
    conn.close()
    return {
        url: {"date": dt, "extract": json.loads(extract)}
        for url, dt, extract in rows
    }


def save_to_store(store: dict, url: str, extract: dict):
    """Save a single article. The `store` dict param is kept for backward compat but ignored."""
    migrate_from_json()
    conn = _get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO articles (url, date, extract) VALUES (?, ?, ?)",
        (url, str(date.today()), json.dumps(extract))
    )
    conn.commit()
    conn.close()


def is_already_processed(store: dict, url: str) -> bool:
    """O(1) lookup via SQLite index instead of loading entire JSON."""
    migrate_from_json()
    conn = _get_conn()
    row = conn.execute("SELECT 1 FROM articles WHERE url = ?", (url,)).fetchone()
    conn.close()
    return row is not None


def _title_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def is_fuzzy_duplicate(title: str, source: str = "") -> bool:
    """Check if a similar title already exists in the store (cross-feed dedup)."""
    if not title or len(title) < 10:
        return False

    conn = _get_conn()
    rows = conn.execute(
        f"SELECT extract FROM articles WHERE date >= date('now', '-{FUZZY_LOOKBACK_DAYS} days')"
    ).fetchall()
    conn.close()

    for (extract_json,) in rows:
        try:
            extract = json.loads(extract_json)
            existing_title = extract.get("title", "")
            if existing_title and _title_similarity(title, existing_title) >= FUZZY_TITLE_THRESHOLD:
                return True
        except (json.JSONDecodeError, TypeError):
            continue

    return False


def get_articles_by_date(target_date: str = None) -> list[dict]:
    """Fetch articles for a specific date (defaults to today)."""
    if target_date is None:
        target_date = str(date.today())
    conn = _get_conn()
    rows = conn.execute(
        "SELECT url, date, extract FROM articles WHERE date = ?", (target_date,)
    ).fetchall()
    conn.close()
    return [
        {"url": url, "date": dt, "extract": json.loads(extract)}
        for url, dt, extract in rows
    ]


def get_store_count() -> int:
    """Fast count without loading entire store."""
    migrate_from_json()
    conn = _get_conn()
    count = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    conn.close()
    return count
