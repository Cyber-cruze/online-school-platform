import uvicorn

from backend.config import HOST, PORT


def run() -> None:
    print(f"Сайт: http://{HOST}:{PORT}")
    print(f"Админка: http://{HOST}:{PORT}/admin")
    uvicorn.run("backend.application:app", host=HOST, port=PORT)
