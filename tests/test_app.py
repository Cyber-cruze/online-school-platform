import json
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

# Настройки тестов не зависят от локального .env и не отправляют реальные письма.
os.environ.update({
    "ADMIN_USERNAME": "test-admin", "ADMIN_PASSWORD": "test-password",
    "SMTP_HOST": "smtp.example.com", "SMTP_PORT": "465",
    "SMTP_USERNAME": "sender@example.com", "SMTP_APP_PASSWORD": "test-app-password", "APPLICATION_RECIPIENTS": "office@example.com",
    "COOKIE_SECURE": "false",
})

from fastapi.testclient import TestClient

with patch("dotenv.load_dotenv"):
    from backend.application import app
from backend.model.teacher import Teacher
from backend.repository.database import initialize_database
from backend.service import auth_service
from backend.service import email_service
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

    def test_unicode_credentials(self) -> None:
        with patch.object(auth_service, "ADMIN_USERNAME", "админ"), patch.object(auth_service, "ADMIN_PASSWORD", "пароль"):
            self.assertTrue(auth_service.credentials_are_valid("админ", "пароль"))
            self.assertFalse(auth_service.credentials_are_valid("админ", "неверно"))
            self.assertFalse(auth_service.credentials_are_valid("другой", "пароль"))
        self.assertFalse(auth_service.is_authenticated('stimulus_admin_session="пароль"'))

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
    def setUp(self) -> None:
        directory = self.enterContext(TemporaryDirectory())
        root = Path(directory)
        self.database_file = root / "test.sqlite3"
        self.enterContext(patch("backend.repository.database.DATABASE_FILE", self.database_file))
        self.enterContext(patch("backend.application.DATABASE_FILE", self.database_file))
        self.enterContext(patch("backend.repository.database.TEACHERS_FILE", root / "teachers.json"))
        uploads = root / "uploads"
        uploads.mkdir()
        self.enterContext(patch("backend.service.teacher_service.UPLOADS_DIR", uploads))

    def test_photo_larger_than_six_mebibytes_can_be_created_and_replaced(self):
        import struct
        import zlib

        def chunk(kind, data):
            return struct.pack("!I", len(data)) + kind + data + struct.pack("!I", zlib.crc32(kind + data))

        # Корректный PNG с большим текстовым блоком, без сторонних библиотек.
        image = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack("!2I5B", 1, 1, 8, 2, 0, 0, 0))
        image += chunk(b"tEXt", b"Comment\0" + b"x" * (8 * 1024 * 1024))
        image += chunk(b"IDAT", zlib.compress(b"\0\0\0\0")) + chunk(b"IEND", b"")
        with TestClient(app) as client:
            client.post("/admin/login", data={"username": "test-admin", "password": "test-password"})
            fields = {"name": "Large photo", "subject": "Math", "bio": "Test"}
            response = client.post("/teachers", data=fields, files={"photo": ("large.png", image, "image/png")})
            self.assertEqual(response.status_code, 201, response.text)
            teacher = client.get("/teachers").json()[0]
            from backend.service import teacher_service
            self.assertEqual((teacher_service.UPLOADS_DIR / Path(teacher["photo"]).name).read_bytes(), image)
            response = client.put("/teachers/" + teacher["id"], data=fields, files={"photo": ("replacement.png", image, "image/png")})
            self.assertEqual(response.status_code, 200, response.text)
            updated = client.get("/teachers/" + teacher["id"]).json()
            self.assertNotEqual(updated["photo"], teacher["photo"])
            self.assertEqual((teacher_service.UPLOADS_DIR / Path(updated["photo"]).name).read_bytes(), image)

    def test_healthcheck_checks_database_and_hides_errors(self) -> None:
        with TestClient(app) as client:
            self.assertEqual(client.get("/healthz").json(), {"status": "ok"})
            with patch("backend.application.DATABASE_FILE", self.database_file.parent / "missing.sqlite3"):
                response = client.get("/healthz")
            self.assertEqual(response.status_code, 503)
            self.assertNotIn(str(self.database_file.parent), response.text)

    def test_login_cookie_secure_for_https(self) -> None:
        with patch("backend.controller.auth.COOKIE_SECURE", True), TestClient(app, base_url="https://testserver") as client:
            response = client.post("/admin/login", data={"username": "test-admin", "password": "test-password"}, follow_redirects=False)
            self.assertIn("Secure", response.headers["set-cookie"])
            self.assertEqual(client.get("/admin").status_code, 200)
            self.assertIn("Secure", client.post("/admin/logout", follow_redirects=False).headers["set-cookie"])

    def test_login_cookie_allows_local_http(self) -> None:
        with TestClient(app) as client:
            response = client.post("/admin/login", data={"username": "test-admin", "password": "test-password"}, follow_redirects=False)
            self.assertNotIn("Secure", response.headers["set-cookie"])
            self.assertEqual(client.get("/admin").status_code, 200)

    def test_application_delivery_failure_and_honeypot(self) -> None:
        payload = {"name": "Анна", "phone": "123", "email": "anna@example.com"}
        with patch("backend.controller.applications.send_application_email", side_effect=email_service.EmailDeliveryError("test")) as send, TestClient(app) as client:
            self.assertEqual(client.post("/applications", json=payload).status_code, 503)
            payload["botcheck"] = "filled"
            self.assertEqual(client.post("/applications", json=payload).status_code, 202)
            self.assertEqual(send.call_count, 1)

    def test_application_is_sent_through_email_service(self) -> None:
        with (
            patch("backend.controller.applications.send_application_email") as send_email,
            TestClient(app) as client,
        ):
            response = client.post(
                "/applications",
                json={
                    "name": "Анна Смирнова",
                    "phone": "+7 900 123-45-67",
                    "email": "anna@example.com",
                },
            )

        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.json(), {"success": True})
        application = send_email.call_args.args[0]
        self.assertEqual(application.email, "anna@example.com")

    def test_application_email_has_reply_to_and_separate_recipient(self) -> None:
        application = email_service.ApplicationCreate(
            name="Анна Смирнова",
            phone="+7 900 123-45-67",
            email="anna@example.com",
        )

        message = email_service._build_message(application, "office@example.com")

        self.assertEqual(message["To"], "office@example.com")
        self.assertEqual(message["Reply-To"], "anna@example.com")
        self.assertEqual(message["From"].addresses[0].addr_spec, "sender@example.com")
        self.assertIn("Анна Смирнова", message.get_content())

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

                hidden = client.patch(f"/teachers/{teacher_id}/visibility")
                self.assertEqual(hidden.status_code, 200)
                self.assertIn("Вернуть", hidden.text)
                self.assertIn("Скрыт с основной страницы", hidden.text)
                self.assertEqual(client.get("/teachers").json(), [])
                self.assertEqual(client.get(f"/teachers/{teacher_id}").status_code, 404)
                self.assertNotIn("Сергей Петров", client.get("/").text)
                self.assertIn("Сергей Петров", client.get("/admin").text)

                restored = client.patch(f"/teachers/{teacher_id}/visibility")
                self.assertEqual(restored.status_code, 200)
                self.assertIn("Скрыть", restored.text)
                self.assertEqual(len(client.get("/teachers").json()), 1)

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
            visibility_response = client.patch(
                "/teachers/" + "a" * 32 + "/visibility",
                headers={"HX-Request": "true"},
            )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.headers["HX-Redirect"], "/admin/login")
        self.assertEqual(update_response.status_code, 401)
        self.assertEqual(update_response.headers["HX-Redirect"], "/admin/login")
        self.assertEqual(visibility_response.status_code, 401)
        self.assertEqual(visibility_response.headers["HX-Redirect"], "/admin/login")


