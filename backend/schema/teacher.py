"""API-схемы преподавателя."""

from pydantic import BaseModel

from backend.model.teacher import Teacher


class TeacherResponse(BaseModel):
    id: str
    name: str
    subject: str
    bio: str
    photo: str
    created_at: str | None = None

    @classmethod
    def from_entity(cls, teacher: Teacher) -> "TeacherResponse":
        return cls(**teacher.to_dict())
