"""Рендеринг страниц и карточек преподавателей."""

from html import escape

from backend.config import TEMPLATES_DIR
from backend.model.teacher import Teacher
from backend.service.teacher_service import load_teachers


def _template(filename: str) -> str:
    return (TEMPLATES_DIR / filename).read_text(encoding="utf-8")


def render_public_teacher(teacher: Teacher) -> str:
    return f'''<article class="teacher">
      <div class="teacher-card-head">
        <div class="photo">
          <img class="photo-main" src="{escape(teacher.photo)}" alt="{escape(teacher.name)}">
        </div>
        <div class="teacher-identity">
          <h3>{escape(teacher.name)}</h3>
          <span class="subject">{escape(teacher.subject)}</span>
        </div>
      </div>
      <p class="teacher-bio">{escape(teacher.bio)}</p>
    </article>'''


def render_admin_teacher(teacher: Teacher) -> str:
    visibility_class = " teacher-card-hidden" if not teacher.is_visible else ""
    visibility_label = "Вернуть" if not teacher.is_visible else "Скрыть"
    visibility_status = (
        '<div class="visibility-status">Скрыт с основной страницы</div>'
        if not teacher.is_visible
        else ""
    )
    return f'''<article class="teacher-card{visibility_class}">
      <div class="teacher-card-head">
        <img src="{escape(teacher.photo)}" alt="{escape(teacher.name)}">
        <div class="teacher-card-identity">
          <h2>{escape(teacher.name)}</h2>
          <span>{escape(teacher.subject)}</span>
          {visibility_status}
        </div>
      </div>
      <p class="teacher-card-bio">{escape(teacher.bio)}</p>
      <div class="teacher-card-actions">
        <button class="delete edit-button" type="button" data-edit-toggle="teacher-editor-{escape(teacher.id)}" aria-expanded="false">Редактировать</button>
        <button class="visibility-button" hx-patch="/teachers/{escape(teacher.id)}/visibility" hx-target="#teacher-list" hx-swap="innerHTML">{visibility_label}</button>
        <button class="delete" hx-delete="/teachers/{escape(teacher.id)}" hx-target="#teacher-list" hx-swap="innerHTML" hx-confirm="Удалить преподавателя?">Удалить</button>
      </div>
      <div class="teacher-editor" id="teacher-editor-{escape(teacher.id)}" hidden>
        <form hx-put="/teachers/{escape(teacher.id)}" hx-encoding="multipart/form-data" hx-target="#teacher-list" hx-swap="innerHTML">
          <label>Имя преподавателя<textarea class="compact-field" name="name" required>{escape(teacher.name)}</textarea></label>
          <label>Предмет<textarea class="compact-field" name="subject" required>{escape(teacher.subject)}</textarea></label>
          <label>Краткая информация<textarea name="bio" required>{escape(teacher.bio)}</textarea></label>
          <label>Новая фотография <small>необязательно</small><input name="photo" type="file" accept="image/jpeg,image/png,image/webp"></label>
          <button class="save-button" type="submit">Сохранить изменения</button>
        </form>
      </div>
    </article>'''


def render_public_teacher_list(teachers: list[Teacher] | None = None) -> str:
    teachers = load_teachers() if teachers is None else teachers
    if not teachers:
        return '<p class="empty-teachers">Список преподавателей скоро появится здесь.</p>'
    return "".join(render_public_teacher(teacher) for teacher in teachers)


def render_admin_teacher_list(teachers: list[Teacher] | None = None) -> str:
    teachers = load_teachers(include_hidden=True) if teachers is None else teachers
    if not teachers:
        return '<p class="empty">Пока не добавлено ни одного преподавателя.</p>'
    return "".join(render_admin_teacher(teacher) for teacher in teachers)


def render_public_page() -> str:
    return _template("index.html").replace("{{TEACHERS}}", render_public_teacher_list())


def render_admin_page() -> str:
    return _template("admin.html").replace("{{TEACHERS}}", render_admin_teacher_list())


def render_login_page(error: str = "") -> str:
    return _template("login.html").replace("{{ERROR}}", escape(error))
