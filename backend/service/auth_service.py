"""Проверка учётных данных и управление сессией администратора."""

import hmac
import secrets
from http.cookies import CookieError, SimpleCookie

from backend.config import ADMIN_PASSWORD, ADMIN_USERNAME, COOKIE_SECURE


SESSION_COOKIE_NAME = "stimulus_admin_session"
_SESSION_TOKEN = secrets.token_urlsafe(32)


def credentials_are_valid(username: str, password: str) -> bool:
    return hmac.compare_digest(
        username.encode("utf-8"), ADMIN_USERNAME.encode("utf-8")
    ) and hmac.compare_digest(
        password.encode("utf-8"),
        ADMIN_PASSWORD.encode("utf-8"),
    )


def is_authenticated(cookie_header: str | None) -> bool:
    if not cookie_header:
        return False

    cookie = SimpleCookie()
    try:
        cookie.load(cookie_header)
    except CookieError:
        return False

    session = cookie.get(SESSION_COOKIE_NAME)
    return bool(
        session and hmac.compare_digest(
            session.value.encode("utf-8"), _SESSION_TOKEN.encode("utf-8")
        )
    )


def session_token() -> str:
    return _SESSION_TOKEN


def create_session_cookie() -> str:
    return (
        f"{SESSION_COOKIE_NAME}={_SESSION_TOKEN}; "
        "Path=/; HttpOnly; SameSite=Strict"
        + ("; Secure" if COOKIE_SECURE else "")
    )


def clear_session_cookie() -> str:
    return (
        f"{SESSION_COOKIE_NAME}=; Path=/; Max-Age=0; "
        "HttpOnly; SameSite=Strict"
        + ("; Secure" if COOKIE_SECURE else "")
    )
