"""Хранение преподавателей и загруженных фотографий."""

import json
import uuid
from pathlib import Path

from backend.config import ALLOWED_IMAGE_TYPES, TEACHERS_FILE, UPLOADS_DIR
from backend.model.teacher import Teacher


class InvalidImageError(ValueError):
    """Загруженный файл не является поддерживаемым изображением."""


def load_teachers() -> list[Teacher]:
    if not TEACHERS_FILE.exists():
        return []

    try:
        raw_teachers = json.loads(TEACHERS_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []

    if not isinstance(raw_teachers, list):
        return []

    teachers: list[Teacher] = []
    changed = False
    for raw_teacher in raw_teachers:
        if not isinstance(raw_teacher, dict):
            continue
        if not raw_teacher.get("id"):
            raw_teacher["id"] = uuid.uuid4().hex
            changed = True
        teachers.append(Teacher.from_dict(raw_teacher))

    if changed:
        save_teachers(teachers)
    return teachers


def save_teachers(teachers: list[Teacher]) -> None:
    payload = [teacher.to_dict() for teacher in teachers]
    TEACHERS_FILE.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def add_teacher(
    *,
    name: str,
    subject: str,
    bio: str,
    original_filename: str,
    content_type: str,
    image_data: bytes,
) -> list[Teacher]:
    extension = Path(original_filename).suffix.lower()
    if ALLOWED_IMAGE_TYPES.get(extension) != content_type:
        raise InvalidImageError("Поддерживаются JPG, PNG и WebP")

    UPLOADS_DIR.mkdir(exist_ok=True)
    filename = f"{uuid.uuid4().hex}{extension}"
    (UPLOADS_DIR / filename).write_bytes(image_data)

    teachers = load_teachers()
    teachers.append(
        Teacher(
            id=uuid.uuid4().hex,
            name=name,
            subject=subject,
            bio=bio,
            photo=f"/uploads/{filename}",
        )
    )
    save_teachers(teachers)
    return teachers


def delete_teacher(teacher_id: str) -> list[Teacher] | None:
    teachers = load_teachers()
    remaining = [teacher for teacher in teachers if teacher.id != teacher_id]
    if len(remaining) == len(teachers):
        return None
    save_teachers(remaining)
    return remaining
