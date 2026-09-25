import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.application import app
from backend.model.teacher import Teacher
from backend.repository.database import initialize_database
from backend.service import auth_service
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
        self.assertIn(f'hx-put="/teachers/{self.teacher.id}"', card)
        self.assertIn('>Иван &lt;Петров&gt;</textarea>', card)


class TeacherServiceTests(unittest.TestCase):
    def test_teacher_can_be_added_loaded_and_deleted(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            teachers_file = root / "teachers.json"
            database_file = root / "data" / "test.sqlite3"
            uploads_dir = root / "uploads"
            teachers_file.write_text("[]", encoding="utf-8")

            with (
                patch("backend.repository.database.DATABASE_FILE", database_file),
                patch("backend.repository.database.TEACHERS_FILE", teachers_file),
                patch("backend.service.teacher_service.UPLOADS_DIR", uploads_dir),
            ):
                initialize_database()
                teachers = add_teacher(
                    name="Анна Смирнова",
                    subject="Русский язык",
                    bio="Готовит к экзаменам",
                    original_filename="portrait.png",
                    content_type="image/png",
                    image_data=b"png-data",
                )

                self.assertEqual(load_teachers(), teachers)
                self.assertTrue(database_file.is_file())
                self.assertIsNotNone(teachers[0].created_at)
                self.assertEqual(len(list(uploads_dir.iterdir())), 1)
                self.assertEqual(delete_teacher(teachers[0].id), [])
                self.assertEqual(load_teachers(), [])

    def test_legacy_json_is_imported_once(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            teachers_file = root / "teachers.json"
            database_file = root / "data" / "test.sqlite3"
            teachers_file.write_text(
                json.dumps(
                    [
                        {
                            "id": "b" * 32,
                            "name": "Сергей Изотов",
                            "subject": "Информатика",
                            "bio": "Преподаватель",
                            "photo": "/uploads/teacher.jpg",
                        }
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with (
                patch("backend.repository.database.DATABASE_FILE", database_file),
                patch("backend.repository.database.TEACHERS_FILE", teachers_file),
            ):
                initialize_database()
                initialize_database()
                teachers = load_teachers()

            self.assertEqual(len(teachers), 1)
            self.assertEqual(teachers[0].name, "Сергей Изотов")


class AuthenticationTests(unittest.TestCase):
    def test_credentials_are_checked_exactly(self) -> None:
        with (
            patch.object(auth_service, "ADMIN_USERNAME", "test-admin"),
            patch.object(auth_service, "ADMIN_PASSWORD", "test-password"),
        ):
            self.assertTrue(auth_service.credentials_are_valid("test-admin", "test-password"))
            self.assertFalse(auth_service.credentials_are_valid("TEST-ADMIN", "test-password"))
            self.assertFalse(auth_service.credentials_are_valid("test-admin", "wrong"))

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


class FastAPIRouteTests(unittest.TestCase):
    def test_admin_flow_and_teacher_endpoints(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            database_file = root / "data" / "test.sqlite3"
            teachers_file = root / "teachers.json"
            uploads_dir = root / "uploads"
            teachers_file.write_text("[]", encoding="utf-8")

            with (
                patch("backend.repository.database.DATABASE_FILE", database_file),
                patch("backend.repository.database.TEACHERS_FILE", teachers_file),
                patch("backend.service.teacher_service.UPLOADS_DIR", uploads_dir),
                TestClient(app) as client,
            ):
                self.assertEqual(client.get("/teachers").json(), [])

                admin_response = client.get("/admin", follow_redirects=False)
                self.assertEqual(admin_response.status_code, 303)
                self.assertEqual(admin_response.headers["location"], "/admin/login")

                wrong_login = client.post(
                    "/admin/login",
                    data={"username": "STIMUL", "password": "wrong"},
                )
                self.assertEqual(wrong_login.status_code, 401)

                login = client.post(
                    "/admin/login",
                    data={
                        "username": auth_service.ADMIN_USERNAME,
                        "password": auth_service.ADMIN_PASSWORD,
                    },
                    follow_redirects=False,
                )
                self.assertEqual(login.status_code, 303)
                self.assertIn(auth_service.SESSION_COOKIE_NAME, client.cookies)

                created = client.post(
                    "/teachers",
                    data={
                        "name": "Сергей Изотов",
                        "subject": "Информатика",
                        "bio": "Преподаватель",
                    },
                    files={"photo": ("portrait.png", b"png-data", "image/png")},
                )
                self.assertEqual(created.status_code, 201)
                self.assertIn("Сергей Изотов", created.text)

                teachers = client.get("/teachers").json()
                self.assertEqual(len(teachers), 1)
                self.assertEqual(teachers[0]["name"], "Сергей Изотов")
                teacher_id = teachers[0]["id"]
                original_photo = teachers[0]["photo"]
                self.assertEqual(client.get(f"/teachers/{teacher_id}").status_code, 200)

                updated = client.put(
                    f"/teachers/{teacher_id}",
                    data={
                        "name": "Сергей Петров",
                        "subject": "Программирование",
                        "bio": "Обновлённая информация",
                    },
                )
                self.assertEqual(updated.status_code, 200)
                self.assertIn("Сергей Петров", updated.text)
                teacher = client.get(f"/teachers/{teacher_id}").json()
                self.assertEqual(teacher["subject"], "Программирование")
                self.assertEqual(teacher["photo"], original_photo)

                photo_updated = client.put(
                    f"/teachers/{teacher_id}",
                    data={
                        "name": "Сергей Петров",
                        "subject": "Программирование",
                        "bio": "Обновлённая информация",
                    },
                    files={"photo": ("new-photo.jpg", b"jpg-data", "image/jpeg")},
                )
                self.assertEqual(photo_updated.status_code, 200)
                teacher = client.get(f"/teachers/{teacher_id}").json()
                self.assertNotEqual(teacher["photo"], original_photo)
                self.assertEqual(len(list(uploads_dir.iterdir())), 1)

                deleted = client.delete(f"/teachers/{teacher_id}")
                self.assertEqual(deleted.status_code, 200)
                self.assertEqual(client.get("/teachers").json(), [])

    def test_teacher_mutation_requires_login(self) -> None:
        with TestClient(app) as client:
            response = client.delete(
                "/teachers/" + "a" * 32,
                headers={"HX-Request": "true"},
            )
            update_response = client.put(
                "/teachers/" + "a" * 32,
                data={"name": "Тест", "subject": "Тест", "bio": "Тест"},
                headers={"HX-Request": "true"},
            )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.headers["HX-Redirect"], "/admin/login")
        self.assertEqual(update_response.status_code, 401)
        self.assertEqual(update_response.headers["HX-Redirect"], "/admin/login")


if __name__ == "__main__":
    unittest.main()
