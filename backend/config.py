import os
from pathlib import Path

from dotenv import load_dotenv

from backend.schema.application import EMAIL_PATTERN


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

FRONTEND_DIR = BASE_DIR / "frontend"
TEMPLATES_DIR = FRONTEND_DIR / "templates"
STATIC_DIR = FRONTEND_DIR / "static"
UPLOADS_DIR = Path(os.getenv("UPLOADS_DIR", str(BASE_DIR / "uploads")))
TEACHERS_FILE = Path(os.getenv("TEACHERS_FILE", str(BASE_DIR / "teachers.json")))
DATA_DIR = BASE_DIR / "data"
DATABASE_FILE = Path(os.getenv("DATABASE_FILE", str(DATA_DIR / "stimulus.sqlite3")))
LOGO_FILE = BASE_DIR / "diploma.png"

HOST = "127.0.0.1"
PORT = 8000


def required_setting(name: str) -> str:
    value = os.getenv(name)
    if not value or not value.strip():
        raise RuntimeError(
            f"Не задана обязательная переменная {name}. "
            "Добавьте её в файл .env или окружение процесса."
        )
    return value


ADMIN_USERNAME = required_setting("ADMIN_USERNAME")
ADMIN_PASSWORD = required_setting("ADMIN_PASSWORD")

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com").strip()
try:
    SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
except ValueError as error:
    raise RuntimeError("SMTP_PORT должен быть целым числом") from error
if not SMTP_HOST or not 1 <= SMTP_PORT <= 65535:
    raise RuntimeError("Проверьте SMTP_HOST и SMTP_PORT")
SMTP_USERNAME = required_setting("SMTP_USERNAME").strip()
SMTP_APP_PASSWORD = required_setting("SMTP_APP_PASSWORD")
APPLICATION_RECIPIENTS = tuple(
    address.strip()
    for address in required_setting("APPLICATION_RECIPIENTS").split(",")
    if address.strip()
)

if not EMAIL_PATTERN.fullmatch(SMTP_USERNAME) or not APPLICATION_RECIPIENTS or any(
    not EMAIL_PATTERN.fullmatch(address) for address in APPLICATION_RECIPIENTS
):
    raise RuntimeError("SMTP_USERNAME и APPLICATION_RECIPIENTS должны содержать адреса электронной почты")

_cookie_secure = os.getenv("COOKIE_SECURE", "false").lower()
if _cookie_secure not in {"true", "false"}:
    raise RuntimeError("COOKIE_SECURE должен быть true или false")
COOKIE_SECURE = _cookie_secure == "true"

ALLOWED_IMAGE_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}
