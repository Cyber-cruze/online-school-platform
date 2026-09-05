"""HTTP-маршруты сайта и админки."""

import mimetypes
import re
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from backend.config import LOGO_FILE, STATIC_DIR, UPLOADS_DIR
from backend.service.auth_service import (
    clear_session_cookie,
    create_session_cookie,
    credentials_are_valid,
    is_authenticated,
)
from backend.service.multipart_service import parse_multipart
from backend.service.teacher_service import InvalidImageError, add_teacher, delete_teacher
from backend.view.page_renderer import (
    render_admin_page,
    render_admin_teacher_list,
    render_login_page,
    render_public_page,
)


class WebsiteHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        path = urlparse(self.path).path

        if path == "/":
            self._send_html(render_public_page())
            return
        if path == "/admin/login":
            if is_authenticated(self.headers.get("Cookie")):
                self._redirect("/admin")
            else:
                self._send_html(render_login_page())
            return
        if path == "/admin":
            if not self._require_admin():
                return
            self._send_html(render_admin_page())
            return
        if path == "/diploma.png":
            self._send_file(LOGO_FILE)
            return
        if path.startswith("/uploads/"):
            self._send_safe_file(UPLOADS_DIR, path.removeprefix("/uploads/"))
            return
        if path.startswith("/static/"):
            self._send_safe_file(STATIC_DIR, path.removeprefix("/static/"))
            return

        self.send_error(404)

    def do_POST(self) -> None:
        path = urlparse(self.path).path

        if path == "/admin/login":
            self._handle_login()
            return
        if path == "/admin/logout":
            self._redirect("/admin/login", cookie=clear_session_cookie(), status=303)
            return
        if path != "/teachers":
            self.send_error(404)
            return
        if not self._require_admin():
            return

        content_length = int(self.headers.get("Content-Length", 0))
        fields, uploaded_file = parse_multipart(
            self.headers.get("Content-Type", ""),
            self.rfile.read(content_length),
        )
        if not uploaded_file or not all(fields.get(key) for key in ("name", "subject", "bio")):
            self.send_error(400, "Заполните все поля и добавьте фотографию")
            return

        original_name, content_type, file_data = uploaded_file
        try:
            teachers = add_teacher(
                name=fields["name"],
                subject=fields["subject"],
                bio=fields["bio"],
                original_filename=original_name,
                content_type=content_type,
                image_data=file_data,
            )
        except InvalidImageError as error:
            self.send_error(400, str(error))
            return

        self._send_html(render_admin_teacher_list(teachers))

    def do_DELETE(self) -> None:
        if not self._require_admin():
            return

        match = re.fullmatch(r"/teachers/([a-f0-9]{32})", urlparse(self.path).path)
        if not match:
            self.send_error(404)
            return

        teachers = delete_teacher(match.group(1))
        if teachers is None:
            self.send_error(404)
            return
        self._send_html(render_admin_teacher_list(teachers))

    def _handle_login(self) -> None:
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length > 65_536:
            self.send_error(413)
            return

        try:
            fields = parse_qs(
                self.rfile.read(content_length).decode("utf-8"),
                keep_blank_values=True,
            )
        except UnicodeDecodeError:
            self.send_error(400)
            return

        username = fields.get("username", [""])[0]
        password = fields.get("password", [""])[0]
        if credentials_are_valid(username, password):
            self._redirect("/admin", cookie=create_session_cookie(), status=303)
            return

        self._send_html(
            render_login_page("Неверный логин или пароль"),
            status=401,
        )

    def _require_admin(self) -> bool:
        if is_authenticated(self.headers.get("Cookie")):
            return True

        if self.headers.get("HX-Request") == "true":
            self.send_response(401)
            self.send_header("HX-Redirect", "/admin/login")
            self.send_header("Content-Length", "0")
            self.end_headers()
        else:
            self._redirect("/admin/login")
        return False

    def _redirect(self, location: str, *, cookie: str | None = None, status: int = 302) -> None:
        self.send_response(status)
        self.send_header("Location", location)
        if cookie:
            self.send_header("Set-Cookie", cookie)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _send_html(self, html: str, *, status: int = 200) -> None:
        payload = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _send_safe_file(self, root: Path, relative_path: str) -> None:
        requested = (root / unquote(relative_path)).resolve()
        try:
            requested.relative_to(root.resolve())
        except ValueError:
            self.send_error(404)
            return
        self._send_file(requested)

    def _send_file(self, file_path: Path) -> None:
        if not file_path.is_file():
            self.send_error(404)
            return

        payload = file_path.read_bytes()
        content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args: object) -> None:
        return
