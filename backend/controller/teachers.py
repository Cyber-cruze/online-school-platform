"""FastAPI-эндпоинты преподавателей."""

from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, Response

from backend.schema.teacher import TeacherResponse
from backend.service.auth_service import is_authenticated
from backend.service.teacher_service import (
    InvalidImageError,
    add_teacher,
    delete_teacher,
    get_teacher,
    load_teachers,
    toggle_teacher_visibility,
    update_teacher,
)
from backend.view.page_renderer import render_admin_teacher_list


router = APIRouter(prefix="/teachers", tags=["Преподаватели"])


def _require_admin(request: Request) -> Response | None:
    if is_authenticated(request.headers.get("cookie")):
        return None
    headers = (
        {"HX-Redirect": "/admin/login"}
        if request.headers.get("HX-Request") == "true"
        else {}
    )
    return Response(status_code=401, headers=headers)


@router.get("", response_model=list[TeacherResponse])
def teachers_list() -> list[TeacherResponse]:
    return [TeacherResponse.from_entity(teacher) for teacher in load_teachers()]


@router.get("/{teacher_id}", response_model=TeacherResponse)
def teacher_detail(teacher_id: str) -> TeacherResponse:
    teacher = get_teacher(teacher_id)
    if teacher is None or not teacher.is_visible:
        raise HTTPException(status_code=404, detail="Преподаватель не найден")
    return TeacherResponse.from_entity(teacher)


@router.post("", response_class=HTMLResponse, status_code=201)
async def create_teacher(
    request: Request,
    name: Annotated[str, Form(min_length=1)],
    subject: Annotated[str, Form(min_length=1)],
    bio: Annotated[str, Form(min_length=1)],
    photo: Annotated[UploadFile, File()],
) -> Response:
    authentication_error = _require_admin(request)
    if authentication_error:
        return authentication_error

    name = name.strip()
    subject = subject.strip()
    bio = bio.strip()
    if not all((name, subject, bio)):
        raise HTTPException(status_code=400, detail="Заполните все поля")

    try:
        teachers = add_teacher(
            name=name,
            subject=subject,
            bio=bio,
            original_filename=photo.filename or "",
            content_type=photo.content_type or "",
            image_data=await photo.read(),
        )
    except InvalidImageError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    finally:
        await photo.close()

    return HTMLResponse(render_admin_teacher_list(teachers), status_code=201)


@router.put("/{teacher_id}", response_class=HTMLResponse)
async def edit_teacher(
    teacher_id: str,
    request: Request,
    name: Annotated[str, Form(min_length=1)],
    subject: Annotated[str, Form(min_length=1)],
    bio: Annotated[str, Form(min_length=1)],
    photo: Annotated[UploadFile | None, File()] = None,
) -> Response:
    authentication_error = _require_admin(request)
    if authentication_error:
        return authentication_error

    name = name.strip()
    subject = subject.strip()
    bio = bio.strip()
    if not all((name, subject, bio)):
        raise HTTPException(status_code=400, detail="Заполните все поля")

    try:
        teachers = update_teacher(
            teacher_id,
            name=name,
            subject=subject,
            bio=bio,
            original_filename=photo.filename if photo else None,
            content_type=photo.content_type if photo else None,
            image_data=await photo.read() if photo else None,
        )
    except InvalidImageError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    finally:
        if photo:
            await photo.close()

    if teachers is None:
        raise HTTPException(status_code=404, detail="Преподаватель не найден")
    return HTMLResponse(render_admin_teacher_list(teachers))


@router.patch("/{teacher_id}/visibility", response_class=HTMLResponse)
def change_teacher_visibility(teacher_id: str, request: Request) -> Response:
    authentication_error = _require_admin(request)
    if authentication_error:
        return authentication_error

    teachers = toggle_teacher_visibility(teacher_id)
    if teachers is None:
        raise HTTPException(status_code=404, detail="Преподаватель не найден")
    return HTMLResponse(render_admin_teacher_list(teachers))


@router.delete("/{teacher_id}", response_class=HTMLResponse)
def remove_teacher(teacher_id: str, request: Request) -> Response:
    authentication_error = _require_admin(request)
    if authentication_error:
        return authentication_error

    teachers = delete_teacher(teacher_id)
    if teachers is None:
        raise HTTPException(status_code=404, detail="Преподаватель не найден")
    return HTMLResponse(render_admin_teacher_list(teachers))
