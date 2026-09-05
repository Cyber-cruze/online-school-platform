"""Создание и запуск HTTP-сервера."""

from http.server import HTTPServer

from backend.config import HOST, PORT
from backend.controller.website_handler import WebsiteHandler


def create_server(host: str = HOST, port: int = PORT) -> HTTPServer:
    return HTTPServer((host, port), WebsiteHandler)


def run() -> None:
    server = create_server()
    print(f"Сайт доступен по адресу http://{HOST}:{PORT}")
    print(f"Сайт доступен по адресу http://{HOST}:{PORT}/admin")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
