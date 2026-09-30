"""Приём заявок с публичной формы."""

import logging

from fastapi import APIRouter, HTTPException, status

from backend.schema.application import ApplicationCreate
from backend.service.email_service import EmailDeliveryError, send_application_email


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/applications", tags=["applications"])


@router.post("", status_code=status.HTTP_202_ACCEPTED)
def create_application(application: ApplicationCreate) -> dict[str, bool]:
    # Скрытое поле заполняют боты. Отвечаем успешно, но письмо не отправляем.
    if application.botcheck:
        return {"success": True}

    try:
        send_application_email(application)
    except EmailDeliveryError as error:
        logger.exception("Не удалось отправить заявку через Gmail")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Не удалось отправить заявку",
        ) from error

    return {"success": True}
