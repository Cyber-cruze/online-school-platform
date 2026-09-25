"""Вход и выход из админки."""

from typing import Annotated

from fastapi import APIRouter, Form
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from backend.service.auth_service import (
    SESSION_COOKIE_NAME,
    credentials_are_valid,
    session_token,
)
from backend.view.page_renderer import render_login_page


router = APIRouter(prefix="/admin", include_in_schema=False)


@router.post("/login")
def login(
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
) -> Response:
    if not credentials_are_valid(username, password):
        return HTMLResponse(render_login_page("Неверный логин или пароль"), status_code=401)

    response = RedirectResponse("/admin", status_code=303)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_token(),
        httponly=True,
        samesite="strict",
    )
    return response


@router.post("/logout")
def logout() -> Response:
    response = RedirectResponse("/admin/login", status_code=303)
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        httponly=True,
        samesite="strict",
    )
    return response
