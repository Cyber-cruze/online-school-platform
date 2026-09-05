import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from backend.model.teacher import Teacher
from backend.service import auth_service
from backend.service.multipart_service import parse_multipart
from backend.service.teacher_service import add_teacher, delete_teacher, load_teachers
from backend.view.page_renderer import render_admin_teacher, render_login_page, render_public_teacher


class TeacherRenderingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.teacher = Teacher(
            id="a" * 32,
            name="Иван <Петров>",
            subject="Математика",
            bio="Готовит к ОГЭ & ЕГЭ",
            photo="/uploads/teacher.jpg",
        )

    def test_public_card_escapes_user_content(self) -> None:
        card = render_public_teacher(self.teacher)

        self.assertIn("Иван &lt;Петров&gt;", card)
        self.assertIn("ОГЭ &amp; ЕГЭ", card)
        self.assertNotIn("Иван <Петров>", card)

    def test_admin_card_contains_delete_route(self) -> None:
        card = render_admin_teacher(self.teacher)

        self.assertIn(f'/teachers/{self.teacher.id}', card)


class MultipartTests(unittest.TestCase):
    def test_parser_keeps_cyrillic_text_and_file(self) -> None:
        boundary = "stimulus-boundary"
        body = (
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="name"\r\n\r\n'
            "Сергей Изотов\r\n"
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="photo"; filename="teacher.jpg"\r\n'
            "Content-Type: image/jpeg\r\n\r\n"
        ).encode("utf-8") + b"image-data\r\n" + f"--{boundary}--\r\n".encode()

        fields, uploaded_file = parse_multipart(
            f"multipart/form-data; boundary={boundary}",
            body,
        )

        self.assertEqual(fields["name"], "Сергей Изотов")
        self.assertEqual(uploaded_file, ("teacher.jpg", "image/jpeg", b"image-data"))


class TeacherServiceTests(unittest.TestCase):
    def test_teacher_can_be_added_loaded_and_deleted(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            teachers_file = root / "teachers.json"
            uploads_dir = root / "uploads"

            with (
                patch("backend.service.teacher_service.TEACHERS_FILE", teachers_file),
                patch("backend.service.teacher_service.UPLOADS_DIR", uploads_dir),
            ):
                teachers = add_teacher(
                    name="Анна Смирнова",
                    subject="Русский язык",
                    bio="Готовит к экзаменам",
                    original_filename="portrait.png",
                    content_type="image/png",
                    image_data=b"png-data",
                )

                self.assertEqual(load_teachers(), teachers)
                self.assertEqual(len(list(uploads_dir.iterdir())), 1)
                self.assertEqual(delete_teacher(teachers[0].id), [])
                self.assertEqual(load_teachers(), [])


class AuthenticationTests(unittest.TestCase):
    def test_credentials_are_checked_exactly(self) -> None:
        with (
            patch.object(auth_service, "ADMIN_USERNAME", "STIMUL"),
            patch.object(auth_service, "ADMIN_PASSWORD", "STIMUL54321"),
        ):
            self.assertTrue(auth_service.credentials_are_valid("STIMUL", "STIMUL54321"))
            self.assertFalse(auth_service.credentials_are_valid("stimul", "STIMUL54321"))
            self.assertFalse(auth_service.credentials_are_valid("STIMUL", "wrong"))

    def test_session_cookie_authenticates_request(self) -> None:
        cookie = auth_service.create_session_cookie()

        self.assertTrue(auth_service.is_authenticated(cookie))
        self.assertFalse(auth_service.is_authenticated(auth_service.clear_session_cookie()))
        self.assertIn("HttpOnly", cookie)
        self.assertIn("SameSite=Strict", cookie)

    def test_login_error_is_escaped(self) -> None:
        page = render_login_page("Ошибка <script>")

        self.assertIn("Ошибка &lt;script&gt;", page)
        self.assertNotIn("Ошибка <script>", page)


if __name__ == "__main__":
    unittest.main()
