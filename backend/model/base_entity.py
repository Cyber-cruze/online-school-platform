"""Базовая сущность приложения."""

from dataclasses import dataclass


@dataclass(slots=True)
class BaseEntity:
    id: str
