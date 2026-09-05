"""Разбор multipart/form-data без внешних зависимостей."""

from email.parser import BytesParser
from email.policy import default


UploadedFile = tuple[str, str, bytes]


def parse_multipart(content_type: str, body: bytes) -> tuple[dict[str, str], UploadedFile | None]:
    message = BytesParser(policy=default).parsebytes(
        f"Content-Type: {content_type}\r\n\r\n".encode() + body
    )
    fields: dict[str, str] = {}
    uploaded_file: UploadedFile | None = None

    for part in message.iter_parts():
        name = part.get_param("name", header="content-disposition")
        filename = part.get_filename()
        payload = part.get_payload(decode=True) or b""
        if filename:
            uploaded_file = (filename, part.get_content_type(), payload)
        elif name:
            fields[name] = payload.decode("utf-8").strip()

    return fields, uploaded_file
