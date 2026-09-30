"""Отправка заявок через Gmail API."""

import base64
from email.message import EmailMessage
from email.utils import formataddr, formatdate, make_msgid

from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from backend.config import (
    APPLICATION_RECIPIENTS,
    GMAIL_SENDER,
    GOOGLE_TOKEN_FILE,
)
from backend.schema.application import ApplicationCreate


GMAIL_SEND_SCOPE = "https://www.googleapis.com/auth/gmail.send"


class EmailDeliveryError(RuntimeError):
    """Письмо с заявкой не удалось отправить."""


def _build_message(application: ApplicationCreate, recipient: str) -> EmailMessage:
    message = EmailMessage()
    message["Subject"] = "Новая заявка с сайта школы «Стимул»"
    message["From"] = formataddr(("Онлайн-школа Стимул", GMAIL_SENDER))
    message["To"] = recipient
    message["Reply-To"] = application.email
    message["Date"] = formatdate(localtime=True)
    message["Message-ID"] = make_msgid(domain="gmail.com")
    message.set_content(
        "\n".join(
            (
                "Новая заявка на консультацию с сайта школы «Стимул».",
                "",
                f"Имя: {application.name}",
                f"Телефон: {application.phone}",
                f"Электронная почта: {application.email}",
                "",
                "Посетитель ожидает обратной связи по указанным контактам.",
            )
        )
    )
    return message


def _load_credentials() -> Credentials:
    if not GOOGLE_TOKEN_FILE.is_file():
        raise EmailDeliveryError(
            "Не найден token.json. Выполните: python authorize_gmail.py"
        )

    try:
        credentials = Credentials.from_authorized_user_file(
            GOOGLE_TOKEN_FILE,
            [GMAIL_SEND_SCOPE],
        )
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
            GOOGLE_TOKEN_FILE.write_text(credentials.to_json(), encoding="utf-8")
    except (GoogleAuthError, OSError, ValueError) as error:
        raise EmailDeliveryError("Не удалось загрузить OAuth-токен Gmail") from error

    if not credentials.valid:
        raise EmailDeliveryError("OAuth-токен Gmail недействителен")
    return credentials


def send_application_email(application: ApplicationCreate) -> None:
    if not APPLICATION_RECIPIENTS:
        raise EmailDeliveryError("Не заданы получатели заявок")

    try:
        service = build(
            "gmail",
            "v1",
            credentials=_load_credentials(),
            cache_discovery=False,
        )
        for recipient in APPLICATION_RECIPIENTS:
            message = _build_message(application, recipient)
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")
            service.users().messages().send(
                userId="me",
                body={"raw": raw_message},
            ).execute()
    except (GoogleAuthError, HttpError, OSError, ValueError) as error:
        raise EmailDeliveryError("Gmail API отклонил отправку письма") from error
