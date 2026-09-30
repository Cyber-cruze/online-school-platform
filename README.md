# Онлайн-школа «Стимул»

Сайт онлайн-школы на FastAPI. В проекте есть публичная страница, отправка заявок через Gmail API, панель управления преподавателями и база данных SQLite.

## Запуск

Нужен Python 3.10 или новее. Создайте виртуальное окружение и установите зависимости:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python main.py
```

Сайт откроется по адресу <http://127.0.0.1:8000>, админка — <http://127.0.0.1:8000/admin>.

Админка защищена логином и паролем. Настройки берутся из локального файла `.env`, который не добавляется в Git. Для нового окружения скопируйте `.env.example` в `.env` и задайте собственные значения:

```bash
cp .env.example .env
```

Переменные окружения процесса имеют приоритет над значениями из `.env`.

Для отправки заявок включите Gmail API в Google Cloud и скачайте OAuth-клиент
типа Desktop app в файл `credentials.json`. Затем выполните одноразовую
авторизацию:

```bash
.venv/bin/python authorize_gmail.py
```

После согласия в браузере появится локальный `token.json`. Оба JSON-файла
игнорируются Git. Gmail-адрес отправителя задаётся в `GMAIL_SENDER`, а
получатели перечисляются через запятую в `APPLICATION_RECIPIENTS`; каждому из
них отправляется отдельное письмо.

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

## Проверка

```bash
.venv/bin/python -m unittest discover -s tests -v
```
