from __future__ import annotations

from .models import CookingSession, Ingredient, Recipe, SessionNote, Substitution


class RecipeStateManager:
    def __init__(self) -> None:
        self.session = CookingSession()

    def set_recipe(
        self,
        name: str,
        ingredients: list[str],
        steps: list[str],
    ) -> dict:
        parsed = []
        for item in ingredients:
            parts = item.split(",", 1)
            if len(parts) == 2:
                parsed.append(Ingredient(name=parts[1].strip(), quantity=parts[0].strip()))
            else:
                parsed.append(Ingredient(name=item.strip(), quantity=""))

        self.session.recipe = Recipe(
            name=name,
            ingredients=parsed,
            steps=steps,
            current_step_index=0,
            is_active=True,
        )
        return {
            "success": True,
            "recipe_name": name,
            "ingredient_count": len(parsed),
            "step_count": len(steps),
        }

    def advance_step(self) -> dict:
        if not self.session.recipe.is_active:
            return {"success": False, "error": "No active recipe"}
        if self.session.recipe.advance_step():
            return {
                "success": True,
                "current_step_index": self.session.recipe.current_step_index,
                "current_step": self.session.recipe.current_step,
                "total_steps": self.session.recipe.total_steps,
            }
        return {"success": False, "error": "Already on the last step"}

    def go_to_step(self, step_index: int) -> dict:
        if not self.session.recipe.is_active:
            return {"success": False, "error": "No active recipe"}
        if 0 <= step_index < self.session.recipe.total_steps:
            self.session.recipe.current_step_index = step_index
            return {
                "success": True,
                "current_step_index": step_index,
                "current_step": self.session.recipe.current_step,
            }
        return {
            "success": False,
            "error": f"Step index {step_index} out of range (0-{self.session.recipe.total_steps - 1})",
        }

    def get_current_step(self) -> dict:
        if not self.session.recipe.is_active:
            return {"success": False, "error": "No active recipe"}
        step = self.session.recipe.current_step
        return {
            "success": True,
            "current_step_index": self.session.recipe.current_step_index,
            "current_step": step,
            "total_steps": self.session.recipe.total_steps,
        }

    def substitute_ingredient(self, original: str, replacement: str, reason: str = "") -> dict:
        if not self.session.recipe.is_active:
            return {"success": False, "error": "No active recipe"}

        sub = Substitution(
            original=original,
            replacement=replacement,
            reason=reason,
        )
        self.session.recipe.substitutions.append(sub)

        for ing in self.session.recipe.ingredients:
            if original.lower() in ing.name.lower():
                ing.name = replacement
                break

        return {
            "success": True,
            "original": original,
            "replacement": replacement,
            "reason": reason,
        }

    def add_note(self, note: str) -> dict:
        self.session.notes.append(SessionNote(content=note))
        return {"success": True, "note_count": len(self.session.notes)}

    def get_state(self) -> dict:
        if not self.session.recipe.is_active:
            return {"success": False, "error": "No active recipe"}
        return {
            "success": True,
            "recipe": self.session.recipe.to_dict(),
            "notes": [
                {"content": n.content, "timestamp": n.timestamp} for n in self.session.notes
            ],
        }

    def save_session(self) -> dict:
        self.session.ended_at = __import__("datetime").datetime.now().isoformat()

        note_text = self._format_session_notes()
        notes_dir = __import__("pathlib").Path("notes")
        notes_dir.mkdir(exist_ok=True)

        filename = f"handful_{self.session.id}_{self.session.recipe.name.replace(' ', '_')}.txt"
        filepath = notes_dir / filename
        filepath.write_text(note_text)

        return {
            "success": True,
            "file": str(filepath),
            "preview": note_text[:200],
        }

    def _format_session_notes(self) -> str:
        recipe = self.session.recipe
        lines = [
            "=" * 40,
            f"  Handful Cooking Session",
            f"  Recipe: {recipe.name}",
            f"  Date: {self.session.started_at}",
            "=" * 40,
            "",
            "--- Recipe ---",
            f"Name: {recipe.name}",
            "",
            "Ingredients:",
        ]
        for ing in recipe.ingredients:
            lines.append(f"  - {ing.quantity} {ing.name}")

        lines.extend(["", "Steps:"])
        for i, step in enumerate(recipe.steps):
            marker = ">>" if i == recipe.current_step_index else "  "
            lines.append(f"  {marker} {i + 1}. {step}")

        if recipe.substitutions:
            lines.extend(["", "Substitutions Made:"])
            for sub in recipe.substitutions:
                lines.append(f"  - {sub.original} -> {sub.replacement} ({sub.reason})")

        if self.session.notes:
            lines.extend(["", "Session Notes:"])
            for note in self.session.notes:
                lines.append(f"  - [{note.timestamp}] {note.content}")

        lines.extend(["", "=" * 40, f"Session ended: {self.session.ended_at}", "=" * 40])
        return "\n".join(lines)
