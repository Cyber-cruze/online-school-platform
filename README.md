# Онлайн-школа «Стимул»

Сайт онлайн-школы на FastAPI. В проекте есть публичная страница, отправка заявок через SMTP, панель управления преподавателями и база данных SQLite.

## Запуск

Для воспроизводимого окружения используйте Python 3.12. Создайте виртуальное окружение и установите зависимости:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
.venv/bin/python main.py
```

Сайт откроется по адресу <http://127.0.0.1:8000>, админка — <http://127.0.0.1:8000/admin>.

Админка защищена логином и паролем. Настройки берутся из локального файла `.env`, который не добавляется в Git. Для нового окружения скопируйте `.env.example` в `.env` и задайте собственные значения:

```bash
cp .env.example .env
```

Переменные окружения процесса имеют приоритет над значениями из `.env`.

Для отправки заявок задайте в `.env`:

```dotenv
COOKIE_SECURE=true # local - false; prod - true
ADMIN_USERNAME=STIMUL
ADMIN_PASSWORD=your-password
SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
SMTP_USERNAME=mail
SMTP_APP_PASSWORD=your-password
GMAIL_SENDER=mail
APPLICATION_RECIPIENTS=mails
```

`SMTP_USERNAME` — полный адрес отправителя, `SMTP_APP_PASSWORD` — пароль приложения Google, а не обычный пароль аккаунта.
`GMAIL_SENDER` - почта отправителя
`APPLICATION_RECIPIENTS` - почты которые будут оповещены
`ADMIN_PASSWORD` - пароль от админ панели

## Структура

```text
backend/
  controller/       HTTP-маршруты
  model/            модели данных
  repository/       подключение к SQLite и SQL-запросы
  service/          хранение данных и обработка форм
  view/             формирование HTML
frontend/
  templates/        HTML-шаблоны
  static/css/       стили сайта и админки
  static/js/        отправка формы заявки в FastAPI
uploads/            фотографии преподавателей
data/               база данных SQLite
tests/              автоматические тесты
main.py             точка запуска
requirements.txt    зависимости FastAPI и Uvicorn
teachers.json       старые данные для одноразового импорта
```

При первом запуске создаётся `data/stimulus.sqlite3`. Если в старом `teachers.json` есть преподаватели, они автоматически импортируются в SQLite один раз.

Доступные маршруты преподавателей:

- `GET /teachers` — получить весь список в JSON;
- `GET /teachers/{id}` — получить одного преподавателя;
- `POST /teachers` — добавить преподавателя из формы админки;
- `PUT /teachers/{id}` — отредактировать преподавателя;
- `PATCH /teachers/{id}/visibility` — скрыть преподавателя или вернуть на сайт;
- `DELETE /teachers/{id}` — удалить преподавателя.

`POST /applications` принимает заявку с публичной формы и отправляет её
получателям через Gmail.

Интерактивная документация API доступна по адресу <http://127.0.0.1:8000/docs>.

Деплой выполняется вручную: [инструкция для Ubuntu 24.04](docs/deployment.md).
Тесты, сборка образа и обновление сервера запускаются вручную.

## Проверка

```bash
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m unittest discover -s tests -v
```
