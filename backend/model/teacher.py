"""Модель преподавателя."""

from dataclasses import asdict, dataclass
from typing import Any

from backend.model.base_entity import BaseEntity


@dataclass(slots=True)
class Teacher(BaseEntity):
    name: str
    subject: str
    bio: str
    photo: str
    created_at: str | None = None
    is_visible: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Teacher":
        return cls(
            id=str(data.get("id", "")),
            name=str(data.get("name", "")),
            subject=str(data.get("subject", "")),
            bio=str(data.get("bio", "")),
            photo=str(data.get("photo", "")),
            created_at=str(data["created_at"]) if data.get("created_at") else None,
            is_visible=bool(data.get("is_visible", True)),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
