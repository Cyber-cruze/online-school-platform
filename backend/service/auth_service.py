"""Проверка учётных данных и управление сессией администратора."""

import hmac
import secrets
from http.cookies import CookieError, SimpleCookie

from backend.config import ADMIN_PASSWORD, ADMIN_USERNAME


SESSION_COOKIE_NAME = "stimulus_admin_session"
_SESSION_TOKEN = secrets.token_urlsafe(32)


def credentials_are_valid(username: str, password: str) -> bool:
    return hmac.compare_digest(username, ADMIN_USERNAME) and hmac.compare_digest(
        password,
        ADMIN_PASSWORD,
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
    return bool(session and hmac.compare_digest(session.value, _SESSION_TOKEN))


def session_token() -> str:
    return _SESSION_TOKEN


def create_session_cookie() -> str:
    return (
        f"{SESSION_COOKIE_NAME}={_SESSION_TOKEN}; "
        "Path=/; HttpOnly; SameSite=Strict"
    )


def clear_session_cookie() -> str:
    return (
        f"{SESSION_COOKIE_NAME}=; Path=/; Max-Age=0; "
        "HttpOnly; SameSite=Strict"
    )
