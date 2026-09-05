"""Рендеринг страниц и карточек преподавателей."""

from html import escape

from backend.config import TEMPLATES_DIR
from backend.model.teacher import Teacher
from backend.service.teacher_service import load_teachers


def _template(filename: str) -> str:
    return (TEMPLATES_DIR / filename).read_text(encoding="utf-8")


def render_public_teacher(teacher: Teacher) -> str:
    return f'''<article class="teacher">
      <div class="photo"><img src="{escape(teacher.photo)}" alt="{escape(teacher.name)}"></div>
      <div class="teacher-info"><h3>{escape(teacher.name)}</h3><span class="subject">{escape(teacher.subject)}</span><p>{escape(teacher.bio)}</p></div>
    </article>'''


def render_admin_teacher(teacher: Teacher) -> str:
    return f'''<article class="teacher-card">
      <img src="{escape(teacher.photo)}" alt="{escape(teacher.name)}">
      <div class="teacher-card-info"><h2>{escape(teacher.name)}</h2><span>{escape(teacher.subject)}</span><p>{escape(teacher.bio)}</p><button class="delete" hx-delete="/teachers/{escape(teacher.id)}" hx-target="#teacher-list" hx-swap="innerHTML" hx-confirm="Удалить преподавателя?">Удалить</button></div>
    </article>'''


def render_public_teacher_list(teachers: list[Teacher] | None = None) -> str:
    teachers = load_teachers() if teachers is None else teachers
    if not teachers:
        return '<p class="empty-teachers">Список преподавателей скоро появится здесь.</p>'
    return "".join(render_public_teacher(teacher) for teacher in teachers)


def render_admin_teacher_list(teachers: list[Teacher] | None = None) -> str:
    teachers = load_teachers() if teachers is None else teachers
    if not teachers:
        return '<p class="empty">Пока не добавлено ни одного преподавателя.</p>'
    return "".join(render_admin_teacher(teacher) for teacher in teachers)


def render_public_page() -> str:
    return _template("index.html").replace("{{TEACHERS}}", render_public_teacher_list())


def render_admin_page() -> str:
    return _template("admin.html").replace("{{TEACHERS}}", render_admin_teacher_list())


def render_login_page(error: str = "") -> str:
    return _template("login.html").replace("{{ERROR}}", escape(error))
