"""SQL-запросы для сущности преподавателя."""

import sqlite3

from backend.model.teacher import Teacher
from backend.repository.database import get_connection


def get_all(*, include_hidden: bool = False) -> list[Teacher]:
    where_clause = "" if include_hidden else "WHERE is_visible = 1"
    with get_connection() as connection:
        rows = connection.execute(
            f"""
            SELECT id, name, subject, bio, photo, created_at, is_visible
            FROM teachers
            {where_clause}
            ORDER BY rowid
            """
        ).fetchall()
    return [_to_teacher(row) for row in rows]


def get_by_id(teacher_id: str) -> Teacher | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, name, subject, bio, photo, created_at, is_visible
            FROM teachers
            WHERE id = ?
            """,
            (teacher_id,),
        ).fetchone()
    return _to_teacher(row) if row else None


def create(teacher: Teacher) -> Teacher:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO teachers (id, name, subject, bio, photo, is_visible)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                teacher.id,
                teacher.name,
                teacher.subject,
                teacher.bio,
                teacher.photo,
                int(teacher.is_visible),
            ),
        )
    created = get_by_id(teacher.id)
    if created is None:
        raise RuntimeError("Не удалось получить созданного преподавателя")
    return created


def update(teacher: Teacher) -> Teacher | None:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE teachers
            SET name = ?, subject = ?, bio = ?, photo = ?, is_visible = ?
            WHERE id = ?
            """,
            (
                teacher.name,
                teacher.subject,
                teacher.bio,
                teacher.photo,
                int(teacher.is_visible),
                teacher.id,
            ),
        )
    if cursor.rowcount == 0:
        return None
    return get_by_id(teacher.id)


def set_visibility(teacher_id: str, *, is_visible: bool) -> bool:
    with get_connection() as connection:
        cursor = connection.execute(
            "UPDATE teachers SET is_visible = ? WHERE id = ?",
            (int(is_visible), teacher_id),
        )
    return cursor.rowcount > 0


def delete(teacher_id: str) -> bool:
    with get_connection() as connection:
        cursor = connection.execute(
            "DELETE FROM teachers WHERE id = ?",
            (teacher_id,),
        )
    return cursor.rowcount > 0


def _to_teacher(row: sqlite3.Row) -> Teacher:
    return Teacher(
        id=row["id"],
        name=row["name"],
        subject=row["subject"],
        bio=row["bio"],
        photo=row["photo"],
        created_at=row["created_at"],
        is_visible=bool(row["is_visible"]),
    )
