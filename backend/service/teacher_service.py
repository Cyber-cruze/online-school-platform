"""Бизнес-логика преподавателей и загруженных фотографий."""

import uuid
from pathlib import Path

from backend.config import ALLOWED_IMAGE_TYPES, UPLOADS_DIR
from backend.model.teacher import Teacher
from backend.repository import teacher_repository


class InvalidImageError(ValueError):
    """Загруженный файл не является поддерживаемым изображением."""


def load_teachers(*, include_hidden: bool = False) -> list[Teacher]:
    return teacher_repository.get_all(include_hidden=include_hidden)


def get_teacher(teacher_id: str) -> Teacher | None:
    return teacher_repository.get_by_id(teacher_id)


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
    image_path = UPLOADS_DIR / filename
    image_path.write_bytes(image_data)

    teacher = Teacher(
        id=uuid.uuid4().hex,
        name=name,
        subject=subject,
        bio=bio,
        photo=f"/uploads/{filename}",
    )
    try:
        teacher_repository.create(teacher)
    except Exception:
        image_path.unlink(missing_ok=True)
        raise
    return load_teachers(include_hidden=True)


def update_teacher(
    teacher_id: str,
    *,
    name: str,
    subject: str,
    bio: str,
    original_filename: str | None = None,
    content_type: str | None = None,
    image_data: bytes | None = None,
) -> list[Teacher] | None:
    current = get_teacher(teacher_id)
    if current is None:
        return None

    photo = current.photo
    new_image_path: Path | None = None
    if original_filename:
        extension = Path(original_filename).suffix.lower()
        if ALLOWED_IMAGE_TYPES.get(extension) != content_type:
            raise InvalidImageError("Поддерживаются JPG, PNG и WebP")

        UPLOADS_DIR.mkdir(exist_ok=True)
        filename = f"{uuid.uuid4().hex}{extension}"
        new_image_path = UPLOADS_DIR / filename
        new_image_path.write_bytes(image_data or b"")
        photo = f"/uploads/{filename}"

    updated_teacher = Teacher(
        id=current.id,
        name=name,
        subject=subject,
        bio=bio,
        photo=photo,
        created_at=current.created_at,
        is_visible=current.is_visible,
    )
    try:
        updated = teacher_repository.update(updated_teacher)
    except Exception:
        if new_image_path:
            new_image_path.unlink(missing_ok=True)
        raise

    if updated is None:
        if new_image_path:
            new_image_path.unlink(missing_ok=True)
        return None

    if new_image_path:
        _delete_uploaded_photo(current.photo)
    return load_teachers(include_hidden=True)


def toggle_teacher_visibility(teacher_id: str) -> list[Teacher] | None:
    teacher = get_teacher(teacher_id)
    if teacher is None:
        return None
    if not teacher_repository.set_visibility(
        teacher_id,
        is_visible=not teacher.is_visible,
    ):
        return None
    return load_teachers(include_hidden=True)


def delete_teacher(teacher_id: str) -> list[Teacher] | None:
    if not teacher_repository.delete(teacher_id):
        return None
    return load_teachers(include_hidden=True)


def _delete_uploaded_photo(photo_url: str) -> None:
    filename = Path(photo_url).name
    if not filename:
        return
    photo_path = (UPLOADS_DIR / filename).resolve()
    if photo_path.parent == UPLOADS_DIR.resolve():
        photo_path.unlink(missing_ok=True)
