"""Пути и настройки приложения."""

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
TEMPLATES_DIR = FRONTEND_DIR / "templates"
STATIC_DIR = FRONTEND_DIR / "static"
UPLOADS_DIR = BASE_DIR / "uploads"
TEACHERS_FILE = BASE_DIR / "teachers.json"
LOGO_FILE = BASE_DIR / "diploma.png"

HOST = "127.0.0.1"
PORT = 8000

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "STIMUL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "STIMUL54321")

ALLOWED_IMAGE_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}
