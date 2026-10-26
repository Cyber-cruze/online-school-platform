"""Создание FastAPI-приложения."""

import sqlite3
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, closing

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.config import DATABASE_FILE, LOGO_FILE, STATIC_DIR, UPLOADS_DIR
from backend.controller import applications, auth, pages, teachers
from backend.repository.database import initialize_database


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    initialize_database()
    yield


def create_app() -> FastAPI:
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

    application = FastAPI(
        title="Стимул",
        description="Сайт онлайн-школы и API преподавателей",
        lifespan=lifespan,
    )

    application.include_router(pages.router)
    application.include_router(auth.router)
    application.include_router(teachers.router)
    application.include_router(applications.router)

    @application.get("/healthz", include_in_schema=False)
    def health() -> dict[str, str]:
        try:
            with closing(sqlite3.connect(
                DATABASE_FILE.resolve().as_uri() + "?mode=ro", uri=True, timeout=2
            )) as connection:
                connection.execute("SELECT id FROM teachers LIMIT 1").fetchone()
        except sqlite3.Error as error:
            raise HTTPException(status_code=503, detail="Service unavailable") from error
        return {"status": "ok"}

    @application.get("/diploma.png", include_in_schema=False)
    def logo() -> FileResponse:
        if not LOGO_FILE.is_file():
            raise HTTPException(status_code=404)
        return FileResponse(LOGO_FILE)

    application.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    application.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")
    return application


app = create_app()
