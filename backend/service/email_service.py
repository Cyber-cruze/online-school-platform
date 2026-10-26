"""Отправка заявок через SMTP с TLS."""

import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr, formatdate, make_msgid

from backend.config import (
    APPLICATION_RECIPIENTS,
    SMTP_APP_PASSWORD,
    SMTP_HOST,
    SMTP_PORT,
    SMTP_USERNAME,
)
from backend.schema.application import ApplicationCreate


SMTP_TIMEOUT_SECONDS = 20


class EmailDeliveryError(RuntimeError):
    """Письмо с заявкой не удалось отправить."""


def _build_message(application: ApplicationCreate, recipient: str) -> EmailMessage:
    message = EmailMessage()
    message["Subject"] = "Новая заявка с сайта школы «Стимул»"
    message["From"] = formataddr(("Онлайн-школа Стимул", SMTP_USERNAME))
    message["To"] = recipient
    message["Reply-To"] = application.email
    message["Date"] = formatdate(localtime=True)
    message["Message-ID"] = make_msgid()
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


def send_application_email(application: ApplicationCreate) -> None:
    if not APPLICATION_RECIPIENTS:
        raise EmailDeliveryError("Не заданы получатели заявок")

    context = ssl.create_default_context()
    try:
        if SMTP_PORT == 465:
            transport = smtplib.SMTP_SSL(
                SMTP_HOST, SMTP_PORT, timeout=SMTP_TIMEOUT_SECONDS, context=context
            )
        else:
            transport = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=SMTP_TIMEOUT_SECONDS)

        with transport as server:
            if SMTP_PORT != 465:
                server.starttls(context=context)
            server.login(SMTP_USERNAME, SMTP_APP_PASSWORD)
            for recipient in APPLICATION_RECIPIENTS:
                server.send_message(
                    _build_message(application, recipient),
                    from_addr=SMTP_USERNAME,
                    to_addrs=[recipient],
                )
    except (smtplib.SMTPException, OSError) as error:
        raise EmailDeliveryError("Не удалось отправить письмо через SMTP") from error
