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

    def add_step(self, instruction: str, position: int | None = None) -> dict:
        r = self.session.recipe
        if not r.is_active:
            return {"success": False, "error": "No active recipe"}
        if position is None or position < 0 or position > len(r.steps):
            r.steps.append(instruction)
            idx = len(r.steps) - 1
        else:
            r.steps.insert(position, instruction)
            idx = position
            if position <= r.current_step_index:
                r.current_step_index += 1
        return {"success": True, "step_index": idx, "total_steps": len(r.steps)}

    def update_step(self, instruction: str, step_index: int | None = None) -> dict:
        r = self.session.recipe
        if not r.is_active:
            return {"success": False, "error": "No active recipe"}
        if step_index is None:
            step_index = r.current_step_index  # "this step" => the one they're on
        if 0 <= step_index < len(r.steps):
            r.steps[step_index] = instruction
            return {"success": True, "step_index": step_index, "instruction": instruction}
        return {"success": False, "error": f"Step index {step_index} out of range"}

    def remove_step(self, step_index: int | None = None) -> dict:
        r = self.session.recipe
        if not r.is_active:
            return {"success": False, "error": "No active recipe"}
        if step_index is None:
            step_index = r.current_step_index
        if 0 <= step_index < len(r.steps):
            r.steps.pop(step_index)
            if step_index < r.current_step_index:
                r.current_step_index -= 1
            if r.current_step_index >= len(r.steps):
                r.current_step_index = max(0, len(r.steps) - 1)
            return {"success": True, "removed_index": step_index, "total_steps": len(r.steps)}
        return {"success": False, "error": f"Step index {step_index} out of range"}

    def add_ingredient(self, name: str, quantity: str = "") -> dict:
        r = self.session.recipe
        if not r.is_active:
            return {"success": False, "error": "No active recipe"}
        r.ingredients.append(Ingredient(name=name.strip(), quantity=(quantity or "").strip()))
        return {"success": True, "name": name, "quantity": quantity, "ingredient_count": len(r.ingredients)}

    def remove_ingredient(self, name: str) -> dict:
        r = self.session.recipe
        if not r.is_active:
            return {"success": False, "error": "No active recipe"}
        before = len(r.ingredients)
        r.ingredients = [i for i in r.ingredients if name.lower() not in i.name.lower()]
        removed = before - len(r.ingredients)
        return {"success": removed > 0, "name": name, "removed": removed, "ingredient_count": len(r.ingredients)}

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
