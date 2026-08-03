from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Ingredient:
    name: str
    quantity: str


@dataclass
class Substitution:
    original: str
    replacement: str
    reason: str
    timestamp: str = ""


@dataclass
class Recipe:
    name: str = ""
    ingredients: list[Ingredient] = field(default_factory=list)
    steps: list[str] = field(default_factory=list)
    current_step_index: int = 0
    substitutions: list[Substitution] = field(default_factory=list)
    is_active: bool = False

    @property
    def current_step(self) -> str | None:
        if 0 <= self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None

    @property
    def total_steps(self) -> int:
        return len(self.steps)

    def advance_step(self) -> bool:
        if self.current_step_index < len(self.steps) - 1:
            self.current_step_index += 1
            return True
        return False

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "ingredients": [{"name": i.name, "quantity": i.quantity} for i in self.ingredients],
            "steps": self.steps,
            "current_step_index": self.current_step_index,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "substitutions": [
                {"original": s.original, "replacement": s.replacement, "reason": s.reason}
                for s in self.substitutions
            ],
            "is_active": self.is_active,
        }


@dataclass
class TimerData:
    id: str
    label: str
    duration_seconds: float
    remaining_seconds: float
    is_running: bool
    is_expired: bool = False
    created_at: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "duration_seconds": self.duration_seconds,
            "remaining_seconds": self.remaining_seconds,
            "is_running": self.is_running,
            "is_expired": self.is_expired,
        }


@dataclass
class SessionNote:
    content: str
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class CookingSession:
    id: str = ""
    recipe: Recipe = field(default_factory=Recipe)
    notes: list[SessionNote] = field(default_factory=list)
    started_at: str = ""
    ended_at: str = ""

    def __post_init__(self) -> None:
        if not self.id:
            self.id = uuid.uuid4().hex[:12]
        if not self.started_at:
            self.started_at = datetime.now().isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "recipe": self.recipe.to_dict(),
            "notes": [{"content": n.content, "timestamp": n.timestamp} for n in self.notes],
            "started_at": self.started_at,
            "ended_at": self.ended_at,
        }
