"""Модель преподавателя."""

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(slots=True)
class Teacher:
    id: str
    name: str
    subject: str
    bio: str
    photo: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Teacher":
        return cls(
            id=str(data.get("id", "")),
            name=str(data.get("name", "")),
            subject=str(data.get("subject", "")),
            bio=str(data.get("bio", "")),
            photo=str(data.get("photo", "")),
        )

    def to_dict(self) -> dict[str, str]:
        return asdict(self)
