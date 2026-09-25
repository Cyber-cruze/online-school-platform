"""Пути и настройки приложения."""

import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

FRONTEND_DIR = BASE_DIR / "frontend"
TEMPLATES_DIR = FRONTEND_DIR / "templates"
STATIC_DIR = FRONTEND_DIR / "static"
UPLOADS_DIR = BASE_DIR / "uploads"
TEACHERS_FILE = BASE_DIR / "teachers.json"
DATA_DIR = BASE_DIR / "data"
DATABASE_FILE = DATA_DIR / "stimulus.sqlite3"
LOGO_FILE = BASE_DIR / "diploma.png"

HOST = "127.0.0.1"
PORT = 8000



def required_setting(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"Не задана обязательная переменная {name}. "
            "Добавьте её в файл .env или окружение процесса."
        )
    return value


ADMIN_USERNAME = required_setting("ADMIN_USERNAME")
ADMIN_PASSWORD = required_setting("ADMIN_PASSWORD")

ALLOWED_IMAGE_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}
