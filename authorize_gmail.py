"""Одноразовая авторизация Gmail API для отправки заявок."""

from google_auth_oauthlib.flow import InstalledAppFlow

from backend.config import GOOGLE_CREDENTIALS_FILE, GOOGLE_TOKEN_FILE
from backend.service.email_service import GMAIL_SEND_SCOPE


def main() -> None:
    if not GOOGLE_CREDENTIALS_FILE.is_file():
        raise SystemExit("Не найден credentials.json в корне проекта")

    flow = InstalledAppFlow.from_client_secrets_file(
        GOOGLE_CREDENTIALS_FILE,
        [GMAIL_SEND_SCOPE],
    )
    credentials = flow.run_local_server(
        port=0,
        access_type="offline",
        prompt="consent",
        authorization_prompt_message="Откройте эту ссылку в браузере:\n{url}",
        success_message="Авторизация завершена. Это окно можно закрыть.",
    )
    GOOGLE_TOKEN_FILE.write_text(credentials.to_json(), encoding="utf-8")
    print("Gmail API настроен: token.json создан.")


if __name__ == "__main__":
    main()
