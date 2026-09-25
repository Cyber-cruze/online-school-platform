"""HTML-страницы сайта и админки."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from backend.service.auth_service import is_authenticated
from backend.view.page_renderer import (
    render_admin_page,
    render_login_page,
    render_public_page,
)


router = APIRouter(include_in_schema=False)


@router.get("/", response_class=HTMLResponse)
def public_page() -> Response:
    return HTMLResponse(render_public_page())


@router.get("/admin/login", response_class=HTMLResponse)
def login_page(request: Request) -> Response:
    if is_authenticated(request.headers.get("cookie")):
        return RedirectResponse("/admin", status_code=303)
    return HTMLResponse(render_login_page())


@router.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request) -> Response:
    if not is_authenticated(request.headers.get("cookie")):
        return RedirectResponse("/admin/login", status_code=303)
    return HTMLResponse(render_admin_page())
