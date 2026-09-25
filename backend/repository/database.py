"""Подключение к SQLite, создание схемы и импорт старых JSON-данных."""

import json
import sqlite3
import uuid

from backend.config import DATABASE_FILE, TEACHERS_FILE


def get_connection() -> sqlite3.Connection:
    DATABASE_FILE.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_FILE, timeout=5)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 5000")
    return connection


def initialize_database() -> None:
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS teachers (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                subject TEXT NOT NULL,
                bio TEXT NOT NULL,
                photo TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS app_metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        _import_legacy_teachers(connection)
        connection.execute("PRAGMA optimize")


def _import_legacy_teachers(connection: sqlite3.Connection) -> None:
    imported = connection.execute(
        "SELECT value FROM app_metadata WHERE key = ?",
        ("legacy_teachers_imported",),
    ).fetchone()
    if imported:
        return

    teachers: list[object] = []
    if TEACHERS_FILE.exists():
        try:
            content = json.loads(TEACHERS_FILE.read_text(encoding="utf-8"))
            if isinstance(content, list):
                teachers = content
        except (json.JSONDecodeError, OSError):
            pass

    for item in teachers:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "")).strip()
        subject = str(item.get("subject", "")).strip()
        bio = str(item.get("bio", "")).strip()
        photo = str(item.get("photo", "")).strip()
        if not all((name, subject, bio, photo)):
            continue
        connection.execute(
            """
            INSERT OR IGNORE INTO teachers (id, name, subject, bio, photo)
            VALUES (?, ?, ?, ?, ?)
            """,
            (str(item.get("id") or uuid.uuid4().hex), name, subject, bio, photo),
        )

    connection.execute(
        "INSERT INTO app_metadata (key, value) VALUES (?, ?)",
        ("legacy_teachers_imported", "1"),
    )