class SMTPDeliveryTests(unittest.TestCase):
    def setUp(self):
        self.application = email_service.ApplicationCreate(name="Test", phone="123", email="test@example.com")

    def test_ssl_login_timeout_and_separate_recipients(self):
        with patch.object(email_service.smtplib, "SMTP_SSL") as smtp, patch.object(email_service, "APPLICATION_RECIPIENTS", ("one@example.com", "two@example.com")):
            email_service.send_application_email(self.application)
            self.assertEqual(smtp.call_args.args, ("smtp.example.com", 465))
            self.assertEqual(smtp.call_args.kwargs["timeout"], 20)
            self.assertTrue(smtp.call_args.kwargs["context"].check_hostname)
            server = smtp.return_value.__enter__.return_value
            server.login.assert_called_once_with("sender@example.com", "test-app-password")
            server.starttls.assert_not_called()
            calls = server.send_message.call_args_list
            self.assertEqual([call.kwargs["to_addrs"] for call in calls], [["one@example.com"], ["two@example.com"]])
            self.assertEqual(calls[0].args[0]["Reply-To"], "test@example.com")
            self.assertEqual(calls[0].args[0]["To"], "one@example.com")
            self.assertEqual(calls[0].kwargs["from_addr"], "sender@example.com")

    def test_starttls_precedes_login_on_port_587(self):
        with patch.object(email_service, "SMTP_PORT", 587), patch.object(email_service.smtplib, "SMTP") as smtp:
            email_service.send_application_email(self.application)
            self.assertEqual(smtp.call_args.args, ("smtp.example.com", 587))
            server = smtp.return_value.__enter__.return_value
            self.assertEqual([call[0] for call in server.mock_calls[:2]], ["starttls", "login"])

    def test_smtp_and_network_failures_become_delivery_error(self):
        for error in (email_service.smtplib.SMTPAuthenticationError(535, b"Rejected"), OSError("Unavailable")):
            with self.subTest(error=type(error).__name__), patch.object(email_service.smtplib, "SMTP_SSL", side_effect=error):
                with self.assertRaises(email_service.EmailDeliveryError):
                    email_service.send_application_email(self.application)

    def test_tls_failure_does_not_send_credentials(self):
        with patch.object(email_service, "SMTP_PORT", 587), patch.object(email_service.smtplib, "SMTP") as smtp:
            server = smtp.return_value.__enter__.return_value
            server.starttls.side_effect = email_service.smtplib.SMTPNotSupportedError("No TLS")
            with self.assertRaises(email_service.EmailDeliveryError):
                email_service.send_application_email(self.application)
            server.login.assert_not_called()
            server.send_message.assert_not_called()


if __name__ == "__main__":
    unittest.main()
